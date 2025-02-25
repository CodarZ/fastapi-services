#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

from backend.app.admin.schema.user import UserInfoDetail
from backend.common.enums import StatusEnum
from backend.common.schema import SchemaBase


class SwaggerToken(SchemaBase):
    """便于swagger 直接使用的 token"""

    access_token: str
    # token_type: str = "Bearer"
    user: UserInfoDetail


class AccessTokenBase(SchemaBase):
    access_token: str
    expire_time: datetime
    session_uuid: str


class NewToken(AccessTokenBase):
    """新 token"""

    pass


class KickOutToken(SchemaBase):
    """踢出用户"""

    session_uuid: str


class LoginUserInfo(AccessTokenBase):
    """附带登录用户信息"""

    user: UserInfoDetail


class LoginTokenDetail(SchemaBase):
    """token 信息"""

    id: int
    session_uuid: str
    username: str
    nickname: str
    ip: str
    os: str
    browser: str
    device: str
    status: StatusEnum
    last_login_time: str
    expire_time: datetime
