#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import BackgroundTasks, Request, Response
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.user import user_crud
from backend.app.admin.model import User
from backend.app.admin.schema.token import AccessTokenBase, LoginUserInfo
from backend.app.admin.schema.user import AuthPhoneByPassword
from backend.common.exception import errors
from backend.common.logger import log
from backend.common.security.jwt import (
    create_access_token,
    create_refresh_token,
    create_new_token,
    jwt_decode,
    get_token,
    password_verify,
)
from backend.core.config import settings
from backend.database.mysql import async_db_session
from backend.database.redis import redis_client
from backend.utils.timezone import timezone


class AuthService:
    @staticmethod
    async def user_verify(db: AsyncSession, phone: str, password: str) -> User:
        user = await user_crud.get_by_phone(db, phone)
        if not user:
            raise errors.NotFoundError(msg="用户名或密码有误")
        elif not password_verify(password, user.password):
            raise errors.AuthorizationError(msg="用户名或密码有误")
        elif not user.status:
            raise errors.AuthorizationError(msg="用户已被锁定, 请联系统管理员")
        return user

    async def login(
        self,
        *,
        request: Request,
        response: Response,
        obj: AuthPhoneByPassword,
        background_tasks: BackgroundTasks,
    ) -> LoginUserInfo:
        async with async_db_session.begin() as db:
            user = None
            try:
                user = await self.user_verify(db, obj.phone, obj.password)
                # 验证码登录

                await user_crud.update_login_time(db, obj.phone)
                await db.refresh(user)

                access_token = await create_access_token(
                    user_id=str(user.id),
                    multi_login=False,
                    # extra info
                    username=user.username,
                    nickname=user.nickname,
                    last_login_time=timezone.t_str(user.last_login_time),
                    ip=request.state.ip,
                    os=request.state.os,
                    browser=request.state.browser,
                    device=request.state.device,
                )

                refresh_token = await create_refresh_token(str(user.id), False)

                response.set_cookie(
                    key=settings.COOKIE_REFRESH_TOKEN_KEY,
                    value=refresh_token.refresh_token,
                    max_age=settings.COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS,
                    expires=timezone.f_utc(refresh_token.refresh_token_expire_time),
                    httponly=True,
                )
            except errors.NotFoundError as e:
                log.error("登陆错误: 账户不存在")
                raise errors.NotFoundError(msg=e.msg)
            except (errors.AuthorizationError, errors.CustomError) as e:
                log.error("------------------")
                if not user:
                    log.error("登录错误：账户或密码错误")
                raise errors.AuthorizationError(msg=e.msg)
            except Exception as e:
                log.error(f"登陆错误: {e}")
                raise e
            else:
                data = LoginUserInfo(
                    access_token=access_token.access_token,
                    expire_time=access_token.access_token_expire_time,
                    session_uuid=access_token.session_uuid,
                    user=user,  # type: ignore
                )
                return data

    async def swagger_login(self, *, obj: AuthPhoneByPassword) -> tuple[str, User]:
        async with async_db_session.begin() as db:
            user = await self.user_verify(db, obj.phone, obj.password)
            await user_crud.update_login_time(db, obj.phone)
            a_token = await create_access_token(
                str(user.id),
                False,
                # extra info
                login_type="swagger",
            )
            return a_token.access_token, user

    @staticmethod
    async def new_token(*, request: Request):
        refresh_token = request.headers.get(settings.COOKIE_REFRESH_TOKEN_KEY)

        if not refresh_token:
            raise errors.TokenError(msg="Refresh Token 过期，请重新登录")
        try:
            user_id = jwt_decode(refresh_token).id
        except Exception:
            raise errors.TokenError(msg="Refresh Token 失效")

        async with async_db_session.begin() as db:
            user = await user_crud.get(db, user_id)
            if not user:
                raise errors.NotFoundError(msg="用户名或密码错误")
            elif user.status:
                raise errors.AuthorizationError(msg="用户已被锁定，请联系管理员")
            new_token = await create_new_token(
                user_id=str(user.id),
                refresh_token=refresh_token,
                multi_login=False,
                # extra info
                username=user.username,
                nickname=user.nickname,
                last_login_time=timezone.t_str(user.last_login_time),
                ip=request.state.ip,
                os=request.state.os,
                browser=request.state.browser,
                device_type=request.state.device,
            )

            data = AccessTokenBase(
                access_token=new_token.new_access_token,
                expire_time=new_token.new_access_token_expire_time,
                session_uuid=new_token.session_uuid,
            )
            return data

    @staticmethod
    async def logout(*, request: Request, response: Response) -> None:
        token = get_token(request)
        user_id = jwt_decode(token).id
        refresh_token = request.cookies.get(settings.COOKIE_REFRESH_TOKEN_KEY)
        response.delete_cookie(settings.COOKIE_REFRESH_TOKEN_KEY)

        if refresh_token:
            await redis_client.delete(
                f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{refresh_token}"
            )
        key_prefix = [
            f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:",
            f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:",
        ]
        for prefix in key_prefix:
            await redis_client.delete_prefix(prefix)


auth_service: AuthService = AuthService()
