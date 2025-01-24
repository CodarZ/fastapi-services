#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from backend.app.admin.api.router import admin_router

all_routes = APIRouter()

all_routes.include_router(admin_router)
