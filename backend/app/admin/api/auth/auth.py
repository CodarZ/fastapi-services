#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response, BackgroundTasks
from fastapi.security import HTTPBasicCredentials, OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter

from backend.app.admin.schema.user import AuthPhoneByPassword
from backend.app.admin.service.auth import auth_service

from backend.app.admin.schema.token import LoginUserInfo, AccessTokenBase, SwaggerToken

from backend.common.response.base import (
    ResponseModel,
    ResponseSchemaModel,
    response_base,
)
from backend.common.security.jwt import DependsJwtAuth

router = APIRouter()


@router.post(
    "/login",
    summary="用户使用 账户密码 登录",
    dependencies=[Depends(RateLimiter(times=5, minutes=1))],
)
async def user_login(
    request: Request,
    response: Response,
    obj: AuthPhoneByPassword,
    background_tasks: BackgroundTasks,
) -> ResponseSchemaModel[LoginUserInfo]:
    data = await auth_service.login(
        request=request, response=response, obj=obj, background_tasks=background_tasks
    )
    return response_base.success(data=data)


@router.post("/logout", summary="用户登出", dependencies=[DependsJwtAuth])
async def user_logout(request: Request, response: Response) -> ResponseModel:
    await auth_service.logout(request=request, response=response)
    return response_base.success()


@router.post(
    "/login/swagger",
    summary="swagger 调试专用",
    description="用于快捷获取 token 进行 swagger 认证",
)
async def swagger_login(obj: AuthPhoneByPassword) -> SwaggerToken:
    token, user = await auth_service.swagger_login(obj=obj)
    return SwaggerToken(access_token=token, user=user)


@router.post("/token/new", summary="根据 Refresh Token 创建新 token")
async def create_new_token(
    request: Request, response: Response
) -> ResponseSchemaModel[AccessTokenBase]:
    data = await auth_service.new_token(request=request)
    return response_base.success(data=data)
