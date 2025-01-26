#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any

from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from starlette.requests import HTTPConnection

from backend.app.admin.schema.user import UserInfoDetail
from backend.common.exception.errors import TokenError
from backend.common.logger import log
from backend.common.security.jwt import jwt_authentication
from backend.core.config import settings
from backend.utils.serializers import MsgSpecJSONResponse


class _AuthenticationError(AuthenticationError):
    """重写内部认证错误类"""

    def __init__(self, *, code: int = None, msg: str = None, headers: dict[str, Any] | None = None):
        self.code = code
        self.msg = msg
        self.headers = headers


class JwtAuthMiddleware(AuthenticationBackend):
    """JWT 认证中间件"""

    @staticmethod
    def auth_exception_handler(_: HTTPConnection, exc: _AuthenticationError) -> Response:
        """覆盖内部认证错误处理"""
        return MsgSpecJSONResponse(content={"code": exc.code, "msg": exc.msg, "data": None}, status_code=exc.code)

    async def authenticate(self, request: Request) -> tuple[AuthCredentials, UserInfoDetail] | None:
        """认证逻辑入口"""
        # 1. 从请求头获取 Authorization 字段
        token = request.headers.get("Authorization")
        if not token:
            return  # 无 Token，跳过认证（可能是匿名访问）

        # 2. 检查请求路径是否在排除列表中（如登录接口）
        if request.url.path in settings.TOKEN_REQUEST_PATH_EXCLUDE:
            return  # 排除路径无需认证

        # 3. 解析 Bearer Token
        scheme, token = get_authorization_scheme_param(token)
        if scheme.lower() != "bearer":
            return  # 非 Bearer 方案，拒绝认证

        try:
            # 4. JWT 认证核心逻辑
            user = await jwt_authentication(token)
        except TokenError as exc:
            # 捕获已知 Token 错误（如过期、无效）
            raise _AuthenticationError(code=exc.code, msg=exc.detail, headers=exc.headers)
        except Exception as e:
            # 捕获未知异常并记录日志
            log.error(f"JWT 授权异常：{e}")
            raise _AuthenticationError(code=getattr(e, "code", 500), msg=getattr(e, "msg", "Internal Server Error"))

        # 5. 认证成功，返回用户信息和权限标识
        # 请注意，此返回使用非标准模式，所以在认证通过时，将丢失某些标准特性
        # 标准返回模式请查看：https://www.starlette.io/authentication/
        return AuthCredentials(["authenticated"]), user
