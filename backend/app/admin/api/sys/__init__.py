#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from .user import router as user_router
from .token import router as token_router

router = APIRouter(prefix="/sys")

router.include_router(user_router, prefix="/user", tags=["用户管理"])
router.include_router(token_router, prefix="/token", tags=["系统令牌"])
