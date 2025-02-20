#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response

from fastapi.security import HTTPBasicCredentials
from backend.app.admin.schema.token import SwaggerToken
from backend.app.admin.schema.user import AuthPhoneByPassword
from backend.app.admin.service.auth import auth_service
from backend.common.response.base import response_base
from backend.common.security.jwt import DependsJwtAuth

router = APIRouter()


# @router.post(
#     "/login/swagger", summary="Swagger 登录", description="Swagger 登录 快捷获取 token"
# )
# async def swagger_login(obj: Annotated[HTTPBasicCredentials, Depends()]):
#     token, user = await auth_service.swagger_login(obj=obj)

#     # TODO user 应该为 UserInfoDetail
#     return SwaggerToken(access_token=token, user=user)  # type: ignore


@router.post("/login", summary="通过手机号和密码登录")
async def user_login(obj: AuthPhoneByPassword, request: Request, response: Response):
    token = await auth_service.user_login(obj=obj, request=request, response=response)
    return token


@router.post("/logout", summary="用户登出", dependencies=[DependsJwtAuth])
async def user_logout(request: Request, response: Response):
    await auth_service.logout(request=request, response=response)
    return response_base.success()


@router.post("/refresh", summary="刷新 token")
async def refresh_token(request: Request, response: Response):
    data = await auth_service.refresh_new_token(request=request, response=response)
    return response_base.success(data=data)
