#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from math import ceil

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

from backend.common.exception import errors
from backend.common.response.code import CustomResponseCode


def ensure_unique_route_names(app: FastAPI) -> None:
    """
    检查路由名称是否唯一

    :param app: FastAPI 应用实例
    :return: 无返回值；若发现重复路由名称则抛出 ValueError
    """
    temp_routes = set()
    for route in app.routes:  # 遍历所有路由
        if isinstance(route, APIRoute):  # 检查当前路由是否为 APIRoute 类型
            if route.name in temp_routes:  # 判断路由名称是否已存在
                raise ValueError(f"路由名称重复: {route.name}")
            temp_routes.add(route.name)  # 记录路由名称


async def http_limit_callback(request: Request, response: Response, expire: int):
    """
    请求限制时的默认回调函数

    :param request: 客户端的 HTTP 请求对象
    :param response: 返回给客户端的 HTTP 响应对象
    :param expire: 限制时间，单位为毫秒
    :return: 无返回值；直接抛出 HTTP 错误
    """
    expires = ceil(expire / 1000)  # 将毫秒转换为秒，并向上取整
    raise errors.HTTPError(
        code=CustomResponseCode.HTTP_429.code,  # HTTP 状态码 429 表示请求过多
        msg=CustomResponseCode.HTTP_429.msg,  # 返回的错误信息
        headers={"Retry-After": str(expires)},  # HTTP 响应头，告知客户端需要等待的时间
    )
