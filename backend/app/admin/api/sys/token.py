#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Annotated
from fastapi import APIRouter, Query, Request, Path

from backend.app.admin.schema.token import KickOutToken
from backend.common.response.base import response_base
from backend.common.security.jwt import DependsJwtAuth, admin_verify

from backend.app.admin.service.token import token_service
from backend.database.redis import redis_client
from backend.core.config import settings


router = APIRouter()


@router.get("/list", summary="获取token列表", dependencies=[DependsJwtAuth])
async def get_token_list():
    data = await token_service.get_token_list()
    return response_base.success(data=data)


@router.delete("/{user_id}", summary="删除token", dependencies=[DependsJwtAuth])
async def kick_out(
    request: Request, user_id: Annotated[int, Path(...)], KickOutToken: KickOutToken
):
    await token_service.kick_out(request, user_id, KickOutToken)
    return response_base.success(msg="退出成功")
