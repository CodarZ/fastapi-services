#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from datetime import timedelta
from uuid import uuid4

from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
# JWT 相关库
from jose import ExpiredSignatureError, JWTError, jwt
# 密码加密验证库
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
# Pydantic 数据解析
from pydantic_core import from_json
# 异步数据库会话
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import User
from backend.app.admin.schema.user import UserInfoDetail
from backend.common.dataclasses import AccessToken, NewToken, RefreshToken, TokenPayload
from backend.common.exception.errors import AuthorizationError, TokenError
from backend.core.config import settings
from backend.database.mysql import async_db_session
from backend.database.redis import redis_client
from backend.utils.serializers import select_as_dict
from backend.utils.timezone import timezone

# JWT 认证依赖注入（自动解析请求头中 `Depends(DependsJwtAuth)` 的 Bearer Token）
DependsJwtAuth = Depends(HTTPBearer())

# 密码哈希实例初始化（使用 Bcrypt 算法），多个哈希器可共存，此处只使用 Bcrypt
password_hash = PasswordHash((BcryptHasher(),))


def get_hash_password(password: str, salt: bytes | None) -> str:
    """使用哈希算法加密密码（含盐值），生成格式如 "bcrypt$..." 的哈希字符串"""
    return password_hash.hash(password, salt=salt)


def password_verify(plain_password: str, hashed_password: str) -> bool:
    """自动解析算法并验证，验证明文密码与哈希值是否匹配"""
    return password_hash.verify(plain_password, hashed_password)


async def create_access_token(user_id: str, multi_login: bool, **kwargs) -> AccessToken:
    """
    生成加密的 Access Token

    :param user_id: 用户唯一标识
    :param multi_login: 是否允许多设备登录
    :param kwargs: 附加信息（如权限数据）
    :return: AccessToken 对象
    """
    # 计算过期时间（当前时间 + 配置中的有效期）
    expire = timezone.now() + timedelta(seconds=settings.TOKEN_EXPIRE_SECONDS)

    # 生成唯一会话 ID（用于控制多设备登录）
    session_uuid = str(uuid4())  # 示例：d7d1a8c0-8a3d-4f5e-9f6a-1c7b8d9e0f1a

    # JWT 编码（包含 payload 和签名）
    access_token = jwt.encode(
        {
            "session_uuid": session_uuid,  # 会话唯一标识
            "exp": expire,  # 过期时间戳（UTC）
            "sub": user_id,  # 用户标识主题（Subject）
        },
        settings.TOKEN_SECRET_KEY,  # 密钥（从配置读取）
        settings.TOKEN_ALGORITHM,  # 加密算法（如 HS256）
    )

    # 多设备登录控制逻辑
    if multi_login is False:
        # 删除该用户所有旧 Token（格式示例：TOKEN_REDIS_PREFIX:1）
        await redis_client.delete_prefix(f"{settings.TOKEN_REDIS_PREFIX}:{user_id}")

    # 存储 Token 到 Redis
    await redis_client.setex(
        f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{session_uuid}",
        settings.TOKEN_EXPIRE_SECONDS,  # 过期时间（秒）
        access_token,  # 存储的 Token 值
    )

    # 存储附加信息（如用户权限数据）
    if kwargs:
        await redis_client.setex(
            f"{settings.TOKEN_EXTRA_INFO_REDIS_PREFIX}:{session_uuid}",  # Key 示例：TOKEN_EXTRA_INFO:d7d1a8c0...
            settings.TOKEN_EXPIRE_SECONDS,  # 与 Token 相同的过期时间
            json.dumps(kwargs, ensure_ascii=False),  # 序列化为 JSON 字符串
        )

    # 返回结构化 Token 对象
    return AccessToken(access_token=access_token, access_token_expire_time=expire, session_uuid=session_uuid)


