#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import ConfigDict, EmailStr, Field, HttpUrl, field_validator

from backend.common.enums import StatusEnum
from backend.common.schema import SchemaBase
from backend.utils.regexp_verify import is_phone


class _VerifyPhone(SchemaBase):
    """校验手机号（该文件内部使用）"""

    phone: str = Field(description="手机号", min_length=11, max_length=11, default="")

    @field_validator("phone", mode="after")
    @classmethod
    def validate_phone(cls, value):
        if not is_phone(value):
            raise ValueError("手机号格式不正确")
        return value


class AuthPhoneByPassword(_VerifyPhone):
    """手机号 x 密码"""

    password: str = Field(description="密码", default="123456", max_length=24)


class UserInfoSchemaBase(SchemaBase):
    """只允许获取可以修改的基础数据"""

    model_config = ConfigDict(from_attributes=True)

    nickname: str | None = Field(description="昵称")
    email: EmailStr | None = Field(description="邮箱", examples=["test@example.com"])
    avatar: HttpUrl | None = Field(description="头像")
    gender: int | None = Field(description="性别(0未知 1男 2女)", ge=0, le=2)
    birth_date: datetime | None = Field(default=None, description="出生日期")


class UserInfoDetail(UserInfoSchemaBase, _VerifyPhone):
    """所有可以展示的数据"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    # uuid: str
    username: str | None = Field(description="用户名 默认为手机号")
    status: StatusEnum = Field(
        default=StatusEnum.YES, description="用户账号状态(0停用 1正常)"
    )
    is_admin: bool = Field(default=False, description="超级权限(0否 1是)")
    is_verified: bool = Field(default=False, description="是否实名认证")
    join_time: datetime | None = Field(default=None, description="注册时间")
    last_login_time: datetime | None = Field(default=None, description="上次登录时间")
    updated_username_time: datetime | None = Field(
        default=None, description="上次更新用户名的时间"
    )


class RegisterUserByCode(_VerifyPhone):
    """手机号 x 手机验证码"""

    code: str = Field(description="验证码")


class RegisterUser(AuthPhoneByPassword):
    pass


class UpdateUser(UserInfoSchemaBase):
    pass
