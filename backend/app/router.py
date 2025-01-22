#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from core.config import settings

all_routes = APIRouter(prefix=settings.API_ROUTE_PREFIX)
