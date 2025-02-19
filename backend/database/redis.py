#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from redis.asyncio import Redis
from redis.exceptions import AuthenticationError, TimeoutError

from backend.common.logger import log
from backend.core.config import settings


class RedisClient(Redis):
    def __init__(self):
        super(RedisClient, self).__init__(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DATABASE,
            socket_timeout=settings.REDIS_TIMEOUT,
            decode_responses=True,
        )

    async def open(self):
        """
        初始化连接
        """
        try:
            await self.ping()
            log.success("✅ Redis 连接成功")
        except TimeoutError:
            log.error("❌ Redis 连接超时")
            sys.exit()
        except AuthenticationError:
            log.error("❌ Redis 认证失败")
            sys.exit()
        except Exception as e:
            log.error("❌ Redis 连接异常 {}", e)
            sys.exit()

    async def delete_prefix(self, prefix: str, exclude: str | list | None = None):
        """
        删除指定前缀的所有key

        :param prefix:
        :param exclude:
        :return:
        """
        keys = []
        async for key in self.scan_iter(match=f"{prefix}*"):
            if isinstance(exclude, str):
                if key != exclude:
                    keys.append(key)
            elif isinstance(exclude, list):
                if key not in exclude:
                    keys.append(key)
            else:
                keys.append(key)
        if keys:
            await self.delete(*keys)


# 创建 redis 客户端单例
redis_client: RedisClient = RedisClient()
