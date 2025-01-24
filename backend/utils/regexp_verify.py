#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re


def search_string(pattern, text) -> bool:
    """全字段正则匹配"""
    result = re.search(pattern, text)
    if result:
        return True
    else:
        return False


def match_string(pattern, text) -> bool:
    """从字段开头正则匹配"""
    result = re.match(pattern, text)
    if result:
        return True
    else:
        return False


def is_phone(text: str) -> bool:
    """检查手机号码"""
    return match_string(r"^1[3-9]\d{9}$", text)


def is_email(text: str) -> bool:
    """检查邮箱地址"""
    return match_string(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", text)


def is_ip(text: str) -> bool:
    """检查 IPv4 地址"""
    return match_string(r"^(?:\d{1,3}\.){3}\d{1,3}$", text)


def is_url(text: str) -> bool:
    """检查 URL 地址"""
    return match_string(r"^https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})+.*$", text)


def is_postal_code(text: str) -> bool:
    """检查邮政编码（中国）"""
    return match_string(r"^\d{6}$", text)


def is_id_card(text: str) -> bool:
    """检查身份证号（中国，18 位）"""
    return match_string(r"^\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}(\d|X|x)$", text)


def is_plate_number(text: str) -> bool:
    """检查车牌号（中国大陆）"""
    return match_string(
        r"^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{4}[A-Z0-9挂学警港澳]$", text
    )


def is_hex_color(text: str) -> bool:
    """检查十六进制颜色代码"""
    return match_string(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", text)


def is_password(text: str) -> bool:
    """检查密码（8-24 位，包含字母和数字）"""
    return match_string(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,24}$", text)


def is_date(text: str) -> bool:
    """检查日期格式 YYYY-MM-DD"""
    return match_string(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$", text)


def is_time(text: str) -> bool:
    """检查时间格式 HH:MM:SS"""
    return match_string(r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$", text)


def is_datetime(text: str) -> bool:
    """检查日期时间格式 YYYY-MM-DD HH:MM:SS"""
    return match_string(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]) (?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$", text)


def is_username(text: str) -> bool:
    """检查用户名（以字母或下划线开头，后续为 4-16 位字母、数字或下划线）"""
    return match_string(r"^[a-zA-Z_][a-zA-Z0-9_]{3,15}$", text)


def is_number(text: str) -> bool:
    """检查是否为数字"""
    return match_string(r"^\d+(\.\d+)?$", text)


def is_html_tag(text: str) -> bool:
    """检查是否为 HTML 标签"""
    return match_string(r"^<[^>]+>$", text)
