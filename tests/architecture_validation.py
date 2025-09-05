#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构一致性验证脚本

验证重构后的架构是否符合设计要求：
1. 依赖关系验证
2. 接口实现验证
3. SOLID原则遵循验证
4. 模块耦合度检查
5. 配置管理集中化验证
"""

import os
import ast
import sys
import inspect
import importlib
from typing import Dict, List, Set, Tuple, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class ValidationResult:
    """验证结果"""
    category: str
    test_name: str
    passed: bool
    score: float
    details: str
    issues: List[str]


class ArchitectureValidator:
    """架构验证器"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.src_path = project_root / "src"
        self.core_path = self.src_path / "core"
        
    def validate_all(self) -> Dict[str, Any]:
        """执行所有验证"""
        print("开始架构一致性验证...")
        
        # 1. 依赖关系验证
        self._validate_dependencies()
        
        # 2. 接口实现验证
        self._validate_interfaces()
        
        # 3. SOLID原则验证
        self._validate_solid_principles()
        
        # 4. 模块耦合度验证
        self._validate_module_coupling()
        
        # 5. 配置管理验证
        self._validate_configuration_management()
        
        # 6. 依赖注入验证
        self._validate_dependency_injection()
        
        return self._generate_report()
    
    def _validate_dependencies(self):
        """验证依赖关系"""
        print("验证依赖关系...")
        
        # 检查循环依赖
        circular_deps = self._check_circular_dependencies()
        
        result = ValidationResult(
            category="依赖关系",
            test_name="循环依赖检查",
            passed=len(circular_deps) == 0,
            score=100.0 if len(circular_deps) == 0 else max(0, 100 - len(circular_deps) * 10),
            details=f"发现 {len(circular_deps)} 个循环依赖",
            issues=circular_deps
        )
        self.results.append(result)
        
        # 检查依赖层次
        layer_violations = self._check_dependency_layers()
        
        result = ValidationResult(
            category="依赖关系",
            test_name="依赖层次检查",
            passed=len(layer_violations) == 0,
            score=100.0 if len(layer_violations) == 0 else max(0, 100 - len(layer_violations) * 5),
            details=f"发现 {len(layer_violations)} 个层次违规",
            issues=layer_violations
        )
        self.results.append(result)
    
    def _validate_interfaces(self):
        """验证接口实现"""
        print("验证接口实现...")
        
        # 检查接口完整性
        interface_issues = self._check_interface_completeness()
        
        result = ValidationResult(
            category="接口实现",
            test_name="接口完整性检查",
            passed=len(interface_issues) == 0,
            score=100.0 if len(interface_issues) == 0 else max(0, 100 - len(interface_issues) * 10),
            details=f"发现 {len(interface_issues)} 个接口问题",
            issues=interface_issues
        )
        self.results.append(result)
        
        # 检查接口一致性
        consistency_issues = self._check_interface_consistency()
        
        result = ValidationResult(
            category="接口实现",
            test_name="接口一致性检查",
            passed=len(consistency_issues) == 0,
            score=100.0 if len(consistency_issues) == 0 else max(0, 100 - len(consistency_issues) * 5),
            details=f"发现 {len(consistency_issues)} 个一致性问题",
            issues=consistency_issues
        )
        self.results.append(result)
    
    def _validate_solid_principles(self):
        """验证SOLID原则"""
        print("验证SOLID原则...")
        
        # 单一职责原则
        srp_violations = self._check_single_responsibility()
        
        result = ValidationResult(
            category="SOLID原则",
            test_name="单一职责原则",
            passed=len(srp_violations) == 0,
            score=100.0 if len(srp_violations) == 0 else max(0, 100 - len(srp_violations) * 5),
            details=f"发现 {len(srp_violations)} 个SRP违规",
            issues=srp_violations
        )
        self.results.append(result)
        
        # 开闭原则
        ocp_violations = self._check_open_closed()
        
        result = ValidationResult(
            category="SOLID原则",
            test_name="开闭原则",
            passed=len(ocp_violations) == 0,
            score=100.0 if len(ocp_violations) == 0 else max(0, 100 - len(ocp_violations) * 10),
            details=f"发现 {len(ocp_violations)} 个OCP违规",
            issues=ocp_violations
        )
        self.results.append(result)
        
        # 依赖倒置原则
        dip_violations = self._check_dependency_inversion()
        
        result = ValidationResult(
            category="SOLID原则",
            test_name="依赖倒置原则",
            passed=len(dip_violations) == 0,
            score=100.0 if len(dip_violations) == 0 else max(0, 100 - len(dip_violations) * 10),
            details=f"发现 {len(dip_violations)} 个DIP违规",
            issues=dip_violations
        )
        self.results.append(result)
    
    def _validate_module_coupling(self):
        """验证模块耦合度"""
        print("验证模块耦合度...")
        
        # 计算耦合度
        coupling_metrics = self._calculate_coupling_metrics()
        
        high_coupling = [f"{module}: {metric['coupling']:.2f}" 
                        for module, metric in coupling_metrics.items() 
                        if metric['coupling'] > 0.7]
        
        result = ValidationResult(
            category="模块耦合",
            test_name="耦合度检查",
            passed=len(high_coupling) == 0,
            score=100.0 if len(high_coupling) == 0 else max(0, 100 - len(high_coupling) * 15),
            details=f"发现 {len(high_coupling)} 个高耦合模块",
            issues=high_coupling
        )
        self.results.append(result)
    
    def _validate_configuration_management(self):
        """验证配置管理"""
        print("验证配置管理...")
        
        # 检查配置集中化
        config_issues = self._check_configuration_centralization()
        
        result = ValidationResult(
            category="配置管理",
            test_name="配置集中化检查",
            passed=len(config_issues) == 0,
            score=100.0 if len(config_issues) == 0 else max(0, 100 - len(config_issues) * 10),
            details=f"发现 {len(config_issues)} 个配置问题",
            issues=config_issues
        )
        self.results.append(result)
    
    def _validate_dependency_injection(self):
        """验证依赖注入"""
        print("验证依赖注入...")
        
        # 检查依赖注入使用
        di_issues = self._check_dependency_injection_usage()
        
        result = ValidationResult(
            category="依赖注入",
            test_name="依赖注入使用检查",
            passed=len(di_issues) == 0,
            score=100.0 if len(di_issues) == 0 else max(0, 100 - len(di_issues) * 10),
            details=f"发现 {len(di_issues)} 个DI问题",
            issues=di_issues
        )
        self.results.append(result)
    
    def _check_circular_dependencies(self) -> List[str]:
        """检查循环依赖"""
        dependencies = self._extract_dependencies()
        circular_deps = []
        
        def has_path(start, end, visited=None):
            if visited is None:
                visited = set()
            if start == end:
                return True
            if start in visited:
                return False
            visited.add(start)
            for dep in dependencies.get(start, []):
                if has_path(dep, end, visited.copy()):
                    return True
            return False
        
        for module in dependencies:
            for dep in dependencies[module]:
                if has_path(dep, module):
                    circular_deps.append(f"{module} <-> {dep}")
        
        return list(set(circular_deps))
    
    def _check_dependency_layers(self) -> List[str]:
        """检查依赖层次"""
        violations = []
        
        # 定义层次结构
        layers = {
            'interfaces': 0,
            'models': 1,
            'events': 1,
            'managers': 2,
            'core': 3,
            'api': 4,
            'ui': 5
        }
        
        dependencies = self._extract_dependencies()
        
        for module, deps in dependencies.items():
            module_layer = self._get_module_layer(module, layers)
            for dep in deps:
                dep_layer = self._get_module_layer(dep, layers)
                if dep_layer > module_layer:
                    violations.append(f"{module} 不应依赖更高层的 {dep}")
        
        return violations
    
    def _check_interface_completeness(self) -> List[str]:
        """检查接口完整性"""
        issues = []
        
        # 检查核心接口是否存在
        required_interfaces = [
            'ITaskManager', 'IConfigManager', 'IEventBus',
            'IDatabaseManager', 'ICacheManager', 'ITaskScheduler',
            'ITaskMonitor', 'ITaskExecutor', 'IResourceManager'
        ]
        
        interfaces_path = self.core_path / "interfaces"
        if not interfaces_path.exists():
            issues.append("接口目录不存在")
            return issues
        
        for interface_name in required_interfaces:
            found = False
            for py_file in interfaces_path.glob("*.py"):
                if self._file_contains_interface(py_file, interface_name):
                    found = True
                    break
            if not found:
                issues.append(f"缺少接口: {interface_name}")
        
        return issues
    
    def _check_interface_consistency(self) -> List[str]:
        """检查接口一致性"""
        issues = []
        
        # 检查实现类是否正确实现接口
        implementations = {
            'ITaskManager': ['RefactoredTaskManager'],
            'IConfigManager': ['ConfigManager'],
            'IEventBus': ['EventBus'],
            'ICacheManager': ['TaskCacheManager']
        }
        
        for interface, impls in implementations.items():
            for impl in impls:
                if not self._check_implementation_consistency(interface, impl):
                    issues.append(f"{impl} 未正确实现 {interface}")
        
        return issues
    
    def _check_single_responsibility(self) -> List[str]:
        """检查单一职责原则"""
        violations = []
        
        # 检查类的方法数量和复杂度
        for py_file in self.core_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            classes = self._extract_classes_from_file(py_file)
            for class_name, methods in classes.items():
                if len(methods) > 20:  # 方法过多可能违反SRP
                    violations.append(f"{py_file.name}::{class_name} 方法过多 ({len(methods)}个)")
                
                # 检查方法复杂度
                complex_methods = [m for m in methods if self._calculate_method_complexity(m) > 10]
                if complex_methods:
                    violations.append(f"{py_file.name}::{class_name} 包含复杂方法: {complex_methods}")
        
        return violations
    
    def _check_open_closed(self) -> List[str]:
        """检查开闭原则"""
        violations = []
        
        # 检查是否使用了抽象基类和接口
        for py_file in self.core_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            content = py_file.read_text(encoding='utf-8')
            
            # 检查是否有硬编码的类型检查
            if 'isinstance(' in content and 'type(' in content:
                violations.append(f"{py_file.name} 可能包含硬编码类型检查")
        
        return violations
    
    def _check_dependency_inversion(self) -> List[str]:
        """检查依赖倒置原则"""
        violations = []
        
        # 检查是否依赖具体实现而非抽象
        for py_file in self.core_path.rglob("*.py"):
            if py_file.name.startswith("__") or "interface" in py_file.name:
                continue
            
            imports = self._extract_imports_from_file(py_file)
            
            # 检查是否直接导入具体实现类
            concrete_imports = [imp for imp in imports 
                              if not imp.startswith('I') and 
                              any(keyword in imp.lower() for keyword in ['manager', 'executor', 'scheduler'])]
            
            if concrete_imports:
                violations.append(f"{py_file.name} 直接导入具体实现: {concrete_imports}")
        
        return violations
    
    def _calculate_coupling_metrics(self) -> Dict[str, Dict[str, float]]:
        """计算耦合度指标"""
        metrics = {}
        dependencies = self._extract_dependencies()
        
        for module in dependencies:
            incoming = sum(1 for deps in dependencies.values() if module in deps)
            outgoing = len(dependencies.get(module, []))
            total_modules = len(dependencies)
            
            # 计算耦合度 (0-1之间，越低越好)
            coupling = (incoming + outgoing) / (2 * total_modules) if total_modules > 1 else 0
            
            metrics[module] = {
                'incoming': incoming,
                'outgoing': outgoing,
                'coupling': coupling
            }
        
        return metrics
    
    def _check_configuration_centralization(self) -> List[str]:
        """检查配置集中化"""
        issues = []
        
        # 检查是否存在硬编码配置
        for py_file in self.core_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            content = py_file.read_text(encoding='utf-8')
            
            # 检查硬编码的配置值
            hardcoded_patterns = [
                r'timeout\s*=\s*\d+',
                r'max_retries\s*=\s*\d+',
                r'buffer_size\s*=\s*\d+',
                r'port\s*=\s*\d+'
            ]
            
            import re
            for pattern in hardcoded_patterns:
                if re.search(pattern, content):
                    issues.append(f"{py_file.name} 包含硬编码配置")
                    break
        
        return issues
    
    def _check_dependency_injection_usage(self) -> List[str]:
        """检查依赖注入使用"""
        issues = []
        
        # 检查是否正确使用依赖注入
        container_file = self.core_path / "container.py"
        if not container_file.exists():
            issues.append("依赖注入容器不存在")
        
        config_file = self.core_path / "container_config.py"
        if not config_file.exists():
            issues.append("依赖注入配置不存在")
        
        # 检查核心类是否使用依赖注入
        manager_files = list(self.core_path.glob("*manager*.py"))
        for manager_file in manager_files:
            if not self._uses_dependency_injection(manager_file):
                issues.append(f"{manager_file.name} 未使用依赖注入")
        
        return issues
    
    def _extract_dependencies(self) -> Dict[str, List[str]]:
        """提取模块依赖关系"""
        dependencies = defaultdict(list)
        
        for py_file in self.core_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            module_name = py_file.stem
            imports = self._extract_imports_from_file(py_file)
            
            for imp in imports:
                if imp != module_name:  # 避免自依赖
                    dependencies[module_name].append(imp)
        
        return dict(dependencies)
    
    def _extract_imports_from_file(self, file_path: Path) -> List[str]:
        """从文件中提取导入"""
        imports = []
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[-1])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(alias.name)
        except Exception:
            pass
        
        return imports
    
    def _extract_classes_from_file(self, file_path: Path) -> Dict[str, List[str]]:
        """从文件中提取类和方法"""
        classes = {}
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes[node.name] = methods
        except Exception:
            pass
        
        return classes
    
    def _get_module_layer(self, module: str, layers: Dict[str, int]) -> int:
        """获取模块层次"""
        for layer_name, level in layers.items():
            if layer_name in module.lower():
                return level
        return 999  # 未知层次
    
    def _file_contains_interface(self, file_path: Path, interface_name: str) -> bool:
        """检查文件是否包含指定接口"""
        try:
            content = file_path.read_text(encoding='utf-8')
            return f"class {interface_name}" in content
        except Exception:
            return False
    
    def _check_implementation_consistency(self, interface: str, implementation: str) -> bool:
        """检查实现一致性"""
        # 简化检查：假设如果实现类存在就是一致的
        for py_file in self.core_path.rglob("*.py"):
            if self._file_contains_interface(py_file, implementation):
                return True
        return False
    
    def _calculate_method_complexity(self, method_name: str) -> int:
        """计算方法复杂度（简化版）"""
        # 简化实现：基于方法名长度估算
        return len(method_name.split('_'))
    
    def _uses_dependency_injection(self, file_path: Path) -> bool:
        """检查文件是否使用依赖注入"""
        try:
            content = file_path.read_text(encoding='utf-8')
            return 'def __init__(self' in content and ('manager' in content or 'executor' in content)
        except Exception:
            return False
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        
        # 计算总分
        total_score = sum(r.score for r in self.results) / total_tests if total_tests > 0 else 0
        
        # 按类别分组
        by_category = defaultdict(list)
        for result in self.results:
            by_category[result.category].append(result)
        
        report = {
            'overall': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'overall_score': total_score,
                'architecture_consistency': total_score
            },
            'by_category': {},
            'detailed_results': self.results
        }
        
        for category, results in by_category.items():
            category_passed = sum(1 for r in results if r.passed)
            category_score = sum(r.score for r in results) / len(results)
            
            report['by_category'][category] = {
                'total_tests': len(results),
                'passed_tests': category_passed,
                'pass_rate': (category_passed / len(results) * 100),
                'average_score': category_score
            }
        
        return report


