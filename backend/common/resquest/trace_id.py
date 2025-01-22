#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request

from backend.core.config import settings


def get_request_trace_id(request: Request) -> str:
    """从请求中提取 Trace ID"""
    return (
        request.headers.get(settings.TRACE_ID_REQUEST_HEADER_KEY)
        or settings.LOG_CID_DEFAULT_VALUE
    )
