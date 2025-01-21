#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局业务异常类

业务代码执行异常时，可以使用 raise xxxError 触发内部错误，它尽可能实现带有后台任务的异常，但它不适用于**自定义响应状态码**
如果要求使用**自定义响应状态码**，则可以通过 return response_base.fail(res=CustomResponseCode.xxx) 直接返回
"""  # noqa: E501

from typing import Any

from fastapi import HTTPException
# Starlette 提供的后台任务类
from starlette.background import BackgroundTask

from backend.common.response.code import CustomErrorCode, StandardResponseCode


# 导入自定义的错误码类，用于定义异常的响应状态码和消息


# ========== 基础异常类 ==========
class BaseExceptionMixin(Exception):
    """
    自定义异常基类，提供统一的结构：
    - code: 错误码（子类定义具体值）
    - msg: 错误信息（可选）
    - data: 附加数据（可选）
    - background: 后台任务（可选，用于在异常触发时执行异步任务）
    """

    code: int

    def __init__(
        self,
        *,
        msg: str = None,
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        self.msg = msg  # 错误消息
        self.data = data  # 附加数据
        self.background = background  # 异步后台任务


# ========== HTTP 异常类 ==========
class HTTPError(HTTPException):
    """
    自定义 HTTP 异常：
    - 继承 FastAPI 提供的 HTTPException。
    - 支持设置自定义状态码、消息和响应头。
    """

    def __init__(
        self, *, code: int, msg: Any = None, headers: dict[str, Any] | None = None
    ):
        super().__init__(status_code=code, detail=msg, headers=headers)


# ========== 业务异常类 ==========
class CustomError(BaseExceptionMixin):
    """
    自定义业务异常：
    - error: 错误码对象（CustomErrorCode 类型，包含 code 和 msg）。
    - data: 附加数据（可选）。
    - background: 后台任务（可选）。
    """

    def __init__(
        self,
        *,
        error: CustomErrorCode,
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        self.code = error.code  # 错误码
        super().__init__(msg=error.msg, data=data, background=background)


# ========== 常见 HTTP 异常 ==========
class RequestError(BaseExceptionMixin):
    """
    请求错误异常：
    - 默认 HTTP 状态码为 400（Bad Request）。
    """

    code = StandardResponseCode.HTTP_400

    def __init__(
        self,
        *,
        msg: str = "Bad Request",
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


class ForbiddenError(BaseExceptionMixin):
    """
    禁止访问异常：
    - 默认 HTTP 状态码为 403（Forbidden）。
    """

    code = StandardResponseCode.HTTP_403

    def __init__(
        self,
        *,
        msg: str = "Forbidden",
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


class NotFoundError(BaseExceptionMixin):
    """
    资源未找到异常：
    - 默认 HTTP 状态码为 404（Not Found）。
    """

    code = StandardResponseCode.HTTP_404

    def __init__(
        self,
        *,
        msg: str = "Not Found",
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


class ServerError(BaseExceptionMixin):
    """
    服务器内部错误异常：
    - 默认 HTTP 状态码为 500（Internal Server Error）。
    """

    code = StandardResponseCode.HTTP_500

    def __init__(
        self,
        *,
        msg: str = "Internal Server Error",
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


class GatewayError(BaseExceptionMixin):
    """
    网关错误异常：
    - 默认 HTTP 状态码为 502（Bad Gateway）。
    """

    code = StandardResponseCode.HTTP_502

    def __init__(
        self,
        *,
        msg: str = "Bad Gateway",
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


class AuthorizationError(BaseExceptionMixin):
    """
    授权失败异常：
    - 默认 HTTP 状态码为 401（Permission Denied）。
    """

    code = StandardResponseCode.HTTP_401

    def __init__(
        self,
        *,
        msg: str = "Permission Denied",
        data: Any = None,
        background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


# ========== 特殊 HTTP 异常 ==========
class TokenError(HTTPError):
    """
    认证失败异常：
    - 默认 HTTP 状态码为 401（Not Authenticated）。
    - 继承自 HTTPError，支持自定义响应头。
    """

    code = StandardResponseCode.HTTP_401

    def __init__(
        self, *, msg: str = "Not Authenticated", headers: dict[str, Any] | None = None
    ):
        super().__init__(
            code=self.code, msg=msg, headers=headers or {"WWW-Authenticate": "Bearer"}
        )
