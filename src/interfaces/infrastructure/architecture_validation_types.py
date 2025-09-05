"""架构验证类型定义

定义架构验证相关的枚举、数据类和类型。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


class ValidationLevel(Enum):
    """验证级别"""
    ERROR = "error"      # 错误级别
    WARNING = "warning"  # 警告级别
    INFO = "info"        # 信息级别
    SUGGESTION = "suggestion"  # 建议级别


class ArchitectureLayer(Enum):
    """架构层级"""
    PRESENTATION = "presentation"    # 表示层
    APPLICATION = "application"      # 应用层
    DOMAIN = "domain"                # 领域层
    INFRASTRUCTURE = "infrastructure"  # 基础设施层
    SHARED = "shared"                # 共享层


class DependencyType(Enum):
    """依赖类型"""
    IMPORT = "import"        # 导入依赖
    INHERITANCE = "inheritance"  # 继承依赖
    COMPOSITION = "composition"  # 组合依赖
    AGGREGATION = "aggregation"  # 聚合依赖
    ASSOCIATION = "association"  # 关联依赖


@dataclass
class ValidationResult:
    """验证结果"""
    level: ValidationLevel
    message: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class DependencyInfo:
    """依赖信息"""
    source: str
    target: str
    dependency_type: DependencyType
    file_path: Path
    line_number: int
    is_circular: bool = False


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    path: Path
    layer: ArchitectureLayer
    dependencies: List[str]
    dependents: List[str]
    complexity: int
    lines_of_code: int


@dataclass
class ArchitectureMetrics:
    """架构指标"""
    consistency_score: float  # 一致性分数 (0-100)
    coupling_score: float     # 耦合度分数 (0-100)
    cohesion_score: float     # 内聚度分数 (0-100)
    complexity_score: float   # 复杂度分数 (0-100)
    maintainability_score: float  # 可维护性分数 (0-100)
    total_modules: int
    circular_dependencies: int
    layer_violations: int
    solid_violations: int