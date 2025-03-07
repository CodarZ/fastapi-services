#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pydantic.errors import PydanticUserError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from uvicorn.protocols.http.h11_impl import STATUS_PHRASES

from backend.common.exception.errors import BaseExceptionMixin
from backend.common.exception.message import (
    USAGE_ERROR_MESSAGES,
    VALIDATION_ERROR_MESSAGES,
)
from backend.common.request.trace_id import get_request_trace_id
from backend.common.response.base import response_base
from backend.common.response.code import CustomResponseCode, StandardResponseCode
from backend.core.config import settings
from backend.utils.serializers import MsgSpecJSONResponse

# 定义模块对外暴露的类和变量，供其他模块引用
__all__ = ["register_exception"]


def _get_exception_code(status_code: int):
    """
    获取返回状态码, OpenAPI, Uvicorn... 可用状态码基于 RFC 定义, 详细代码见下方链接

    `python 状态码标准支持 <https://github.com/python/cpython/blob/6e3cc72afeaee2532b4327776501eb8234ac787b/Lib/http
    /__init__.py#L7>`__

    `IANA 状态码注册表 <https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml>`__

    :param status_code:
    :return:
    """
    # noinspection PyBroadException
    try:
        STATUS_PHRASES[status_code]
    except Exception:
        code = StandardResponseCode.HTTP_400
    else:
        code = status_code
    return code


async def _validation_exception_handler(
    request: Request, e: RequestValidationError | ValidationError
):
    """
    数据验证异常处理，返回统一的响应结构。

    :param request: FastAPI 请求对象
    :param e: 捕获的验证异常
    :return: 标准化 JSON 响应
    """
    errors = []
    for error in e.errors():
        # 提取错误类型，并根据配置文件获取定制的错误信息
        custom_message = VALIDATION_ERROR_MESSAGES.get(error["type"])
        if custom_message:
            ctx = error.get("ctx")
            if not ctx:
                error["msg"] = custom_message
            else:
                error["msg"] = custom_message.format(**ctx)
                ctx_error = ctx.get("error")
                if ctx_error:
                    error["ctx"]["error"] = (  # type: ignore
                        ctx_error.__str__().replace("'", '"')
                        if isinstance(ctx_error, Exception)
                        else None
                    )
        errors.append(error)
    error = errors[0]  # 只返回第一个错误信息

    if error.get("type") == "json_invalid":
        message = "json解析失败"
    else:
        # 拼接错误详细信息
        error_input = error.get("input")
        field = str(error.get("loc")[-1])
        error_msg = error.get("ctx", {}).get("error", error.get("msg"))
        message = (
            f"{field} {error_msg}，输入：{error_input}"
            if settings.ENVIRONMENT == "development"
            else error_msg
        )
    msg = f"{CustomResponseCode.HTTP_422.msg}: {message}"
    data = {"errors": errors} if settings.ENVIRONMENT == "development" else None
    content = {
        "code": StandardResponseCode.HTTP_422,
        "msg": msg,
        "data": data,
    }
    request.state.__request_validation_exception__ = (
        content  # 用于在中间件中获取异常信息
    )
    if settings.ENVIRONMENT == "development":
        content.update(trace_id=get_request_trace_id(request))  # 添加请求唯一标识
    return MsgSpecJSONResponse(status_code=422, content=content)


