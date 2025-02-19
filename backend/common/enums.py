#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum, IntEnum as SourceIntEnum
from typing import Type


class _EnumBase(Enum):
    """
    枚举辅助基类，用于扩展枚举类的功能

    `cls.__members__` 是枚举类的特殊属性，包含所有成员的键值对。
    """

    @classmethod
    def get_member_keys(cls: Type[Enum]) -> list[str]:
        return [name for name in cls.__members__.keys()]

    @classmethod
    def get_member_values(cls: Type[Enum]) -> list:
        return [item.value for item in cls.__members__.values()]


class IntEnum(_EnumBase, SourceIntEnum):
    """整型枚举"""

    pass


class StrEnum(_EnumBase, str, Enum):
    """字符串枚举"""

    pass


class MenuEnum(IntEnum):
    """菜单类型枚举"""

    directory = 0
    menu = 1
    button = 2


class RoleDataRuleOperatorEnum(IntEnum):
    """数据权限规则运算符"""

    AND = 0
    OR = 1


class RoleDataRuleExpressionEnum(IntEnum):
    """数据权限规则表达式"""

    eq = 0  # ==
    ne = 1  # !=
    gt = 2  # >
    ge = 3  # >=
    lt = 4  # <
    le = 5  # <=
    in_ = 6
    not_in = 7


class MethodEnum(StrEnum):
    """请求方法"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class LoginLogStatusEnum(IntEnum):
    """登陆日志状态"""

    fail = 0
    success = 1


class BuildTreeEnum(StrEnum):
    """构建树形结构类型枚举"""

    traversal = "traversal"
    recursive = "recursive"


class OperaLogCipherEnum(IntEnum):
    """操作日志加密类型枚举"""

    aes = 0
    md5 = 1
    itsdangerous = 2
    plan = 3


class StatusEnum(IntEnum):
    """状态类型枚举"""

    NO = 0
    YES = 1


class UserSocialEnum(str, Enum):
    """用户社交类型枚举"""

    WECHAT = "微信"
    QQ = "QQ"
    WEIBO = "微博"
    DOUYIN = "抖音"
    XIAOHONGSHU = "小红书"
    TAOBAO = "淘宝"
    JD = "京东"
    PINDUODUO = "拼多多"
    ALIPAY = "支付宝"
    ZHIHU = "知乎"
    BILIBILI = "哔哩哔哩"
    KUWO = "酷我"
    KUKE = "酷客"
    MEITUAN = "美团"
    ELEME = "饿了么"
    TIEBA = "百度贴吧"
    YOUKU = "优酷"
    TOUTIAO = "今日头条"
    EMAIL = "邮箱"
    PHONE = "手机号"
    OTHER = "其他平台"


class UserSourceEnum(str, Enum):
    """用户来源枚举"""

    ORGANIC_SEARCH = "organic_search"  # 自然搜索
    PAID_SEARCH = "paid_search"  # 付费搜索（如百度推广、360竞价）
    SOCIAL_MEDIA = "social_media"  # 社交媒体引流
    DIRECT_ACCESS = "direct_access"  # 直接访问
    REFERRAL = "referral"  # 外部链接跳转
    APP_STORE = "app_store"  # 应用商店
    QR_CODE = "qr_code"  # 扫描二维码
    OFFLINE_EVENT = "offline_event"  # 线下活动
    FRIEND_RECOMMENDATION = "friend_recommendation"  # 好友推荐
    CONTENT_MARKETING = "content_marketing"  # 内容营销（如软文、视频）
    ECOMMERCE_PARTNER = "ecommerce_partner"  # 电商合作伙伴（如京东、天猫）
    BANNER_AD = "banner_ad"  # 横幅广告
    PUSH_NOTIFICATION = "push_notification"  # 推送通知
    SMS_PROMOTION = "sms_promotion"  # 短信营销
    EMAIL_MARKETING = "email_marketing"  # 邮件营销
    KOL_PROMOTION = "kol_promotion"  # KOL（关键意见领袖）推广
    LIVE_STREAMING = "live_streaming"  # 直播推广（如抖音直播、快手直播）
    OFFICIAL_WEBSITE = "official_website"  # 官方网站
    CUSTOMER_SERVICE = "customer_service"  # 客服推荐
    OTHER = "other"  # 其他来源
