#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from .auth import router as auth_router

router = APIRouter(prefix="/auth", tags=["认证授权"])

router.include_router(auth_router)
