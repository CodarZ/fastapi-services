#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.common.logger import log
from backend.utils.timezone import timezone


class AccessMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件：
        - 记录每个 HTTP 请求的关键信息，包括：
        - 客户端 IP 地址
        - HTTP 方法（如 GET、POST）
        - 响应状态码（如 200、404）
        - 请求路径（如 /api/v1/resource）
        - 请求处理时间（毫秒级）
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        拦截每个 HTTP 请求，记录关键信息并继续调用下一个中间件或视图函数。

        :param request: FastAPI 的 Request 对象，表示当前 HTTP 请求
        :param call_next: 下一个中间件或视图函数的调用点
        :return: 响应对象
        """
        # 获取请求开始时间
        start_time = timezone.now()

        # 调用下一个中间件或视图函数，并等待响应返回
        response = await call_next(request)

        # 获取请求结束时间
        end_time = timezone.now()

        # 计算请求处理时间，单位为毫秒
        elapsed_time_ms = round((end_time - start_time).total_seconds(), 3) * 1000.0

        # 记录请求日志
        log.info(
            f'{(request.client.host if request.client else "unknown"): <15} | {request.method: <5} | {f"{elapsed_time_ms}ms": <9} |'
            f" {response.status_code: <3} | "
            f"{request.url.path}"
        )

        # 返回响应对象
        return response