async def create_refresh_token(user_id: str, multi_login: bool) -> RefreshToken:
    """
    生成 Refresh Token（仅用于刷新 Access Token）

    :param user_id: 用户唯一标识
    :param multi_login: 是否允许多设备登录
    :return: RefreshToken 对象
    """
    # 计算过期时间（通常比 Access Token 长，一般是8 天）
    expire = timezone.now() + timedelta(seconds=settings.TOKEN_REFRESH_EXPIRE_SECONDS)

    # JWT 编码（仅包含用户 ID 和过期时间）
    refresh_token = jwt.encode(
        {"exp": expire, "sub": user_id},  # Payload
        settings.TOKEN_SECRET_KEY,  # 密钥（与 Access Token 相同）
        settings.TOKEN_ALGORITHM,  # 算法（如 HS256）
    )

    # 多设备登录控制
    if multi_login is False:
        # 删除该用户所有旧 Refresh Token（格式示例：REFRESH_TOKEN:1:*）
        await redis_client.delete_prefix(f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}")

    # 存储 Refresh Token（Key 示例：REFRESH_TOKEN:1:eyJhbGciOiJIUzI1NiIsIn...）
    await redis_client.setex(
        f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{refresh_token}",  # 包含完整 Token
        settings.TOKEN_REFRESH_EXPIRE_SECONDS,  # 过期时间（通常较长）
        refresh_token,  # 存储值与 Key 中的 Token 相同，便于验证
    )

    return RefreshToken(refresh_token=refresh_token, refresh_token_expire_time=expire)


