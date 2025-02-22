#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from .user import router as user_router

router = APIRouter(prefix="/sys")

router.include_router(user_router, prefix="/user", tags=["用户管理"])
