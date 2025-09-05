#!/usr/bin/env python3
"""架构验证脚本

用于验证项目架构的一致性和合规性。
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.architecture_validator import ArchitectureValidator


def main():
    """主函数"""
    print("开始架构验证...")
    print("=" * 50)
    
    # 创建验证器
    validator = ArchitectureValidator(project_root)
    
    # 执行验证
    result = validator.validate()
    
    # 显示结果
    print(f"\n架构一致性分数: {result['consistency_score']}%")
    print(f"总违规数: {result['total_violations']}")
    print(f"错误: {result['error_count']}")
    print(f"警告: {result['warning_count']}")
    
    if result['violations']:
        print("\n违规详情:")
        print("-" * 30)
        
        # 按严重程度分组显示
        errors = [v for v in result['violations'] if v['severity'] == 'error']
        warnings = [v for v in result['violations'] if v['severity'] == 'warning']
        infos = [v for v in result['violations'] if v['severity'] == 'info']
        
        if errors:
            print("\n🔴 错误:")
            for violation in errors:
                print(f"  - {violation['message']}")
                print(f"    文件: {violation['file_path']}")
                if violation['line_number']:
                    print(f"    行号: {violation['line_number']}")
                if violation['suggestion']:
                    print(f"    建议: {violation['suggestion']}")
                print()
        
        if warnings:
            print("\n🟡 警告:")
            for violation in warnings:
                print(f"  - {violation['message']}")
                print(f"    文件: {violation['file_path']}")
                if violation['line_number']:
                    print(f"    行号: {violation['line_number']}")
                if violation['suggestion']:
                    print(f"    建议: {violation['suggestion']}")
                print()
        
        if infos:
            print("\n🔵 信息:")
            for violation in infos:
                print(f"  - {violation['message']}")
                print(f"    文件: {violation['file_path']}")
                if violation['line_number']:
                    print(f"    行号: {violation['line_number']}")
                if violation['suggestion']:
                    print(f"    建议: {violation['suggestion']}")
                print()
    
    # 生成详细报告
    report = validator.generate_report()
    report_path = project_root / "architecture_validation_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n详细报告已保存到: {report_path}")
    
    # 保存JSON结果
    json_path = project_root / "architecture_validation_result.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"JSON结果已保存到: {json_path}")
    
    # 判断是否通过验证
    if result['consistency_score'] >= 95.0:
        print("\n✅ 架构验证通过！一致性分数达到95%以上")
        return 0
    else:
        print(f"\n❌ 架构验证未通过！一致性分数({result['consistency_score']}%)低于95%")
        print("请根据上述违规信息进行修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())