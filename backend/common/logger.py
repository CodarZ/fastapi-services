#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import logging
import os
from sys import stderr, stdout

from asgi_correlation_id import correlation_id
from loguru import logger

from backend.core.config import settings
from backend.core.paths import LOG_DIR


class InterceptHandler(logging.Handler):
    """
    自定义日志处理器，将标准 logging 日志转发到 loguru。
    详见：https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        # 尝试获取对应的 Loguru 日志等级
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找日志调用源的堆栈深度
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        # 使用 Loguru 记录日志
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    """
    配置统一日志系统，结合标准 logging 和 loguru。
    From https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
    https://github.com/pawamoy/pawamoy.github.io/issues/17
    """
    # 设置根日志处理器为 InterceptHandler
    logging.root.handlers = [InterceptHandler()]
    # 设置根日志级别
    logging.root.setLevel(settings.LOG_ROOT_LEVEL)

    # 遍历所有子日志记录器，移除默认处理器，设置传播选项
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []  # 移除子日志器的所有处理器
        if 'uvicorn.access' in name or 'watchfiles.main' in name:
            logging.getLogger(name).propagate = False  # 不传播日志
        else:
            logging.getLogger(name).propagate = True  # 传播日志到根记录器

        # 调试日志处理
        # logging.debug(f'{logging.getLogger(name)}, {logging.getLogger(name).propagate}')

    # 移除 Loguru 默认处理器
    logger.remove()

    # 定义相关联 ID 过滤函数
    # https://github.com/snok/asgi-correlation-id?tab=readme-ov-file#configure-logging
    # https://github.com/snok/asgi-correlation-id/issues/7
    def correlation_id_filter(record) -> bool:
        cid = correlation_id.get(settings.LOG_CID_DEFAULT_VALUE)
        record['correlation_id'] = cid[: settings.LOG_CID_UUID_LENGTH]
        return True

    # Configure loguru logger before starts logging
    logger.configure(
        handlers=[
            {
                # 输出到标准输出
                'sink': stdout,
                'level': settings.LOG_STDOUT_LEVEL,
                # 过滤低于 WARNING 的日志
                'filter': lambda record: correlation_id_filter(record) and record['level'].no <= 25,
                'format': settings.LOG_STD_FORMAT,
            },
            {
                # 输出到标准错误
                'sink': stderr,
                'level': settings.LOG_STDERR_LEVEL,
                # 过滤 WARNING 及以上的日志
                'filter': lambda record: correlation_id_filter(record) and record['level'].no >= 30,
                'format': settings.LOG_STD_FORMAT,
            },
        ]
    )


def set_customize_logfile():
    """
    配置自定义日志文件。
    """
    log_path = LOG_DIR
    if not os.path.exists(log_path):
        os.mkdir(log_path)

    # 日志文件路径
    log_stdout_file = os.path.join(log_path, settings.LOG_STDOUT_FILENAME)
    log_stderr_file = os.path.join(log_path, settings.LOG_STDERR_FILENAME)

    # 配置 Loguru 日志文件处理器
    # https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add
    log_config = {
        'rotation': '10 MB',  # 单个日志文件大小超过 10MB 时轮转
        'retention': '15 days',  # 保留最近 15 天的日志
        'compression': 'tar.gz',  # 旧日志压缩为 .tar.gz 格式
        'enqueue': True,  # 启用多线程安全
        'format': settings.LOG_FILE_FORMAT,  # 日志格式化样式
    }

    # 配置 stdout 日志文件
    logger.add(
        str(log_stdout_file),
        level=settings.LOG_STDOUT_LEVEL,
        **log_config,  # 使用通用日志配置
        backtrace=False,  # 禁用详细回溯信息
        diagnose=False,  # 禁用诊断信息
    )

    # 配置 stderr 日志文件
    logger.add(
        str(log_stderr_file),
        level=settings.LOG_STDERR_LEVEL,
        **log_config,
        backtrace=True,  # 启用详细回溯信息
        diagnose=True,  # 启用诊断信息
    )


def register_logger() -> None:
    """
    注册系统日志服务
    """
    setup_logging()
    set_customize_logfile()


log = logger
