#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import secrets
from functools import lru_cache
from typing import Literal

from pydantic import (
    MySQLDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.paths import ENV_DIR


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "test", "production"] = "development"

    # 动态配置加载 `.env` 文件
    model_config = SettingsConfigDict(
        env_file=os.path.join(ENV_DIR, f'.env.{os.getenv("ENVIRONMENT", "development")}'),
        env_file_encoding="utf-8",
    )

    # ==============  Uvicorn ==============
    UVICORN_HOST: str = "127.0.0.1"
    UVICORN_PORT: int = 6972
    UVICORN_RELOAD: bool = True

    # ==============  FastAPI  ==============
    API_ROUTE_PREFIX: str = "/api"
    VERSION: str = "0.0.0"
    TITLE: str = "FastAPI Services"
    DESCRIPTION: str = "基于 FastAPI 搭建的后端服务"
    DOCS_URL: str | None = f"{API_ROUTE_PREFIX}/docs"
    REDOCS_URL: str | None = f"{API_ROUTE_PREFIX}/redocs"
    OPENAPI_URL: str | None = f"{API_ROUTE_PREFIX}/openapi"
    FASTAPI_STATIC_FILES: bool = False  # 是否启动静态文件

    @model_validator(mode="before")
    @classmethod
    def validator_api_url(cls, values):
        """
        生产环境下，不启动静态文件服务。
        :param values:
        :return:
        """
        if values["ENVIRONMENT"] == "production":
            values["OPENAPI_URL"] = None
            values["FASTAPI_STATIC_FILES"] = False
        return values

    # ============== 中间件 ==============
    MIDDLEWARE_ACCESS: bool = True  # 请求日志
    MIDDLEWARE_CORS: bool = True  # 跨域

    # ============== Trace ID ==============
    TRACE_ID_REQUEST_HEADER_KEY: str = "X-Request-ID"

    # ==============  CORS  ==============
    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:5173",  # 前端地址，末尾不要带 '/'
    ]
    CORS_EXPOSE_HEADERS: list[str] = [
        TRACE_ID_REQUEST_HEADER_KEY,
    ]

    # ============== 数据库 MySQL ==============
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_DATABASE: str = "fastapi-services"

    DB_ECHO: bool = False  # 连接到数据库时是否打印SQL语句
    DB_CHARSET: str = "utf8mb4"

    # ============== DateTime ==============
    DATETIME_TIMEZONE: str = "Asia/Shanghai"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MYSQL_DATABASE_URI(self) -> str:
        return str(
            MySQLDsn.build(
                scheme="mysql+asyncmy",
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                path=f"{self.DB_DATABASE}?charset={self.DB_CHARSET}",
            )
        )

    # ============== Redis ==============
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DATABASE: int = 0
    REDIS_TIMEOUT: int = 10
    REQUEST_LIMITER_REDIS_PREFIX: str = "fs:limiter"  # Request limiter

    # ==============  JWT ================
    JWT_USER_REDIS_PREFIX: str = "fs:user"
    JWT_USER_REDIS_EXPIRE_SECONDS: int = 604800  # 过期时间 7 天，单位：秒

    # ==============  Token  ==============
    TOKEN_SECRET_KEY: str = secrets.token_urlsafe(32)  # 密钥
    TOKEN_ALGORITHM: str = "HS256"  # 算法
    TOKEN_EXPIRE_SECONDS: int = 604800  # 过期时间 7 天，单位：秒
    TOKEN_REFRESH_EXPIRE_SECONDS: int = 691200  # refresh token 过期时间 8 天，单位：秒
    TOKEN_REDIS_PREFIX: str = "fs:token"
    TOKEN_REFRESH_REDIS_PREFIX: str = "fs:refresh_token"
    TOKEN_EXTRA_INFO_REDIS_PREFIX: str = "fs:token_extra_info"  # token 存储在 Redis 额外信息
    TOKEN_ONLINE_REDIS_PREFIX: str = "fs:token_online"  # token 在线状态 存储在 Redis
    TOKEN_REQUEST_PATH_EXCLUDE: list[str] = [  # JWT / RBAC 白名单
        f"{API_ROUTE_PREFIX}/auth/login",
    ]

    # # ==============  Cookies  ==================
    COOKIE_REFRESH_TOKEN_KEY: str = "fs_refresh_token"
    COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS: int = TOKEN_REFRESH_EXPIRE_SECONDS

    # ==============  Sentry  ==================
    CAPTCHA_EXPIRE_TIME: int = 300  # 验证码, 短信类数据过期时间 5 分钟，单位：秒

    # ==============  Ip location  ==============
    IP_LOCATION_PARSE: Literal["online", "offline", "false"] = "offline"
    IP_LOCATION_REDIS_PREFIX: str = "fs:ip:location"
    IP_LOCATION_EXPIRE_SECONDS: int = 86400  # 过期时间 1 天，单位：秒

    # ============== 日志 Log ==============
    LOG_ROOT_LEVEL: str = "NOTSET"
    LOG_STD_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | "
        "<cyan> {correlation_id} </> | <lvl>{message}</>"
    )
    LOG_FILE_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | "
        "<cyan> {correlation_id} </> | <lvl>{message}</>"
    )
    LOG_CID_DEFAULT_VALUE: str = "-"
    LOG_CID_UUID_LENGTH: int = 32  # must <= 32
    LOG_STDOUT_LEVEL: str = "INFO"
    LOG_STDERR_LEVEL: str = "ERROR"
    LOG_STDOUT_FILENAME: str = "fs_access.log"
    LOG_STDERR_FILENAME: str = "fs_error.log"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
