#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.common.logger import register_logger
from backend.core.config import settings
from backend.core.paths import STATIC_DIR


@asynccontextmanager
async def register_lifespan(app: FastAPI):
    yield


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

    # # 日志
    register_logger()
    #
    # # 静态文件
    register_static_file(app)
    #
    # # 中间件
    # register_middleware(app)
    #
    # # 路由
    # register_router(app)
    #
    # # 分页
    # register_page(app)
    #
    # # 全局异常处理
    # register_exception(app)

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