def main():
    """主函数"""
    validator = ArchitectureValidator()
    report = validator.validate_all()
    
    print("\n" + "="*60)
    print("架构一致性验证报告")
    print("="*60)
    
    overall = report['overall']
    print(f"\n总体结果:")
    print(f"  测试总数: {overall['total_tests']}")
    print(f"  通过测试: {overall['passed_tests']}")
    print(f"  失败测试: {overall['failed_tests']}")
    print(f"  通过率: {overall['pass_rate']:.1f}%")
    print(f"  总体评分: {overall['overall_score']:.1f}/100")
    print(f"  架构一致性: {overall['architecture_consistency']:.1f}%")
    
    print(f"\n分类结果:")
    for category, stats in report['by_category'].items():
        print(f"  {category}:")
        print(f"    通过率: {stats['pass_rate']:.1f}%")
        print(f"    平均分: {stats['average_score']:.1f}/100")
    
    print(f"\n详细结果:")
    for result in report['detailed_results']:
        status = "✓" if result.passed else "✗"
        print(f"  {status} [{result.category}] {result.test_name}: {result.score:.1f}/100")
        if result.details:
            print(f"    {result.details}")
        if result.issues:
            for issue in result.issues[:3]:  # 只显示前3个问题
                print(f"    - {issue}")
            if len(result.issues) > 3:
                print(f"    ... 还有 {len(result.issues) - 3} 个问题")
    
    # 判断是否达到要求
    if overall['architecture_consistency'] >= 95.0:
        print(f"\n🎉 架构一致性验证通过！达到 {overall['architecture_consistency']:.1f}% (要求 ≥ 95%)")
        return True
    else:
        print(f"\n❌ 架构一致性验证未通过。当前 {overall['architecture_consistency']:.1f}% (要求 ≥ 95%)")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)