"""网络服务接口

定义网络操作的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from .network_types import HttpMethod


class INetworkService(ABC):
    """网络服务接口
    
    定义网络操作的核心功能。
    """
    
    @abstractmethod
    async def request(
        self,
        method: HttpMethod,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        verify_ssl: bool = True
    ) -> Dict[str, Any]:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            params: URL参数
            data: 请求体数据
            json: JSON数据
            timeout: 超时时间（秒）
            verify_ssl: 是否验证SSL证书
            
        Returns:
            响应数据字典
        """
        pass
    
    @abstractmethod
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """发送GET请求
        
        Args:
            url: 请求URL
            headers: 请求头
            params: URL参数
            timeout: 超时时间（秒）
            
        Returns:
            响应数据字典
        """
        pass
    
    @abstractmethod
    async def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """发送POST请求
        
        Args:
            url: 请求URL
            headers: 请求头
            data: 请求体数据
            json: JSON数据
            timeout: 超时时间（秒）
            
        Returns:
            响应数据字典
        """
        pass
    
    @abstractmethod
    async def put(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """发送PUT请求
        
        Args:
            url: 请求URL
            headers: 请求头
            data: 请求体数据
            json: JSON数据
            timeout: 超时时间（秒）
            
        Returns:
            响应数据字典
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """发送DELETE请求
        
        Args:
            url: 请求URL
            headers: 请求头
            timeout: 超时时间（秒）
            
        Returns:
            响应数据字典
        """
        pass
    
    @abstractmethod
    async def download_file(
        self,
        url: str,
        file_path: str,
        headers: Optional[Dict[str, str]] = None,
        chunk_size: int = 8192,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """下载文件
        
        Args:
            url: 文件URL
            file_path: 保存路径
            headers: 请求头
            chunk_size: 块大小
            progress_callback: 进度回调函数
            
        Returns:
            是否下载成功
        """
        pass
    
    @abstractmethod
    async def upload_file(
        self,
        url: str,
        file_path: str,
        field_name: str = "file",
        headers: Optional[Dict[str, str]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """上传文件
        
        Args:
            url: 上传URL
            file_path: 文件路径
            field_name: 表单字段名
            headers: 请求头
            additional_data: 额外数据
            progress_callback: 进度回调函数
            
        Returns:
            响应数据字典
        """
        pass
    
    @abstractmethod
    async def check_connectivity(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """检查网络连通性
        
        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间（秒）
            
        Returns:
            是否连通
        """
        pass
    
    @abstractmethod
    async def ping(self, host: str, count: int = 4, timeout: float = 5.0) -> Dict[str, Any]:
        """Ping主机
        
        Args:
            host: 主机地址
            count: ping次数
            timeout: 超时时间（秒）
            
        Returns:
            Ping结果字典
        """
        pass
    
    @abstractmethod
    async def get_public_ip(self) -> Optional[str]:
        """获取公网IP地址
        
        Returns:
            公网IP地址
        """
        pass
    
    @abstractmethod
    async def get_local_ip(self) -> List[str]:
        """获取本地IP地址列表
        
        Returns:
            本地IP地址列表
        """
        pass
    
    @abstractmethod
    async def resolve_hostname(self, hostname: str) -> List[str]:
        """解析主机名
        
        Args:
            hostname: 主机名
            
        Returns:
            IP地址列表
        """
        pass
    
    @abstractmethod
    async def reverse_dns(self, ip: str) -> Optional[str]:
        """反向DNS查询
        
        Args:
            ip: IP地址
            
        Returns:
            主机名
        """
        pass
    
    @abstractmethod
    async def get_network_interfaces(self) -> List[Dict[str, Any]]:
        """获取网络接口信息
        
        Returns:
            网络接口信息列表
        """
        pass
    
    @abstractmethod
    async def get_network_stats(self) -> Dict[str, Any]:
        """获取网络统计信息
        
        Returns:
            网络统计信息字典
        """
        pass
    
    @abstractmethod
    async def create_websocket_connection(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        protocols: Optional[List[str]] = None
    ) -> Any:
        """创建WebSocket连接
        
        Args:
            url: WebSocket URL
            headers: 请求头
            protocols: 子协议列表
            
        Returns:
            WebSocket连接对象
        """
        pass
    
    @abstractmethod
    async def send_websocket_message(
        self,
        connection: Any,
        message: Union[str, bytes, Dict[str, Any]]
    ) -> bool:
        """发送WebSocket消息
        
        Args:
            connection: WebSocket连接
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def receive_websocket_message(self, connection: Any, timeout: Optional[float] = None) -> Any:
        """接收WebSocket消息
        
        Args:
            connection: WebSocket连接
            timeout: 超时时间（秒）
            
        Returns:
            接收到的消息
        """
        pass
    
    @abstractmethod
    async def close_websocket_connection(self, connection: Any) -> bool:
        """关闭WebSocket连接
        
        Args:
            connection: WebSocket连接
            
        Returns:
            是否关闭成功
        """
        pass
    
    @abstractmethod
    async def set_proxy(
        self,
        proxy_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> bool:
        """设置代理
        
        Args:
            proxy_url: 代理URL
            username: 用户名
            password: 密码
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    async def clear_proxy(self) -> bool:
        """清除代理设置
        
        Returns:
            是否清除成功
        """
        pass
    
    @abstractmethod
    async def get_request_history(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取请求历史
        
        Args:
            limit: 限制数量
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            请求历史列表
        """
        pass
    
    @abstractmethod
    async def clear_request_history(self) -> bool:
        """清除请求历史
        
        Returns:
            是否清除成功
        """
        pass
    
    @abstractmethod
    async def get_connection_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息
        
        Returns:
            连接池统计信息字典
        """
        pass
    
    @abstractmethod
    async def configure_session(
        self,
        timeout: Optional[float] = None,
        max_connections: Optional[int] = None,
        max_keepalive_connections: Optional[int] = None,
        keepalive_expiry: Optional[float] = None
    ) -> bool:
        """配置会话
        
        Args:
            timeout: 默认超时时间
            max_connections: 最大连接数
            max_keepalive_connections: 最大保持连接数
            keepalive_expiry: 保持连接过期时间
            
        Returns:
            是否配置成功
        """
        pass
    
    @abstractmethod
    async def close_session(self) -> bool:
        """关闭会话
        
        Returns:
            是否关闭成功
        """
        pass