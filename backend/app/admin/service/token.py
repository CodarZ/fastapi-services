#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Annotated, Set

from fastapi import Query, Request
from backend.app.admin.schema.token import KickOutToken, LoginTokenDetail
from backend.common.enums import StatusEnum
from backend.common.security.jwt import admin_verify, jwt_decode
from backend.database.redis import redis_client
from backend.core.config import settings


class TokenService:
    @staticmethod
    async def get_token_list(username: Annotated[str | None, Query()] = None):
        token_keys = await redis_client.keys(f"{settings.TOKEN_REDIS_PREFIX}:*")
        token_online: Set[str] = await redis_client.smembers(
            settings.TOKEN_ONLINE_REDIS_PREFIX
        )  # type: ignore

        data = []

        for key in token_keys:
            token = await redis_client.get(key)
            payload = jwt_decode(token)
            session_uuid = payload.session_uuid
            token_detail = LoginTokenDetail(
                id=payload.id,
                session_uuid=session_uuid,
                username="未知",
                nickname="未知",
                ip="未知",
                os="未知",
                browser="未知",
                device="未知",
                status=(
                    StatusEnum.NO
                    if session_uuid not in token_online
                    else StatusEnum.YES
                ),
                last_login_time="未知",
                expire_time=payload.expire_time,
            )
            extra_info = await redis_client.get(
                f"{settings.TOKEN_EXTRA_INFO_REDIS_PREFIX}:{session_uuid}"
            )
            if extra_info:

                def append_token_detail():
                    data.append(
                        token_detail.model_copy(
                            update={
                                "username": extra_info.get("username"),
                                "nickname": extra_info.get("nickname"),
                                "ip": extra_info.get("ip"),
                                "os": extra_info.get("os"),
                                "browser": extra_info.get("browser"),
                                "device": extra_info.get("device"),
                                "last_login_time": extra_info.get("last_login_time"),
                            }
                        )
                    )

                extra_info = json.loads(extra_info)
                if extra_info.get("login_type") != "swagger":
                    if not username or username == extra_info.get("username"):
                        append_token_detail()
            else:
                data.append(token_detail)

            return data

    @staticmethod
    async def kick_out(request: Request, user_id: int, KickOutToken: KickOutToken):
        admin_verify(request)
        # 删除 当前会话 token
        await redis_client.delete(
            f"{settings.TOKEN_REDIS_PREFIX}:{user_id}:{KickOutToken.session_uuid}"
        )
        await redis_client.delete(
            f"{settings.TOKEN_EXTRA_INFO_REDIS_PREFIX}:{user_id}:{KickOutToken.session_uuid}"
        )


token_service = TokenService()
