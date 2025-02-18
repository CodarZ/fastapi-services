#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model import User
from backend.app.admin.schema.user import RegisterUser, UpdateUser
from backend.utils.timezone import timezone


class CRUDUser(CRUDPlus[User]):
    async def create(self, db: AsyncSession, obj: RegisterUser):
        """创建用户"""

        dict_user = obj.model_dump()
        dict_user["username"] = dict_user["phone"]
        new_user = self.model(**dict_user)
        db.add(new_user)

    async def delete(self, db: AsyncSession, user_id: int) -> int:
        """删除用户"""
        return await self.delete_model(db, user_id)

    async def get_list(self):
        """获取用户列表"""
        stmt = select(self.model).order_by(desc(self.model.join_time))
        # 做筛选
        return stmt

    async def get(self, db: AsyncSession, user_id: int) -> User | None:
        """通过 id 获取用户"""
        return await self.select_model(db, user_id)

    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        """通过 phone 获取用户"""
        return await self.select_model_by_column(db, phone=phone)

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        """通过 username 获取用户"""
        return await self.select_model_by_column(db, username=username)

    async def update_user_info(self, db: AsyncSession, user_id: int, obj: UpdateUser):
        """更新用户信息"""
        return await self.update_model(db, user_id, obj)

    async def update_login_time(self, db: AsyncSession, phone: str) -> int:
        """
        更新用户登录时间

        :param db:
        :param phone:
        :return:
        """
        return await self.update_model_by_column(
            db, {"last_login_time": timezone.now()}, phone=phone
        )


user_crud: CRUDUser = CRUDUser(User)
