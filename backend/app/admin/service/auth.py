#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from fastapi import Request, Response
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask, BackgroundTasks

from backend.app.admin.api import auth
from backend.app.admin.crud.user import user_crud
from backend.app.admin.model import User
from backend.app.admin.schema.token import LoginTokenDetail, LoginUserInfo, NewToken
from backend.app.admin.schema.user import AuthPhoneByPassword
from backend.common.enums import StatusEnum
from backend.common.exception import errors
from backend.common.logger import log
from backend.common.response.code import CustomErrorCode
from backend.common.security.jwt import (
    create_access_token,
    create_new_token,
    create_refresh_token,
    get_token,
    jwt_decode,
    password_verify,
)
from backend.core.config import settings
from backend.database.mysql import async_db_session, uuid4_str
from backend.database.redis import redis_client
from backend.utils.timezone import timezone


class AuthService:
    @staticmethod
    async def user_verify(
        db: AsyncSession,
        *,
        phone: str | None = None,
        username: str | None = None,
        password: str,
    ) -> User:
        if phone:
            user = await user_crud.get_by_phone(db, phone)
        elif username:
            user = await user_crud.get_by_username(db, username)
        else:
            raise errors.RequestError(msg="请填写用户名或手机号")

        if not user:
            raise errors.NotFoundError(msg="用户不存在")
        elif not user.status:
            raise errors.ForbiddenError(msg="用户已被禁用")
        elif user.password and not password_verify(password, user.password):
            raise errors.ForbiddenError(msg="密码错误")
        # TODO 没有密码的用户验证, 引导设置密码等操作
        return user

    async def swagger_login(self, *, obj: HTTPBasicCredentials):
        async with async_db_session.begin() as db:
            user = await self.user_verify(
                db, username=obj.username, password=obj.password
            )

            await user_crud.update_login_time(db, user.phone)

            a_token = await create_access_token(
                user_id=str(user.id),
                multi_login=user.is_multi_login,
                # extra info
                login_type="Swagger 登录",
            )

            return a_token.access_token, user

    async def user_login(
        self, *, obj: AuthPhoneByPassword, request: Request, response: Response
    ):
        async with async_db_session.begin() as db:
            user = None
            try:
                user = await self.user_verify(
                    db=db, phone=obj.phone, password=obj.password
                )

                await user_crud.update_login_time(db, user.phone)

                await db.refresh(user)
                a_token = await create_access_token(
                    user_id=str(user.id),
                    multi_login=user.is_multi_login,
                    # extra info
                    username=user.username,
                    nickname=user.nickname,
                    last_login_time=(
                        timezone.t_str(user.last_login_time)
                        if user.last_login_time
                        else timezone.now()
                    ),
                    ip=request.state.ip,
                    os=request.state.os,
                    browser=request.state.browser,
                    device=request.state.device,
                )

                r_token = await create_refresh_token(
                    user_id=str(user.id), multi_login=user.is_multi_login
                )

                response.set_cookie(
                    key=settings.COOKIE_REFRESH_TOKEN_KEY,
                    value=r_token.refresh_token,
                    max_age=settings.COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS,
                    expires=timezone.f_utc(r_token.refresh_token_expire_time),
                    httponly=True,
                )
            except errors.NotFoundError as e:
                log.error("用户不存在")
                raise errors.NotFoundError(msg=e.msg if e.msg else "用户不存在")
            except (errors.AuthorizationError, errors.CustomError) as e:
                if not user:
                    log.error("用户名或密码错误")
                    raise errors.AuthorizationError(
                        msg=e.msg if e.msg else "用户名或密码错误"
                    )
            except Exception as e:
                log.error(f"登录失败: {e}")
                raise e
            else:
                # TODO user 应该为 UserInfoDetail
                return LoginUserInfo(
                    access_token=a_token.access_token,
                    expire_time=a_token.access_token_expire_time,
                    session_uuid=a_token.session_uuid,
                    user=user,  # type: ignore
                )

    @staticmethod
    async def refresh_new_token(*, request: Request, response: Response):
        token = get_token(request)
        refresh_token = request.cookies.get(settings.COOKIE_REFRESH_TOKEN_KEY)
        if not refresh_token:
            raise errors.TokenError(msg="Refresh Token 已过期，请重新登录")
        try:
            user_id = jwt_decode(refresh_token).id
        except Exception:
            raise errors.TokenError(msg="Refresh Token 无效")
        async with async_db_session.begin() as db:
            user = await user_crud.get(db, user_id)
            if not user:
                raise errors.NotFoundError(msg="用户不存在")
            if not user.status:
                raise errors.ForbiddenError(msg="用户已被禁用")

            n_token = await create_new_token(
                user_id=str(user.id),
                multi_login=user.is_multi_login,
                refresh_token=refresh_token,
                token=token,
                # extra info
                username=user.username,
                nickname=user.nickname,
                last_login_time=(
                    timezone.t_str(user.last_login_time)
                    if user.last_login_time
                    else timezone.now()
                ),
                ip=request.state.ip,
                os=request.state.os,
                browser=request.state.browser,
                device_type=request.state.device,
            )

            # 更新 refresh token
            response.set_cookie(
                key=settings.COOKIE_REFRESH_TOKEN_KEY,
                value=n_token.new_refresh_token,
                max_age=settings.COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS,
                expires=timezone.f_utc(n_token.new_refresh_token_expire_time),
                httponly=True,
            )

            return NewToken(
                access_token=n_token.new_access_token,
                expire_time=n_token.new_access_token_expire_time,
                session_uuid=n_token.session_uuid,
            )

    async def logout(self, *, request: Request, response: Response):
        token = get_token(request)
        payload = jwt_decode(token)
        user_id = payload.id
        refresh_token = request.cookies.get(settings.COOKIE_REFRESH_TOKEN_KEY)

        response.delete_cookie(settings.COOKIE_REFRESH_TOKEN_KEY)

        if request.user.is_multi_login:
            await redis_client.delete(
                f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{payload.session_uuid}"
            )
            if refresh_token:
                await redis_client.delete(
                    f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{refresh_token}"
                )
        else:
            key_prefix = [
                f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:",
                f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:",
            ]
            for prefix in key_prefix:
                await redis_client.delete_prefix(prefix)


auth_service: AuthService = AuthService()
