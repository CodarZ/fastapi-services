#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination
from starlette.middleware.authentication import AuthenticationMiddleware

from backend.app.router import all_routes
from backend.common.exception.handler import register_exception
from backend.common.logger import register_logger
from backend.common.response.check import ensure_unique_route_names, http_limit_callback
from backend.core.config import settings
from backend.core.paths import STATIC_DIR
from backend.database.mysql import create_table
from backend.database.redis import redis_client
from backend.middleware.jwt_auth import JwtAuthMiddleware
from backend.middleware.state import StateMiddleware
from backend.utils.openapi import simplify_operation_ids


@asynccontextmanager
async def register_lifespan(_: FastAPI):
    # 创建数据库表
    await create_table()
    # 连接 redis
    await redis_client.open()
    # 初始化 limiter
    await FastAPILimiter.init(
        redis=redis_client,
        prefix=settings.REQUEST_LIMITER_REDIS_PREFIX,
        http_callback=http_limit_callback,
    )
    yield

    # 关闭 redis 连接
    await redis_client.close()
    # 关闭 limiter
    await FastAPILimiter.close()


def register_app():
    # FastAPI
    app = FastAPI(
        title=settings.TITLE,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOCS_URL,
        openapi_url=settings.OPENAPI_URL,
        lifespan=register_lifespan,
    )

    # 日志
    register_logger()

    # 静态文件
    register_static_file(app)

    # 中间件
    register_middleware(app)

    # 路由
    register_router(app)

    # 分页
    register_page(app)

    # 全局异常处理
    register_exception(app)

    return app


def register_static_file(app: FastAPI):
    """
    静态文件交互开发模式, 生产不要开启
    """
    if settings.FASTAPI_STATIC_FILES:
        from fastapi.staticfiles import StaticFiles

        if not os.path.exists(STATIC_DIR):
            os.makedirs(STATIC_DIR)

        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def register_middleware(app) -> None:
    """
    中间件，执行顺序从下往上
    :param app:
    :return:
    """

    # JWT 认证（必须）
    app.add_middleware(
        AuthenticationMiddleware, backend=JwtAuthMiddleware(), on_error=JwtAuthMiddleware.auth_exception_handler
    )

    # 接口访问日志
    if settings.MIDDLEWARE_ACCESS:
        from backend.middleware.access import AccessMiddleware

        app.add_middleware(AccessMiddleware)

    # State
    app.add_middleware(StateMiddleware)
    # Trace ID (必须)
    app.add_middleware(CorrelationIdMiddleware, validator=False)
    # 跨域: 需要一直配置在最后
    # if settings.MIDDLEWARE_CORS:
    #     from starlette.middleware.cors import CORSMiddleware
    #
    #     app.add_middleware(
    #         CORSMiddleware,
    #         allow_origins=["*"],
    #         allow_credentials=True,
    #         allow_methods=["*"],
    #         allow_headers=["*"],
    #     )
    if settings.MIDDLEWARE_CORS:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        )


def register_router(app: FastAPI):
    """路由"""

    # API
    app.include_router(all_routes, dependencies=None)

    # Extra
    ensure_unique_route_names(app)
    simplify_operation_ids(app)


def register_page(app: FastAPI):
    """分页查询"""
    add_pagination(app)
