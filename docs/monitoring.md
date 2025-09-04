# 持续监控机制

本项目建立了完善的持续监控机制，确保代码质量的持续改进和维护。

## 🎯 监控目标

- **代码质量**: 格式化、风格、类型检查
- **测试覆盖率**: 确保测试覆盖率达到80%以上
- **重复代码**: 检测并消除重复代码
- **性能监控**: 监控代码执行性能
- **安全扫描**: 检测潜在安全漏洞

## 📋 监控组件

### 1. 质量门禁 (Quality Gate)

**脚本**: `scripts/quality_gate.py`

**功能**:
- 代码格式化检查 (Black, isort)
- 代码风格检查 (flake8)
- 代码质量检查 (Pylint)
- 类型检查 (mypy)
- 重复代码检测
- 测试覆盖率检查

**使用方法**:
```bash
# 运行质量门禁
python scripts/quality_gate.py

# 查看质量报告
cat reports/quality_gate.json
```

### 2. 持续监控 (Continuous Monitoring)

**脚本**: `scripts/continuous_monitoring.py`

**功能**:
- 定期执行质量检查
- 生成趋势报告
- 清理旧报告
- 监控摘要生成

**使用方法**:
```bash
# 运行一次监控周期
python scripts/continuous_monitoring.py --once

# 启动持续监控模式
python scripts/continuous_monitoring.py

# 使用自定义配置
python scripts/continuous_monitoring.py --config config/custom_monitoring.yml
```

### 3. GitHub Actions 集成

**配置文件**: `.github/workflows/quality-check.yml`

**触发条件**:
- 推送到 main/develop 分支
- 创建 Pull Request
- 每日定时检查 (凌晨2点)

**功能**:
- 自动运行质量检查
- 上传质量报告
- PR 评论质量结果

### 4. Pre-commit 钩子

**配置文件**: `.pre-commit-config.yaml`

**功能**:
- 提交前代码格式化
- 提交前基础检查
- 推送前质量门禁
- 推送前测试运行

**安装方法**:
```bash
# 安装 pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 安装推送钩子
pre-commit install --hook-type pre-push
```

## ⚙️ 配置说明

### 监控配置文件

**文件**: `config/monitoring.yml`

**主要配置项**:

```yaml
monitoring:
  # 质量阈值
  thresholds:
    coverage_threshold: 80.0      # 测试覆盖率阈值
    pylint_threshold: 8.0         # Pylint评分阈值
    complexity_threshold: 10      # 代码复杂度阈值
    duplicate_threshold: 0.8      # 重复代码阈值

  # 监控频率
  schedule:
    daily_check: "0 2 * * *"      # 每日检查
    weekly_report: "0 9 * * 1"    # 周报
    monthly_audit: "0 10 1 * *"   # 月度审计

  # 质量门禁
  quality_gates:
    strict_mode: false            # 严格模式
    block_on_failure: true        # 失败时阻止
    required_checks:              # 必需检查
      - "代码格式化"
      - "代码风格"
      - "类型检查"
      - "测试覆盖率"
```

## 📊 报告说明

### 质量报告格式

**文件**: `reports/quality_gate.json`

**结构**:
```json
{
  "timestamp": "2025-01-15 10:30:00",
  "project_root": "/path/to/project",
  "thresholds": { ... },
  "results": [
    {
      "name": "代码格式化",
      "status": "passed",
      "message": "检查通过",
      "details": "...",
      "duration": 1.5,
      "score": null
    }
  ],
  "summary": {
    "total_checks": 6,
    "passed": 4,
    "failed": 2,
    "total_duration": 45.2
  }
}
```

### 趋势报告格式

**文件**: `reports/trend_report_YYYYMMDD.json`

**内容**:
- 质量分数趋势
- 通过/失败检查趋势
- 执行时间趋势
- 历史对比分析

## 🚀 快速开始

### 1. 初始化监控环境

```bash
# 安装依赖
pip install -r requirements-dev.txt

# 安装 pre-commit 钩子
pre-commit install
pre-commit install --hook-type pre-push

# 创建报告目录
mkdir -p reports
```

### 2. 运行首次质量检查

```bash
# 运行质量门禁
python scripts/quality_gate.py

# 查看结果
cat reports/quality_gate.json
```

### 3. 启动持续监控

```bash
# 运行一次完整监控
python scripts/continuous_monitoring.py --once

# 启动持续监控 (可选)
python scripts/continuous_monitoring.py
```

## 📈 质量改进流程

### 1. 识别问题
- 查看质量报告
- 分析失败检查项
- 确定改进优先级

### 2. 修复问题
- 代码格式化: `black . && isort .`
- 代码风格: 根据 flake8 提示修复
- 类型检查: 添加类型注解
- 测试覆盖率: 编写更多测试

### 3. 验证改进
- 重新运行质量检查
- 确认所有检查通过
- 提交代码变更

## 🔧 故障排除

### 常见问题

1. **编码问题**
   ```bash
   # 设置环境变量
   export PYTHONIOENCODING=utf-8
   ```

2. **依赖缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements-dev.txt
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   chmod +x scripts/*.py
   ```

### 调试模式

```bash
# 启用详细输出
python scripts/quality_gate.py --verbose

# 查看具体错误
python scripts/quality_gate.py --debug
```

## 📞 支持

如有问题或建议，请:
1. 查看项目文档
2. 检查 GitHub Issues
3. 联系项目维护者

---

**注意**: 持续监控机制需要定期维护和更新，建议每月检查一次配置和阈值设置。