async def create_new_token(user_id: str, token: str, refresh_token: str, multi_login: bool, **kwargs) -> NewToken:
    """
    通过 Refresh Token 生成新 Token

    :param user_id: 用户唯一标识
    :param token: 旧 Access Token（需验证有效性）
    :param refresh_token: 旧 Refresh Token（需验证有效性）
    :param multi_login: 是否允许多设备登录
    :param kwargs: 新 Token 的附加信息
    :return: NewToken 对象（包含新 Access/Refresh Token）
    """
    # 验证 Refresh Token 是否有效
    redis_refresh_token = await redis_client.get(f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{refresh_token}")
    # 检查 Redis 中是否存在且值匹配
    if not redis_refresh_token or redis_refresh_token != refresh_token:
        raise TokenError(msg="Refresh Token 已过期")

    # 解码旧 Access Token 获取会话信息
    token_payload = jwt_decode(token)  # 自定义解码函数（后文定义）

    # 生成新 Token
    new_access_token = await create_access_token(user_id, multi_login, **kwargs)
    new_refresh_token = await create_refresh_token(user_id, multi_login)

    # 删除旧 Token（防止重复使用）
    keys = [
        # 旧 Access Token 的 Redis Key
        f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{token_payload.session_uuid}",
        # 旧 Refresh Token 的 Redis Key
        f"{settings.TOKEN_REFRESH_REDIS_PREFIX}:{user_id}:{refresh_token}",
    ]
    for key in keys:
        await redis_client.delete(key)  # 异步删除 Key

    return NewToken(
        new_access_token=new_access_token.access_token,
        new_access_token_expire_time=new_access_token.access_token_expire_time,
        new_refresh_token=new_refresh_token.refresh_token,
        new_refresh_token_expire_time=new_refresh_token.refresh_token_expire_time,
        session_uuid=new_access_token.session_uuid,  # 新会话 ID
    )


def jwt_decode(token: str) -> TokenPayload:
    """
    解码并验证 Token 有效性

    :param token: JWT 字符串
    :return: TokenPayload 对象（包含用户 ID 和会话信息）
    """
    try:
        # 解码 JWT（自动验证签名和过期时间）
        payload = jwt.decode(
            token,
            settings.TOKEN_SECRET_KEY,  # 必须与编码时使用的密钥一致
            algorithms=[settings.TOKEN_ALGORITHM],  # 必须指定允许的算法列表
        )

        # 提取关键字段（兼容开发模式）
        session_uuid = payload.get("session_uuid") or "debug"  # 开发环境可能不传此字段
        user_id = payload.get("sub")  # JWT 标准字段 subject
        expire_time = payload.get("exp")  # 过期时间戳

        # 验证必要字段是否存在
        if not user_id:
            raise TokenError(msg="Token 无效")

    except ExpiredSignatureError:  # 捕获过期异常
        raise TokenError(msg="Token 已过期")
    except (JWTError, Exception):  # 捕获签名错误等通用异常
        raise TokenError(msg="Token 无效")

    # 返回结构化数据
    return TokenPayload(id=int(user_id), session_uuid=session_uuid, expire_time=expire_time)


async def get_current_user(db: AsyncSession, pk: int) -> User:
    """
    通过 Token 获取当前用户

    :param db: 异步数据库会话
    :param pk: 用户主键 ID
    :return: User 对象
    """
    from backend.app.admin.crud.user import user_crud  # 延迟导入避免循环依赖

    # 查询数据库用户
    user = await user_crud.get(db, user_id=pk)
    if not user:
        raise TokenError(msg="登录用户不存在")

    # 检查用户状态（是否被禁用）
    if not user.status:
        raise AuthorizationError(msg="用户已被锁定，请联系系统管理员")

    return user


async def jwt_authentication(token: str) -> UserInfoDetail:
    """
    完整的 JWT 认证流程

    :param token: JWT 字符串
    :return: 用户详细信息
    """
    # 解码 Token 获取基础信息
    token_payload = jwt_decode(token)
    user_id = token_payload.id

    # 验证 Token 是否在 Redis 中有效
    token_verify = await redis_client.get(f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{token_payload.session_uuid}")
    if not token_verify:
        raise TokenError(msg="Token 已过期")  # Redis 中不存在或已过期

    # 检查用户信息 Redis 缓存
    cache_user = await redis_client.get(f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}")
    if not cache_user:
        #  Redis 缓存未命中，查询数据库
        async with async_db_session() as db:
            current_user = await get_current_user(db, user_id)
            # 序列化用户信息
            user = UserInfoDetail(**select_as_dict(current_user))
            # 存储到 Redis
            await redis_client.setex(
                f"{settings.JWT_USER_REDIS_PREFIX}:{user_id}",
                settings.JWT_USER_REDIS_EXPIRE_SECONDS,
                user.model_dump_json(),  # Pydantic 模型转 JSON
            )
    else:
        # 使用缓存数据（允许部分字段缺失）
        user = UserInfoDetail.model_validate(from_json(cache_user, allow_partial=True))

    return user


def get_token(request: Request) -> str:
    """
    从请求头中提取并验证 Bearer Token

    :param request: FastAPI 请求对象（包含 HTTP 请求信息）
    :return: 提取到的 Token 字符串
    :raises TokenError: 当 Token 无效时抛出异常
    """
    # 从请求头获取 Authorization 字段值（格式应为 "Bearer <token>"）
    authorization = request.headers.get("Authorization")

    # 使用 FastAPI 工具函数分割认证方案和 Token
    # 示例输入："Bearer abc123" → scheme="Bearer", token="abc123"
    scheme, token = get_authorization_scheme_param(authorization)

    # 验证逻辑：
    # 1. 检查 Authorization 头是否存在
    # 2. 检查认证方案是否为 "bearer"（不区分大小写）
    if not authorization or scheme.lower() != "bearer":
        raise TokenError(msg="Token 无效")  # 抛出标准错误

    return token  # 返回纯 Token 字符串（不含 "Bearer" 前缀）


def admin_verify(request: Request) -> bool:
    """
    通过 Token 验证当前用户是否为管理员

    :param request: FastAPI 请求对象（包含用户信息）
    :return: 布尔值（True 表示是管理员）
    :raises AuthorizationError: 如果用户非管理员则抛出异常
    """
    # 从请求对象中提取用户的管理员权限状态
    # request.user 来自于 中间件 补充
    admin = request.user.is_admin

    if not admin:
        raise AuthorizationError(msg="权限不足，请联系管理员")

    return admin
