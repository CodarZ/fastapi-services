#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from .sys.user import router as user_router

admin_router = APIRouter(prefix="/system")

admin_router.include_router(user_router)
