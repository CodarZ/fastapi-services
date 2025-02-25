#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from backend.app.admin.schema.user import RegisterUser, UpdateUser, UserInfoDetail
from backend.app.admin.service.user import user_service
from backend.common.pagination import DependsPagination, PageData, paging_data
from backend.common.response.base import (
    ResponseModel,
    ResponseSchemaModel,
    response_base,
)
from backend.common.security.jwt import DependsJwtAuth
from backend.database.mysql import CurrentSession
from backend.utils.serializers import select_as_dict

router = APIRouter()


@router.post("/register", summary="通过手机号和密码注册用户")
async def register_user(obj: RegisterUser) -> ResponseModel:
    await user_service.register(obj=obj)
    return response_base.success()


@router.delete(
    "/deleteUser", summary="通过 id 删除用户信息", dependencies=[DependsJwtAuth]
)
async def delete_user(id: int) -> ResponseModel:
    count = await user_service.delete(id=id)
    if count > 0:
        return response_base.success(msg="删除成功")
    return response_base.fail(msg="删除失败")


@router.put(
    "/updateUser",
    summary="通过 id 更新用户必要的信息，不可修改状态等",
    dependencies=[DependsJwtAuth],
)
async def update_user(id: int, obj: UpdateUser) -> ResponseModel:
    count = await user_service.update(id=id, obj=obj)
    if count > 0:
        return response_base.success(msg="更新信息成功")
    return response_base.fail(msg="更新信息失败")


@router.get(
    "/getUser",
    summary="获取用户详情信息",
    response_model=ResponseSchemaModel[UserInfoDetail],
    dependencies=[DependsJwtAuth],
)
async def get_user(id: int) -> ResponseModel:
    current_user = await user_service.get(id=id)
    data = UserInfoDetail(**select_as_dict(current_user))
    return response_base.success(data=data)


@router.get(
    "/list",
    summary="获取用户详情信息",
    response_model=ResponseSchemaModel[PageData[UserInfoDetail]],
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def get_user_list(
    db: CurrentSession,
):
    data_select = await user_service.get_list()
    page_data = await paging_data(db, data_select)
    return response_base.success(data=page_data)
