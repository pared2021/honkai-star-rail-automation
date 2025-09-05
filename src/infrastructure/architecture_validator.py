"""架构验证工具

用于验证项目架构的一致性和合规性。
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """违规类型"""
    CIRCULAR_DEPENDENCY = "circular_dependency"
    LAYER_VIOLATION = "layer_violation"
    NAMING_CONVENTION = "naming_convention"
    INTERFACE_VIOLATION = "interface_violation"
    DEPENDENCY_RULE = "dependency_rule"
    SOLID_PRINCIPLE = "solid_principle"
    ARCHITECTURE_PATTERN = "architecture_pattern"


@dataclass
class ArchitectureViolation:
    """架构违规信息"""
    type: ViolationType
    severity: str  # "error", "warning", "info"
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class LayerDefinition:
    """层定义"""
    name: str
    path_patterns: List[str]
    allowed_dependencies: List[str]
    forbidden_dependencies: List[str]
    interfaces_required: bool = False


class ArchitectureValidator:
    """架构验证器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.violations: List[ArchitectureViolation] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # 定义分层架构
        self.layers = {
            "presentation": LayerDefinition(
                name="presentation",
                path_patterns=["ui/*", "gui/*"],
                allowed_dependencies=["application", "domain"],
                forbidden_dependencies=["infrastructure"],
                interfaces_required=True
            ),
            "application": LayerDefinition(
                name="application",
                path_patterns=["application/*", "services/*"],
                allowed_dependencies=["domain", "infrastructure"],
                forbidden_dependencies=["presentation"],
                interfaces_required=True
            ),
            "domain": LayerDefinition(
                name="domain",
                path_patterns=["domain/*", "models/*", "entities/*"],
                allowed_dependencies=[],
                forbidden_dependencies=["application", "infrastructure", "presentation"],
                interfaces_required=False
            ),
            "infrastructure": LayerDefinition(
                name="infrastructure",
                path_patterns=["infrastructure/*"],
                allowed_dependencies=["domain"],
                forbidden_dependencies=["application", "presentation"],
                interfaces_required=True
            ),
            "interfaces": LayerDefinition(
                name="interfaces",
                path_patterns=["interfaces/*"],
                allowed_dependencies=[],
                forbidden_dependencies=["*"],
                interfaces_required=False
            )
        }
    
    def validate(self) -> Dict[str, Any]:
        """执行完整的架构验证
        
        Returns:
            验证结果
        """
        self.violations.clear()
        self.dependency_graph.clear()
        
        # 构建依赖图
        self._build_dependency_graph()
        
        # 执行各种验证
        self._validate_circular_dependencies()
        self._validate_layer_dependencies()
        self._validate_naming_conventions()
        self._validate_interface_usage()
        self._validate_solid_principles()
        self._validate_mvp_pattern()
        
        # 计算一致性分数
        consistency_score = self._calculate_consistency_score()
        
        return {
            "consistency_score": consistency_score,
            "violations": [{
                "type": v.type.value,
                "severity": v.severity,
                "message": v.message,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "suggestion": v.suggestion
            } for v in self.violations],
            "total_violations": len(self.violations),
            "error_count": len([v for v in self.violations if v.severity == "error"]),
            "warning_count": len([v for v in self.violations if v.severity == "warning"]),
            "dependency_graph": {k: list(v) for k, v in self.dependency_graph.items()}
        }
    
    def _build_dependency_graph(self) -> None:
        """构建依赖关系图"""
        src_path = self.project_root / "src"
        if not src_path.exists():
            return
        
        for py_file in src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_key = str(py_file.relative_to(self.project_root))
                dependencies = set()
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dependencies.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies.add(node.module)
                
                self.dependency_graph[file_key] = dependencies
                
            except Exception as e:
                self._add_violation(
                    ViolationType.ARCHITECTURE_PATTERN,
                    "error",
                    f"无法解析文件: {e}",
                    str(py_file.relative_to(self.project_root))
                )
    
    def _validate_circular_dependencies(self) -> None:
        """检查循环依赖"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                self._add_violation(
                    ViolationType.CIRCULAR_DEPENDENCY,
                    "error",
                    f"检测到循环依赖: {' -> '.join(cycle)}",
                    node,
                    suggestion="重构代码以消除循环依赖，考虑使用依赖注入或事件驱动架构"
                )
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for dependency in self.dependency_graph.get(node, set()):
                # 只检查项目内部的依赖
                if any(dependency.startswith(prefix) for prefix in ['src.', '.']):
                    if has_cycle(dependency, path + [node]):
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.dependency_graph:
            if node not in visited:
                has_cycle(node, [])
    
    def _validate_layer_dependencies(self) -> None:
        """验证分层架构依赖规则"""
        for file_path, dependencies in self.dependency_graph.items():
            file_layer = self._get_file_layer(file_path)
            if not file_layer:
                continue
            
            layer_def = self.layers[file_layer]
            
            for dependency in dependencies:
                if not dependency.startswith('src.'):
                    continue
                
                dep_layer = self._get_dependency_layer(dependency)
                if not dep_layer:
                    continue
                
                # 检查是否违反了依赖规则
                if dep_layer in layer_def.forbidden_dependencies:
                    self._add_violation(
                        ViolationType.LAYER_VIOLATION,
                        "error",
                        f"{file_layer}层不应依赖{dep_layer}层",
                        file_path,
                        suggestion=f"移除对{dep_layer}层的直接依赖，使用接口或事件进行解耦"
                    )
                elif (layer_def.allowed_dependencies and 
                      dep_layer not in layer_def.allowed_dependencies):
                    self._add_violation(
                        ViolationType.LAYER_VIOLATION,
                        "warning",
                        f"{file_layer}层对{dep_layer}层的依赖可能不合适",
                        file_path,
                        suggestion="检查依赖关系是否符合分层架构原则"
                    )
    
    def _validate_naming_conventions(self) -> None:
        """验证命名约定"""
        src_path = self.project_root / "src"
        if not src_path.exists():
            return
        
        # 检查接口命名
        interfaces_path = src_path / "interfaces"
        if interfaces_path.exists():
            for py_file in interfaces_path.rglob("*.py"):
                if py_file.name == "__init__.py" or py_file.name.endswith("_types.py"):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # 检查是否是真正的接口类（继承自ABC或有abstractmethod装饰器）
                            is_interface = self._is_interface_class(node)
                            if is_interface and not node.name.startswith('I'):
                                self._add_violation(
                                    ViolationType.NAMING_CONVENTION,
                                    "warning",
                                    f"接口类 {node.name} 应以 'I' 开头",
                                    str(py_file.relative_to(self.project_root)),
                                    node.lineno,
                                    f"将类名改为 I{node.name}"
                                )
                except Exception:
                    pass
        
        # 检查MVP模式命名
        ui_path = src_path / "ui"
        if ui_path.exists():
            for py_file in ui_path.rglob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                file_name = py_file.stem
                if not any(suffix in file_name for suffix in ['_view', '_presenter', '_model']):
                    self._add_violation(
                        ViolationType.NAMING_CONVENTION,
                        "info",
                        f"UI文件 {file_name} 建议使用MVP命名约定",
                        str(py_file.relative_to(self.project_root)),
                        suggestion="文件名应包含 _view、_presenter 或 _model 后缀"
                    )
    
    def _validate_interface_usage(self) -> None:
        """验证接口使用"""
        for file_path, dependencies in self.dependency_graph.items():
            file_layer = self._get_file_layer(file_path)
            if not file_layer:
                continue
            
            layer_def = self.layers[file_layer]
            if not layer_def.interfaces_required:
                continue
            
            # 检查是否使用了接口
            has_interface_import = any(
                'interfaces' in dep for dep in dependencies
            )
            
            if not has_interface_import:
                self._add_violation(
                    ViolationType.INTERFACE_VIOLATION,
                    "warning",
                    f"{file_layer}层应使用接口进行解耦",
                    file_path,
                    suggestion="引入相应的接口定义，避免直接依赖具体实现"
                )
    
    def _validate_solid_principles(self) -> None:
        """验证SOLID原则"""
        src_path = self.project_root / "src"
        if not src_path.exists():
            return
        
        for py_file in src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查文件长度（单一职责原则）
                lines = content.split('\n')
                if len(lines) > 500:
                    self._add_violation(
                        ViolationType.SOLID_PRINCIPLE,
                        "warning",
                        f"文件过长({len(lines)}行)，可能违反单一职责原则",
                        str(py_file.relative_to(self.project_root)),
                        suggestion="考虑将文件拆分为多个更小的模块"
                    )
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 检查类的方法数量
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        if len(methods) > 20:
                            self._add_violation(
                                ViolationType.SOLID_PRINCIPLE,
                                "warning",
                                f"类 {node.name} 有太多方法({len(methods)})，可能违反单一职责原则",
                                str(py_file.relative_to(self.project_root)),
                                node.lineno,
                                "考虑将类拆分为多个更小的类"
                            )
                    
                    elif isinstance(node, ast.FunctionDef):
                        # 检查函数长度
                        if hasattr(node, 'end_lineno') and node.end_lineno:
                            func_length = node.end_lineno - node.lineno
                            if func_length > 50:
                                self._add_violation(
                                    ViolationType.SOLID_PRINCIPLE,
                                    "info",
                                    f"函数 {node.name} 过长({func_length}行)",
                                    str(py_file.relative_to(self.project_root)),
                                    node.lineno,
                                    "考虑将函数拆分为多个更小的函数"
                                )
            except Exception:
                pass
    
    def _validate_mvp_pattern(self) -> None:
        """验证MVP模式"""
        ui_path = self.project_root / "src" / "ui"
        if not ui_path.exists():
            return
        
        for component_dir in ui_path.iterdir():
            if not component_dir.is_dir() or component_dir.name.startswith('.'):
                continue
            
            # 检查MVP三元组
            has_view = any(f.name.endswith('_view.py') for f in component_dir.glob('*.py'))
            has_presenter = any(f.name.endswith('_presenter.py') for f in component_dir.glob('*.py'))
            has_model = any(f.name.endswith('_model.py') for f in component_dir.glob('*.py'))
            
            if not (has_view and has_presenter):
                self._add_violation(
                    ViolationType.ARCHITECTURE_PATTERN,
                    "warning",
                    f"UI组件 {component_dir.name} 缺少完整的MVP结构",
                    str(component_dir.relative_to(self.project_root)),
                    suggestion="确保每个UI组件都有对应的View和Presenter"
                )
    
    def _get_file_layer(self, file_path: str) -> Optional[str]:
        """获取文件所属的层"""
        for layer_name, layer_def in self.layers.items():
            for pattern in layer_def.path_patterns:
                if self._match_pattern(file_path, pattern):
                    return layer_name
        return None
    
    def _get_dependency_layer(self, dependency: str) -> Optional[str]:
        """获取依赖所属的层"""
        # 简化的依赖层判断
        if 'ui' in dependency or 'gui' in dependency:
            return 'presentation'
        elif 'application' in dependency or 'services' in dependency:
            return 'application'
        elif 'domain' in dependency or 'models' in dependency:
            return 'domain'
        elif 'infrastructure' in dependency:
            return 'infrastructure'
        elif 'interfaces' in dependency:
            return 'interfaces'
        return None
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """匹配路径模式"""
        # 简单的通配符匹配
        pattern = pattern.replace('*', '.*')
        return bool(re.match(pattern, path))
    
    def _is_interface_class(self, node: ast.ClassDef) -> bool:
        """判断是否是接口类"""
        # 检查是否继承自ABC
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'ABC':
                return True
            elif isinstance(base, ast.Attribute) and base.attr == 'ABC':
                return True
        
        # 检查是否有abstractmethod装饰器
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                        return True
                    elif isinstance(decorator, ast.Attribute) and decorator.attr == 'abstractmethod':
                        return True
        
        return False
    
    def _add_violation(self, 
                      violation_type: ViolationType, 
                      severity: str, 
                      message: str, 
                      file_path: str, 
                      line_number: Optional[int] = None, 
                      suggestion: Optional[str] = None) -> None:
        """添加违规记录"""
        self.violations.append(ArchitectureViolation(
            type=violation_type,
            severity=severity,
            message=message,
            file_path=file_path,
            line_number=line_number,
            suggestion=suggestion
        ))
    
    def _calculate_consistency_score(self) -> float:
        """计算架构一致性分数"""
        if not self.violations:
            return 100.0
        
        # 根据违规类型和严重程度计算扣分
        total_deduction = 0
        for violation in self.violations:
            if violation.severity == "error":
                deduction = 10
            elif violation.severity == "warning":
                deduction = 5
            else:  # info
                deduction = 1
            
            # 某些违规类型扣分更多
            if violation.type in [ViolationType.CIRCULAR_DEPENDENCY, ViolationType.LAYER_VIOLATION]:
                deduction *= 2
            
            total_deduction += deduction
        
        # 计算最终分数
        score = max(0, 100 - total_deduction)
        return round(score, 2)
    
    def generate_report(self) -> str:
        """生成验证报告"""
        result = self.validate()
        
        report = []
        report.append("# 架构验证报告\n")
        report.append(f"**一致性分数**: {result['consistency_score']}%\n")
        report.append(f"**总违规数**: {result['total_violations']}")
        report.append(f"**错误**: {result['error_count']}")
        report.append(f"**警告**: {result['warning_count']}\n")
        
        if result['violations']:
            report.append("## 违规详情\n")
            
            # 按类型分组
            violations_by_type = {}
            for violation in result['violations']:
                vtype = violation['type']
                if vtype not in violations_by_type:
                    violations_by_type[vtype] = []
                violations_by_type[vtype].append(violation)
            
            for vtype, violations in violations_by_type.items():
                report.append(f"### {vtype.replace('_', ' ').title()}\n")
                for violation in violations:
                    report.append(f"- **{violation['severity'].upper()}**: {violation['message']}")
                    report.append(f"  - 文件: {violation['file_path']}")
                    if violation['line_number']:
                        report.append(f"  - 行号: {violation['line_number']}")
                    if violation['suggestion']:
                        report.append(f"  - 建议: {violation['suggestion']}")
                    report.append("")
        
        return "\n".join(report)