"""安全接口

定义安全相关的抽象接口，包括身份验证、授权、加密等功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class AuthenticationMethod(Enum):
    """身份验证方法"""
    PASSWORD = "password"        # 密码验证
    TOKEN = "token"              # 令牌验证
    OAUTH = "oauth"              # OAuth验证
    LDAP = "ldap"                # LDAP验证
    BIOMETRIC = "biometric"      # 生物识别
    TWO_FACTOR = "two_factor"    # 双因素验证
    SSO = "sso"                  # 单点登录


class PermissionLevel(Enum):
    """权限级别"""
    NONE = "none"        # 无权限
    READ = "read"        # 读权限
    WRITE = "write"      # 写权限
    EXECUTE = "execute"  # 执行权限
    ADMIN = "admin"      # 管理员权限
    OWNER = "owner"      # 所有者权限


class EncryptionAlgorithm(Enum):
    """加密算法"""
    AES_256 = "aes_256"      # AES-256加密
    RSA_2048 = "rsa_2048"    # RSA-2048加密
    RSA_4096 = "rsa_4096"    # RSA-4096加密
    CHACHA20 = "chacha20"    # ChaCha20加密
    BLOWFISH = "blowfish"    # Blowfish加密


class HashAlgorithm(Enum):
    """哈希算法"""
    SHA256 = "sha256"        # SHA-256
    SHA512 = "sha512"        # SHA-512
    BCRYPT = "bcrypt"        # bcrypt
    SCRYPT = "scrypt"        # scrypt
    ARGON2 = "argon2"        # Argon2
    PBKDF2 = "pbkdf2"        # PBKDF2


class SecurityEventType(Enum):
    """安全事件类型"""
    LOGIN_SUCCESS = "login_success"      # 登录成功
    LOGIN_FAILURE = "login_failure"      # 登录失败
    LOGOUT = "logout"                    # 登出
    PERMISSION_DENIED = "permission_denied"  # 权限拒绝
    DATA_ACCESS = "data_access"          # 数据访问
    DATA_MODIFICATION = "data_modification"  # 数据修改
    SECURITY_VIOLATION = "security_violation"  # 安全违规
    SUSPICIOUS_ACTIVITY = "suspicious_activity"  # 可疑活动


@dataclass
class User:
    """用户信息"""
    id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = None
    permissions: List[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.permissions is None:
            self.permissions = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Role:
    """角色信息"""
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Permission:
    """权限信息"""
    id: str
    name: str
    resource: str
    action: str
    level: PermissionLevel
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}


@dataclass
class AuthenticationResult:
    """身份验证结果"""
    success: bool
    user: Optional[User] = None
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    requires_two_factor: bool = False
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SecurityEvent:
    """安全事件"""
    id: str
    event_type: SecurityEventType
    user_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = "info"

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


class IAuthenticationService(ABC):
    """身份验证服务接口"""
    
    @abstractmethod
    async def authenticate(self, 
                          username: str, 
                          password: str, 
                          method: AuthenticationMethod = AuthenticationMethod.PASSWORD) -> AuthenticationResult:
        """身份验证
        
        Args:
            username: 用户名
            password: 密码
            method: 验证方法
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    async def authenticate_token(self, token: str) -> AuthenticationResult:
        """令牌验证
        
        Args:
            token: 访问令牌
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthenticationResult:
        """刷新令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的验证结果
        """
        pass
    
    @abstractmethod
    async def logout(self, token: str) -> bool:
        """登出
        
        Args:
            token: 访问令牌
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> bool:
        """验证令牌有效性
        
        Args:
            token: 访问令牌
            
        Returns:
            是否有效
        """
        pass
    
    @abstractmethod
    async def get_user_from_token(self, token: str) -> Optional[User]:
        """从令牌获取用户信息
        
        Args:
            token: 访问令牌
            
        Returns:
            用户信息
        """
        pass
    
    @abstractmethod
    async def enable_two_factor(self, user_id: str) -> Dict[str, Any]:
        """启用双因素验证
        
        Args:
            user_id: 用户ID
            
        Returns:
            双因素验证配置信息
        """
        pass
    
    @abstractmethod
    async def verify_two_factor(self, user_id: str, code: str) -> bool:
        """验证双因素验证码
        
        Args:
            user_id: 用户ID
            code: 验证码
            
        Returns:
            是否验证成功
        """
        pass


