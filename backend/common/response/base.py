#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Generic, TypeVar

from fastapi import Response
from pydantic import BaseModel

from backend.common.response.code import CustomResponse, CustomResponseCode
from backend.utils.serializers import MsgSpecJSONResponse

SchemaT = TypeVar("SchemaT")

# 定义模块对外暴露的类和变量，供其他模块引用
__all__ = ["ResponseModel", "response_base"]


class ResponseModel(BaseModel):
    """
    统一的响应数据模型。

    通过 Pydantic 定义的数据模型，用于返回统一格式的接口响应。

    示例用法::

        # 示例 1：直接返回 ResponseModel
        @router.get('/test', response_model=ResponseModel)
        def test():
            return ResponseModel(data={'test': 'test'})

        # 示例 2：方法返回类型为 ResponseModel
        @router.get('/test')
        def test() -> ResponseModel:
            return ResponseModel(data={'test': 'test'})

        # 示例 3：自定义返回码和消息
        @router.get('/test')
        def test() -> ResponseModel:
            res = CustomResponseCode.HTTP_200
            return ResponseModel(code=res.code, msg=res.msg, data={'test': 'test'})
    """

    # json_encoders 配置失效的参考问题：https://github.com/tiangolo/fastapi/discussions/10252
    # model_config = ConfigDict(
    #     json_encoders={
    #         datetime: lambda x: x.strftime(settings.DATETIME_FORMAT)
    #     }  # 设置 datetime 格式化输出
    # )

    # 定义响应模型的字段
    code: int = CustomResponseCode.HTTP_200.code  # 默认响应码
    msg: str = CustomResponseCode.HTTP_200.msg  # 默认响应消息
    data: Any | None = None  # 返回数据，默认为 None


class ResponseSchemaModel(ResponseModel, Generic[SchemaT]):
    """
    包含 data schema 的统一返回模型，适用于非分页接口

    示例用法::

        # 示例 1：
        @router.get('/test', response_model=ResponseSchemaModel[GetApiDetail])
        def test():
            return ResponseSchemaModel[GetApiDetail](data=GetApiDetail(...))


        # 示例 2：
        @router.get('/test')
        def test() -> ResponseSchemaModel[GetApiDetail]:
            return ResponseSchemaModel[GetApiDetail](data=GetApiDetail(...))


        # 示例 3：
        @router.get('/test')
        def test() -> ResponseSchemaModel[GetApiDetail]:
            res = CustomResponseCode.HTTP_200
            return ResponseSchemaModel[GetApiDetail](code=res.code, msg=res.msg, data=GetApiDetail(...))
    """

    data: SchemaT


class ResponseBase:
    """
    统一返回方法，快速生成标准化的响应模型。
    """

    @staticmethod
    def __response(
        *, res: CustomResponseCode | CustomResponse = None, msg: str = None, code: int = None, data: Any | None = None
    ) -> ResponseModel | ResponseSchemaModel:
        response_code = code if code is not None else res.code
        response_msg = msg if msg is not None else res.msg

        return ResponseModel(code=response_code, msg=response_msg, data=data)

    def success(
        self,
        *,
        res: CustomResponseCode | CustomResponse = CustomResponseCode.HTTP_200,
        msg: str = None,
        code: int = None,
        data: Any | None = None,
    ) -> ResponseModel | ResponseSchemaModel:
        """
        快捷方法，用于生成成功响应。

        :param res: 成功状态码及信息（默认为 HTTP_200）（CustomResponseCode 或 CustomResponse 实例）
        :param msg: 自定义返回消息（可选）
        :param code: 自定义返回状态码（可选）
        :param data: 成功返回的数据（可选）
        :return: 统一格式的成功响应 ResponseModel 模型
        """
        return self.__response(res=res, msg=msg, code=code, data=data)

    def fail(
        self,
        *,
        res: CustomResponseCode | CustomResponse = CustomResponseCode.HTTP_400,
        msg: str = None,
        code: int = None,
        data: Any = None,
    ) -> ResponseModel | ResponseSchemaModel:
        """
        快捷方法，用于生成失败响应。

        :param res: 失败状态码及信息（默认为 HTTP_400）（CustomResponseCode 或 CustomResponse 实例）
        :param msg: 自定义返回消息（可选）
        :param code: 自定义返回状态码（可选）
        :param data: 失败返回的数据（可选）
        :return: 统一格式的失败响应 ResponseModel 模型
        """
        return self.__response(res=res, msg=msg, code=code, data=data)

    @staticmethod
    def fast_success(
        *,
        res: CustomResponseCode | CustomResponse = CustomResponseCode.HTTP_200,
        data: Any | None = None,
    ) -> Response:
        """
        此方法是为了提高接口响应速度而创建的，在解析较大 json 时有显著性能提升，但将丢失 pydantic 解析和验证

        .. warning::

            使用此返回方法时，不能指定接口参数 response_model 和箭头返回类型

        示例用法::

            @router.get('/test')
            def test():
                return response_base.fast_success(data={'test': 'test'})

        :param res: 成功状态码及信息（默认为 HTTP_200）
        :param data: 返回的数据（可选）
        :return: 直接返回序列化后的 JSON 数据
        """
        return MsgSpecJSONResponse({"code": res.code, "msg": res.msg, "data": data})


response_base: ResponseBase = ResponseBase()
