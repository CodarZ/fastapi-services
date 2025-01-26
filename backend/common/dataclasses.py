#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dataclasses
from datetime import datetime

from fastapi import Response

from backend.common.enums import StatusEnum


@dataclasses.dataclass
class IpInfo:
    ip: str                                     # 原始 IP 地址
    country: str | None = None                  # 国家
    region: str | None = None                   # 省/州
    city: str | None = None                     # 城市
    district: str | None = None                 # 区
    postal_code: str | None = None              # 邮政编码
    timezone: str | None = None                 # 时区
    latitude: float | None = None               # 纬度
    longitude: float | None = None              # 经度
    location_code: str | None = None            # 位置编码，例如北京为 110000
    full_address: str | None = None             # 完整地址（例如：北京市朝阳区三里屯）


@dataclasses.dataclass
class UserAgentInfo:
    user_agent: str                              # 原始的 User-Agent 字符串
    os: str | None = None                        # 操作系统（如 Windows, macOS, iOS, Android）
    os_version: str | None = None                # 操作系统版本（如 10.0.1, Big Sur, etc.）
    browser: str | None = None                   # 浏览器类型（如 Chrome, Safari, Firefox）
    browser_version: str | None = None           # 浏览器版本（如 91.0.4472.124）
    device: str | None = None                    # 设备类型（如 Mobile, Tablet, Desktop）
    device_model: str | None = None              # 具体的设备型号（如 iPhone 12, Galaxy S21）


@dataclasses.dataclass
class RequestCallNext:
    code: str
    msg: str
    status: StatusEnum
    err: Exception | None
    response: Response


@dataclasses.dataclass
class NewToken:
    new_access_token: str
    new_access_token_expire_time: datetime
    new_refresh_token: str
    new_refresh_token_expire_time: datetime
    session_uuid: str


@dataclasses.dataclass
class AccessToken:
    access_token: str
    access_token_expire_time: datetime
    session_uuid: str


@dataclasses.dataclass
class RefreshToken:
    refresh_token: str
    refresh_token_expire_time: datetime


@dataclasses.dataclass
class TokenPayload:
    id: int
    session_uuid: str
    expire_time: datetime