class IAuthorizationService(ABC):
    """授权服务接口"""
    
    @abstractmethod
    async def check_permission(self, 
                              user_id: str, 
                              resource: str, 
                              action: str) -> bool:
        """检查权限
        
        Args:
            user_id: 用户ID
            resource: 资源
            action: 操作
            
        Returns:
            是否有权限
        """
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """获取用户权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限列表
        """
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: str) -> List[Role]:
        """获取用户角色
        
        Args:
            user_id: 用户ID
            
        Returns:
            角色列表
        """
        pass
    
    @abstractmethod
    async def assign_role(self, user_id: str, role_id: str) -> bool:
        """分配角色
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def revoke_role(self, user_id: str, role_id: str) -> bool:
        """撤销角色
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def grant_permission(self, user_id: str, permission_id: str) -> bool:
        """授予权限
        
        Args:
            user_id: 用户ID
            permission_id: 权限ID
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def revoke_permission(self, user_id: str, permission_id: str) -> bool:
        """撤销权限
        
        Args:
            user_id: 用户ID
            permission_id: 权限ID
            
        Returns:
            是否成功
        """
        pass


class IEncryptionService(ABC):
    """加密服务接口"""
    
    @abstractmethod
    async def encrypt(self, 
                     data: Union[str, bytes], 
                     algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256,
                     key: Optional[str] = None) -> bytes:
        """加密数据
        
        Args:
            data: 要加密的数据
            algorithm: 加密算法
            key: 加密密钥
            
        Returns:
            加密后的数据
        """
        pass
    
    @abstractmethod
    async def decrypt(self, 
                     encrypted_data: bytes, 
                     algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256,
                     key: Optional[str] = None) -> Union[str, bytes]:
        """解密数据
        
        Args:
            encrypted_data: 加密的数据
            algorithm: 加密算法
            key: 解密密钥
            
        Returns:
            解密后的数据
        """
        pass
    
    @abstractmethod
    async def hash_password(self, 
                           password: str, 
                           algorithm: HashAlgorithm = HashAlgorithm.BCRYPT) -> str:
        """哈希密码
        
        Args:
            password: 明文密码
            algorithm: 哈希算法
            
        Returns:
            哈希后的密码
        """
        pass
    
    @abstractmethod
    async def verify_password(self, 
                             password: str, 
                             hashed_password: str, 
                             algorithm: HashAlgorithm = HashAlgorithm.BCRYPT) -> bool:
        """验证密码
        
        Args:
            password: 明文密码
            hashed_password: 哈希密码
            algorithm: 哈希算法
            
        Returns:
            是否匹配
        """
        pass
    
    @abstractmethod
    async def generate_key(self, algorithm: EncryptionAlgorithm) -> str:
        """生成密钥
        
        Args:
            algorithm: 加密算法
            
        Returns:
            生成的密钥
        """
        pass
    
    @abstractmethod
    async def generate_salt(self, length: int = 32) -> str:
        """生成盐值
        
        Args:
            length: 盐值长度
            
        Returns:
            生成的盐值
        """
        pass


class ISecurityAuditService(ABC):
    """安全审计服务接口"""
    
    @abstractmethod
    async def log_security_event(self, event: SecurityEvent) -> None:
        """记录安全事件
        
        Args:
            event: 安全事件
        """
        pass
    
    @abstractmethod
    async def get_security_events(self, 
                                 user_id: Optional[str] = None,
                                 event_type: Optional[SecurityEventType] = None,
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None,
                                 limit: int = 100) -> List[SecurityEvent]:
        """获取安全事件
        
        Args:
            user_id: 用户ID
            event_type: 事件类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            安全事件列表
        """
        pass
    
    @abstractmethod
    async def detect_suspicious_activity(self, user_id: str) -> List[SecurityEvent]:
        """检测可疑活动
        
        Args:
            user_id: 用户ID
            
        Returns:
            可疑活动列表
        """
        pass
    
    @abstractmethod
    async def generate_security_report(self, 
                                      start_time: datetime,
                                      end_time: datetime) -> Dict[str, Any]:
        """生成安全报告
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            安全报告
        """
        pass
    
    @abstractmethod
    async def get_failed_login_attempts(self, 
                                       user_id: Optional[str] = None,
                                       ip_address: Optional[str] = None,
                                       time_window: timedelta = timedelta(hours=1)) -> int:
        """获取失败登录尝试次数
        
        Args:
            user_id: 用户ID
            ip_address: IP地址
            time_window: 时间窗口
            
        Returns:
            失败次数
        """
        pass
    
    @abstractmethod
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """检查IP是否被阻止
        
        Args:
            ip_address: IP地址
            
        Returns:
            是否被阻止
        """
        pass
    
    @abstractmethod
    async def block_ip(self, ip_address: str, duration: Optional[timedelta] = None) -> None:
        """阻止IP
        
        Args:
            ip_address: IP地址
            duration: 阻止时长
        """
        pass
    
    @abstractmethod
    async def unblock_ip(self, ip_address: str) -> None:
        """解除IP阻止
        
        Args:
            ip_address: IP地址
        """
        pass


class ISecurityConfigService(ABC):
    """安全配置服务接口"""
    
    @abstractmethod
    async def get_password_policy(self) -> Dict[str, Any]:
        """获取密码策略
        
        Returns:
            密码策略配置
        """
        pass
    
    @abstractmethod
    async def set_password_policy(self, policy: Dict[str, Any]) -> None:
        """设置密码策略
        
        Args:
            policy: 密码策略配置
        """
        pass
    
    @abstractmethod
    async def get_session_config(self) -> Dict[str, Any]:
        """获取会话配置
        
        Returns:
            会话配置
        """
        pass
    
    @abstractmethod
    async def set_session_config(self, config: Dict[str, Any]) -> None:
        """设置会话配置
        
        Args:
            config: 会话配置
        """
        pass
    
    @abstractmethod
    async def get_security_headers(self) -> Dict[str, str]:
        """获取安全头
        
        Returns:
            安全头配置
        """
        pass
    
    @abstractmethod
    async def set_security_headers(self, headers: Dict[str, str]) -> None:
        """设置安全头
        
        Args:
            headers: 安全头配置
        """
        pass
    
    @abstractmethod
    async def validate_password(self, password: str) -> Dict[str, Any]:
        """验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            验证结果
        """
        pass


# 异常类
class SecurityException(Exception):
    """安全异常基类"""
    pass


class AuthenticationException(SecurityException):
    """身份验证异常"""
    pass


class AuthorizationException(SecurityException):
    """授权异常"""
    pass


class EncryptionException(SecurityException):
    """加密异常"""
    pass


class TokenExpiredException(AuthenticationException):
    """令牌过期异常"""
    pass


class InvalidTokenException(AuthenticationException):
    """无效令牌异常"""
    pass


class PermissionDeniedException(AuthorizationException):
    """权限拒绝异常"""
    pass


class TwoFactorRequiredException(AuthenticationException):
    """需要双因素验证异常"""
    pass