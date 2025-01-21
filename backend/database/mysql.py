#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.common.logger import log
from backend.common.model import MappedBase
from backend.core.config import settings


def create_engine_and_session(url: str):
    """
    通过 `create_async_engine` 创建异步数据库引擎，
    通过 `async_sessionmaker` 创建数据库会话工厂。

    :param url: 数据库连接字符串
    :return: 数据库引擎和会话工厂
    """
    try:
        # 创建异步数据库引擎，启用连接池预检测
        engine = create_async_engine(
            url, echo=settings.DB_ECHO, future=True, pool_pre_ping=True
        )
        log.success("✅ MySQL 连接成功")
    except Exception as e:
        log.error("❌ MySQL 连接失败 {}", e)
    else:
        # 创建异步会话工厂
        db_session = async_sessionmaker(
            bind=engine, autoflush=False, expire_on_commit=False
        )
        return engine, db_session


async def get_db() -> AsyncSession:
    """
    session 数据库会话生成器。

    通过依赖注入的方式，在 FastAPI 的请求生命周期内提供异步数据库会话。
    在发生异常时回滚事务，并在会话结束后关闭会话。

    :yield: 异步数据库会话对象
    """
    session = async_db_session()
    try:
        yield session
    except Exception as se:
        # 如果发生异常，则回滚事务
        await session.rollback()
        raise se
    finally:
        # 关闭数据库会话
        await session.close()


async def create_table():
    """
    创建数据库表。

    通过 `MappedBase.metadata.create_all` 方法，根据定义的 SQLAlchemy 模型，自动创建数据库表。
    """
    async with async_engine.begin() as coon:
        # 在事务中运行同步方法以创建表
        await coon.run_sync(MappedBase.metadata.create_all)


def uuid4_str() -> str:
    """
    数据库引擎对 UUID 类型兼容性的解决方案。

    将 Python 的 UUID4 对象转换为字符串，以便在数据库中以文本格式存储。

    :return: UUID4 的字符串表示
    """
    return str(uuid4())


# 使用配置中的数据库 URI 创建异步数据库引擎和会话工厂
async_engine, async_db_session = create_engine_and_session(settings.MYSQL_DATABASE_URI)

# 使用 `Annotated` 类型为 FastAPI 依赖注入的会话提供类型提示
CurrentSession = Annotated[AsyncSession, Depends(get_db)]
