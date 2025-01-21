#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

# 获取项目根目录
# 根目录 绝对路径
BasePath = Path(__file__).resolve().parent.parent.parent

# alembic 迁移文件存放路径
ALEMBIC_VERSIONS_DIR = os.path.join(BasePath, "alembic", "versions")

# env 环境变量文件
ENV_DIR = os.path.join(BasePath, "env")

# log 日志文件路径
LOG_DIR = os.path.join(BasePath, "log")

# static 挂载静态目录
STATIC_DIR = os.path.join(BasePath, "static")
