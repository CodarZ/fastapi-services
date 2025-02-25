#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING, Generic, Sequence, TypeVar

from fastapi import Depends, Query
from fastapi_pagination import pagination_ctx
from fastapi_pagination.bases import AbstractPage, AbstractParams, RawParams
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.links.bases import create_links
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")
SchemaT = TypeVar("SchemaT")


class _CustomPageParams(BaseModel, AbstractParams):
    page: int = Query(1, ge=1, description="页码, 从 1 开始")
    size: int = Query(20, gt=0, le=100, description="页大小, 默认 20 条记录")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=self.size * (self.page - 1),
        )


class _Links(BaseModel):
    first: str = Field(..., description="首页链接")
    last: str = Field(..., description="尾页链接")
    self: str = Field(..., description="当前页链接")
    next: str | None = Field(None, description="下一页链接")
    prev: str | None = Field(None, description="上一页链接")


class _PageDetails(BaseModel):
    items: list = Field([], description="当前页数据")
    total: int = Field(..., description="总条数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    links: _Links


class _CustomPage(_PageDetails, AbstractPage[T], Generic[T]):
    """
    自定义分页响应类，用于封装分页查询结果

    继承了 _PageDetails 以提供分页元数据
    实现了 AbstractPage 接口以与 fastapi-pagination 库集成
    使用 Generic[T] 支持泛型，T 为项目类型
    """

    __params_type__ = _CustomPageParams

    @classmethod
    def create(
        cls,
        items: list,
        params: _CustomPageParams,
        total: int,
        *,
        create_links=create_links,
    ) -> _CustomPage[T]:
        """
        创建分页响应对象

        Args:
            items:  当前页的数据项
            params: 分页参数
            total:  总数据量
            create_links: 用于生成分页链接的回调函数

        Returns:
            包含分页数据和元数据的 _CustomPage 实例
        """
        # raw_params = params.to_raw_params()
        # page = (
        #     params.page
        #     if hasattr(params, "page")
        #     else (raw_params.offset // raw_params.limit) + 1
        # )
        # size = params.size if hasattr(params, "size") else raw_params.limit
        # total_pages = ceil(total / size) if size else 0
        page = params.page
        size = params.size
        total_pages = ceil(total / size) if size else 0

        links = create_links(
            first={"page": 1, "size": size},
            last=(
                {"page": total_pages, "size": size}
                if total > 0
                else {"page": 1, "size": size}
            ),
            next=(
                {"page": f"{page + 1}", "size": size}
                if (page + 1) <= total_pages
                else None
            ),
            prev={"page": f"{page - 1}", "size": size} if (page - 1) >= 1 else None,
        ).model_dump()

        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links=links,
        )


class PageData(_PageDetails, Generic[SchemaT]):
    """
    通用分页数据模型，用于API响应接口

    继承了 _PageDetails 以提供分页元数据
    使用 Generic[SchemaT] 支持泛型，SchemaT 为数据项的模式类型

    本类用于将内部分页对象转换为面向API的响应格式


    Example:
        ```
        @router.get('/test', response_model=ResponseSchemaModel[PageData[GetApiDetail]])
        def test():
            return ResponseSchemaModel[PageData[GetApiDetail]](data=GetApiDetail(...))
        ```
    """

    items: list[SchemaT] = Field(..., description="当前页数据列表")


async def paging_data(db: AsyncSession, select: Select):
    """
    基于 SQLAlchemy 创建分页数据

    执行 SQLAlchemy 查询并应用分页，返回符合 _CustomPage 格式的分页结果
    """
    # result = await paginate(db, select)
    # return result

    paginated_data: _CustomPage = await paginate(db, select)
    page_data = paginated_data.model_dump()
    return page_data


# 分页依赖注入
DependsPagination = Depends(pagination_ctx(_CustomPage))
