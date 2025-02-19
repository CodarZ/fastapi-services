#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import HttpUrl
from sqlalchemy import Boolean, DateTime, INTEGER, String, VARBINARY
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key
from backend.database.mysql import uuid4_str
from backend.utils.timezone import timezone


class User(Base):
    """
    用户表
    当用户注册时，使用 `phone` 手机号注册，默认没有密码，同时将 `username` 值 填写为注册的手机号
    与此同时 `username` 只允许一年修改一次。
        - `id` 主键
        - `phone`, `username` 需要是唯一值，作为用户的标识。
        - `username` 默认是`phone`，有修改限制（一年一次等）。
        - `password` 密码，可有可无。
    """

    __tablename__ = "sys_user"  # type: ignore

    id: Mapped[id_key] = mapped_column(init=False)
    uuid: Mapped[str] = mapped_column(
        String(50), unique=True, init=False, default_factory=uuid4_str
    )
    phone: Mapped[str] = mapped_column(
        String(11), unique=True, index=True, nullable=False, comment="手机号"
    )
    username: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, comment="用户名"
    )
    password: Mapped[str | None] = mapped_column(
        String(255), default=None, comment="密码"
    )
    nickname: Mapped[str | None] = mapped_column(
        String(20), default=None, comment="昵称"
    )
    email: Mapped[str | None] = mapped_column(String(100), default=None, comment="邮箱")
    avatar: Mapped[HttpUrl | None] = mapped_column(
        String(255), default=None, comment="头像"
    )
    gender: Mapped[int | None] = mapped_column(
        INTEGER, default=None, comment="性别(0未知 1男 2女)"
    )
    birth_date: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, comment="出生日期"
    )
    status: Mapped[int] = mapped_column(default=1, comment="用户账号状态(0停用 1正常)")
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="超级权限(0否 1是)"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否实名认证"
    )
    salt: Mapped[bytes | None] = mapped_column(
        VARBINARY(255), default=None, comment="加密盐"
    )
    join_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        init=False,
        default_factory=timezone.now,
        comment="注册时间",
    )
    last_login_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        init=False,
        onupdate=timezone.now,
        comment="上次登录时间",
    )
    updated_username_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        init=False,
        default_factory=timezone.now,
        onupdate=timezone.now,
        comment="上次更新用户名的时间",
    )