def register_exception(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """全局HTTP异常处理"""
        if settings.ENVIRONMENT == "development":
            content = {
                "code": exc.status_code,
                "msg": exc.detail,
                "data": None,
            }
        else:
            res = response_base.fail(res=CustomResponseCode.HTTP_400)
            content = res.model_dump()
        request.state.__request_http_exception__ = content
        if settings.ENVIRONMENT == "development":
            content.update(trace_id=get_request_trace_id(request))
        return MsgSpecJSONResponse(
            status_code=_get_exception_code(exc.status_code),
            content=content,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def fastapi_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Fastapi 数据验证异常处理"""
        return await _validation_exception_handler(request, exc)

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        """pydantic 数据验证异常处理"""
        return await _validation_exception_handler(request, exc)

    @app.exception_handler(PydanticUserError)
    async def pydantic_user_error_handler(request: Request, exc: PydanticUserError):
        """Pydantic 用户异常处理"""
        content = {
            "code": StandardResponseCode.HTTP_500,
            "msg": (USAGE_ERROR_MESSAGES.get(exc.code) if exc.code else "用户处理异常"),
            "data": None,
        }
        request.state.__request_pydantic_user_error__ = content
        if settings.ENVIRONMENT == "development":
            content.update(trace_id=get_request_trace_id(request))
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_500,
            content=content,
        )

    @app.exception_handler(AssertionError)
    async def assertion_error_handler(request: Request, exc: AssertionError):
        """断言错误处理"""
        if settings.ENVIRONMENT == "development":
            content = {
                "code": StandardResponseCode.HTTP_500,
                "msg": str("".join(exc.args) if exc.args else exc.__doc__),
                "data": None,
            }
        else:
            res = response_base.fail(res=CustomResponseCode.HTTP_500)
            content = res.model_dump()
        request.state.__request_assertion_error__ = content
        if settings.ENVIRONMENT == "development":
            content.update(trace_id=get_request_trace_id(request))
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_500,
            content=content,
        )

    @app.exception_handler(BaseExceptionMixin)
    async def custom_exception_handler(request: Request, exc: BaseExceptionMixin):
        """全局自定义异常处理"""
        content = {
            "code": exc.code,
            "msg": str(exc.msg),
            "data": exc.data if exc.data else None,
        }
        request.state.__request_custom_exception__ = content
        if settings.ENVIRONMENT == "development":
            content.update(trace_id=get_request_trace_id(request))
        return MsgSpecJSONResponse(
            status_code=_get_exception_code(exc.code),
            content=content,
            background=exc.background,
        )

    @app.exception_handler(Exception)
    async def all_unknown_exception_handler(request: Request, exc: Exception):
        """全局未知异常处理"""
        if settings.ENVIRONMENT == "development":
            content = {
                "code": StandardResponseCode.HTTP_500,
                "msg": str(exc),
                "data": None,
            }
        else:
            res = response_base.fail(res=CustomResponseCode.HTTP_500)
            content = res.model_dump()
        request.state.__request_all_unknown_exception__ = content
        if settings.ENVIRONMENT == "development":
            content.update(trace_id=get_request_trace_id(request))
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_500,
            content=content,
        )

    if settings.MIDDLEWARE_CORS:

        @app.exception_handler(StandardResponseCode.HTTP_500)
        async def cors_custom_code_500_exception_handler(request, exc):
            """
            跨域 - 自定义 500 异常处理

            `Related issue <https://github.com/encode/starlette/issues/1175>`_
            `Solution <https://github.com/fastapi/fastapi/discussions/7847#discussioncomment-5144709>`_
            """
            if isinstance(exc, BaseExceptionMixin):
                content = {
                    "code": exc.code,
                    "msg": exc.msg,
                    "data": exc.data,
                }
            else:
                if settings.ENVIRONMENT == "development":
                    content = {
                        "code": StandardResponseCode.HTTP_500,
                        "msg": str(exc),
                        "data": None,
                    }
                else:
                    res = response_base.fail(res=CustomResponseCode.HTTP_500)
                    content = res.model_dump()
            request.state.__request_cors_500_exception__ = content
            if settings.ENVIRONMENT == "development":
                content.update(trace_id=get_request_trace_id(request))
            response = MsgSpecJSONResponse(
                status_code=(
                    exc.code
                    if isinstance(exc, BaseExceptionMixin)
                    else StandardResponseCode.HTTP_500
                ),
                content=content,
                background=(
                    exc.background if isinstance(exc, BaseExceptionMixin) else None
                ),
            )
            origin = request.headers.get("origin")
            if origin:
                cors = CORSMiddleware(
                    app=app,
                    allow_origins=settings.CORS_ALLOWED_ORIGINS,
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                    expose_headers=settings.CORS_EXPOSE_HEADERS,
                )
                response.headers.update(cors.simple_headers)
                has_cookie = "cookie" in request.headers
                if cors.allow_all_origins and has_cookie:
                    response.headers["Access-Control-Allow-Origin"] = origin
                elif not cors.allow_all_origins and cors.is_allowed_origin(
                    origin=origin
                ):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers.add_vary_header("Origin")
            return response
