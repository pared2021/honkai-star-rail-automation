"""网络类型定义

定义网络相关的枚举和类型。
"""

from enum import Enum


class HttpMethod(Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class NetworkProtocol(Enum):
    """网络协议枚举"""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    WEBSOCKET = "websocket"