#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter

from .sys import router as sys_router

admin_router = APIRouter()

admin_router.include_router(sys_router)
