#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.common.request.parse import parse_ip_info, parse_user_agent_info


class StateMiddleware(BaseHTTPMiddleware):
    """请求 state 中间件"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # noinspection PyBroadException
        try:
            ip_info = await parse_ip_info(request)

            # 设置附加请求信息
            request.state.ip = ip_info.ip
            request.state.country = ip_info.country
            request.state.region = ip_info.region
            request.state.city = ip_info.city
        except Exception as e:
            print(f"请求 state 中间件异常，没查到 IP 信息: {e}")
            pass

        ua_info = parse_user_agent_info(request)
        request.state.user_agent = ua_info.user_agent
        request.state.os = ua_info.os
        request.state.os_version = ua_info.os_version
        request.state.browser = ua_info.browser
        request.state.browser_version = ua_info.browser_version
        request.state.device = ua_info.device
        request.state.device_model = ua_info.device_model

        response = await call_next(request)

        return response
