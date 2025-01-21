#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from decimal import Decimal
from typing import Any, Sequence, TypeVar

from fastapi.encoders import decimal_encoder
from msgspec import json
from sqlalchemy import Row, RowMapping
from sqlalchemy.orm import ColumnProperty, SynonymProperty, class_mapper
from starlette.responses import JSONResponse

# RowData 类型别名，表示可能是 SQLAlchemy 的 Row、RowMapping 类型或其他任意类型
RowData = Row | RowMapping | Any

# 泛型 R，用于限定类型必须为 RowData
R = TypeVar("R", bound=RowData)


def select_columns_serialize(row: R) -> dict:
    """
    序列化 SQLAlchemy 查询结果的表列数据（不包含关联关系的列）。

    遍历给定 SQLAlchemy Row 对象中的所有表列，将其转换为字典格式，并对 Decimal 类型的数据进行处理。

    :param row: SQLAlchemy Row 对象，包含表列的查询结果
    :return: 序列化后的字典对象，仅包含表列的数据
    """
    result = {}
    # 遍历表中所有列名
    for column in row.__table__.columns.keys():
        # 获取列的值
        v = getattr(row, column)
        # 如果值是 Decimal 类型，则使用 fastapi 提供的 decimal_encoder 进行转换
        if isinstance(v, Decimal):
            v = decimal_encoder(v)
        # 将列名和对应的值加入结果字典
        result[column] = v
    return result


def select_list_serialize(row: Sequence[R]) -> list[dict[str, Any]]:
    """
    序列化 SQLAlchemy 查询结果列表。

    对多个 SQLAlchemy Row 对象依次调用 `select_columns_serialize` 方法，
    将查询结果列表转换为字典列表。

    :param row: 包含多个 SQLAlchemy Row 对象的序列
    :return: 序列化后的字典列表
    """
    # 对每个 Row 对象调用 select_columns_serialize，并生成字典列表
    result = [select_columns_serialize(_) for _ in row]
    return result


def select_as_dict(row: R, use_alias: bool = False) -> dict:
    """
    将 SQLAlchemy 查询结果转换为字典格式，可以包含关联数据。

    默认直接使用 Row 对象的 `__dict__` 属性。如果设置 `use_alias` 为 True，
    则会返回列的别名作为键（如果列未定义别名，不建议设置为 True）。

    :param row: SQLAlchemy Row 对象
    :param use_alias: 是否使用列的别名作为键（默认 False）
    :return: 转换后的字典
    """
    if not use_alias:
        # 如果不使用别名，直接获取对象的字典属性
        result = row.__dict__
        # 删除 SQLAlchemy 自动生成的内部状态属性
        if "_sa_instance_state" in result:
            del result["_sa_instance_state"]
    else:
        # 如果使用别名，遍历对象的所有列属性
        result = {}
        mapper = class_mapper(row.__class__)  # 获取对象的类映射
        for prop in mapper.iterate_properties:
            # 判断属性是否为列属性或同义词属性
            if isinstance(prop, (ColumnProperty, SynonymProperty)):
                key = prop.key  # 获取列的键（可能是别名）
                result[key] = getattr(row, key)  # 获取列值并加入结果字典

    return result


class MsgSpecJSONResponse(JSONResponse):
    """
    使用高性能 msgspec 库实现的 JSON 响应类。

    该类继承了 Starlette 提供的 JSONResponse，并通过覆盖 `render` 方法，
    使用 msgspec 库将数据序列化为 JSON 格式，显著提升响应性能。
    """

    def render(self, content: Any) -> bytes:
        """
        重写 `render` 方法，将输入内容序列化为 JSON 字节流。

        使用 msgspec 提供的 `json.encode` 方法高效地将 Python 数据转换为 JSON 格式的字节流。

        :param content: 需要序列化的任意数据
        :return: 序列化后的 JSON 字节流
        """
        return json.encode(content)
