#!/usr/bin/env python3
"""
持续监控脚本
定期执行质量检查，生成趋势报告，并发送通知
"""

from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional

import yaml

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ContinuousMonitor:
    """持续监控管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.project_root = project_root
        self.config_path = (
            config_path or self.project_root / "config" / "monitoring.yml"
        )
        self.reports_dir = self.project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载监控配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ 配置文件未找到: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "monitoring": {
                "thresholds": {
                    "coverage_threshold": 80.0,
                    "pylint_threshold": 8.0,
                    "complexity_threshold": 10,
                    "duplicate_threshold": 0.8,
                },
                "reports": {
                    "format": ["json"],
                    "output_dir": "reports",
                    "retention_days": 30,
                },
            }
        }

    def run_quality_check(self) -> Dict:
        """运行质量检查"""
        print("🔍 开始质量检查...")

        # 运行质量门禁脚本
        quality_gate_script = self.project_root / "scripts" / "quality_gate.py"
        if quality_gate_script.exists():
            os.system(f"python {quality_gate_script}")

        # 读取质量报告
        report_path = self.reports_dir / "quality_gate.json"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return {}

    def generate_trend_report(self) -> Dict:
        """生成趋势报告"""
        print("📈 生成趋势报告...")

        # 收集历史报告
        history_reports = []
        for report_file in self.reports_dir.glob("quality_gate_*.json"):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)
                    history_reports.append(report)
            except Exception as e:
                print(f"⚠️ 读取历史报告失败: {report_file}, {e}")

        # 按时间排序
        history_reports.sort(key=lambda x: x.get("timestamp", ""))

        # 生成趋势数据
        trend_data = {
            "generated_at": datetime.now().isoformat(),
            "period_days": 30,
            "total_reports": len(history_reports),
            "trends": self._calculate_trends(history_reports),
        }

        # 保存趋势报告
        trend_report_path = (
            self.reports_dir / f"trend_report_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(trend_report_path, "w", encoding="utf-8") as f:
            json.dump(trend_data, f, indent=2, ensure_ascii=False)

        print(f"📊 趋势报告已保存: {trend_report_path}")
        return trend_data

    def _calculate_trends(self, reports: List[Dict]) -> Dict:
        """计算趋势数据"""
        if not reports:
            return {}

        trends = {
            "quality_score": [],
            "passed_checks": [],
            "failed_checks": [],
            "total_duration": [],
        }

        for report in reports[-30:]:  # 最近30个报告
            summary = report.get("summary", {})

            # 计算质量分数
            total_checks = summary.get("total_checks", 1)
            passed_checks = summary.get("passed", 0)
            quality_score = (
                (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            )

            trends["quality_score"].append(
                {"timestamp": report.get("timestamp"), "value": quality_score}
            )

            trends["passed_checks"].append(
                {"timestamp": report.get("timestamp"), "value": passed_checks}
            )

            trends["failed_checks"].append(
                {
                    "timestamp": report.get("timestamp"),
                    "value": summary.get("failed", 0),
                }
            )

            trends["total_duration"].append(
                {
                    "timestamp": report.get("timestamp"),
                    "value": summary.get("total_duration", 0),
                }
            )

        return trends

    def cleanup_old_reports(self):
        """清理旧报告"""
        retention_days = (
            self.config.get("monitoring", {})
            .get("reports", {})
            .get("retention_days", 30)
        )
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        cleaned_count = 0
        for report_file in self.reports_dir.glob("*.json"):
            if report_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    report_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    print(f"⚠️ 删除旧报告失败: {report_file}, {e}")

        if cleaned_count > 0:
            print(f"🧹 已清理 {cleaned_count} 个旧报告")

    def run_monitoring_cycle(self):
        """运行一次完整的监控周期"""
        print(f"🚀 开始监控周期 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # 1. 运行质量检查
            quality_report = self.run_quality_check()

            # 2. 生成趋势报告
            trend_report = self.generate_trend_report()

            # 3. 清理旧报告
            self.cleanup_old_reports()

            # 4. 生成监控摘要
            summary = self._generate_monitoring_summary(quality_report, trend_report)
            print("\n" + "=" * 60)
            print("📋 监控摘要")
            print("=" * 60)
            print(summary)

            return True

        except Exception as e:
            print(f"❌ 监控周期执行失败: {e}")
            return False

    def _generate_monitoring_summary(
        self, quality_report: Dict, trend_report: Dict
    ) -> str:
        """生成监控摘要"""
        summary_lines = []

        # 质量检查摘要
        if quality_report:
            summary_data = quality_report.get("summary", {})
            total_checks = summary_data.get("total_checks", 0)
            passed_checks = summary_data.get("passed", 0)
            failed_checks = summary_data.get("failed", 0)

            summary_lines.append(f"📊 质量检查: {passed_checks}/{total_checks} 通过")
            if failed_checks > 0:
                summary_lines.append(f"❌ 失败检查: {failed_checks} 项")
            else:
                summary_lines.append("✅ 所有检查通过")

        # 趋势摘要
        if trend_report:
            total_reports = trend_report.get("total_reports", 0)
            summary_lines.append(f"📈 历史报告: {total_reports} 个")

        # 系统状态
        summary_lines.append(
            f"🕒 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        summary_lines.append(f"📁 报告目录: {self.reports_dir}")

        return "\n".join(summary_lines)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="持续监控脚本")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--once", action="store_true", help="只运行一次")

    args = parser.parse_args()

    monitor = ContinuousMonitor(args.config)

    if args.once:
        # 运行一次监控周期
        success = monitor.run_monitoring_cycle()
        sys.exit(0 if success else 1)
    else:
        print("🔄 持续监控模式 (Ctrl+C 退出)")
        try:
            while True:
                monitor.run_monitoring_cycle()
                print("\n⏰ 等待下次检查 (60分钟)...")
                time.sleep(3600)  # 等待1小时
        except KeyboardInterrupt:
            print("\n👋 监控已停止")


if __name__ == "__main__":
    main()
