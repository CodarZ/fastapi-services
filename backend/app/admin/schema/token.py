#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

from backend.app.admin.schema.user import UserInfoDetail
from backend.common.enums import StatusEnum
from backend.common.schema import SchemaBase


class SwaggerToken(SchemaBase):
    access_token: str
    token_type: str = 'Bearer'
    user: UserInfoDetail


class AccessTokenBase(SchemaBase):
    access_token: str
    expire_time: datetime
    session_uuid: str


class LoginUserInfo(AccessTokenBase):
    user: UserInfoDetail


class LoginTokenDetail(SchemaBase):
    id: int
    session_uuid: str
    username: str
    nickname: str
    phone: str
    ip: str
    os: str
    browser: str
    device: str
    status: StatusEnum
    last_login_time: str
    expire_time: datetime
