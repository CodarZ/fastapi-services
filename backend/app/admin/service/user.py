#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from backend.app.admin.crud.user import user_crud
from backend.app.admin.model import User
from backend.app.admin.schema.user import RegisterUser, UpdateUser
from backend.common.exception import errors
from backend.core.config import settings
from backend.database.mysql import async_db_session
from backend.database.redis import redis_client


class UserService:
    @staticmethod
    async def register(*, obj: RegisterUser):
        async with async_db_session.begin() as db:
            phone = await user_crud.get_by_phone(db, obj.phone)
            if phone:
                raise errors.RequestError(msg="用户已经注册")
            await user_crud.create(db, obj)

    @staticmethod
    async def delete(*, id: int) -> int:
        async with async_db_session.begin() as db:
            if id == 1:
                raise errors.ForbiddenError(msg="超级管理员不允许删除")
            user = await user_crud.get(db, id)
            if not user:
                raise errors.NotFoundError(msg="用户不存在")
            count = await user_crud.delete(db, user.id)
            key_prefix = [
                f"{settings.TOKEN_REDIS_PREFIX}:{user.id}",
                f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user.id}",
            ]
            for key in key_prefix:
                await redis_client.delete_prefix(key)
            return count

    @staticmethod
    async def update(*, id: int, obj: UpdateUser) -> int:
        async with async_db_session.begin() as db:
            if id == 1:
                raise errors.ForbiddenError(msg="超级管理员不允许修改")

            user = await user_crud.get(db, id)

            if not user:
                raise errors.NotFoundError(msg="用户不存在")
            # 校验 token 是否有修改信息的权限
            # verify

            count = await user_crud.update_user_info(db, id, obj)
            return count

    @staticmethod
    async def get(*, id: int) -> User:
        async with async_db_session() as db:
            user = await user_crud.get(db, id)
            if not user:
                raise errors.NotFoundError(msg="用户不存在")
            return user


user_service: UserService = UserService()
