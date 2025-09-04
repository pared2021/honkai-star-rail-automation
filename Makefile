# Makefile for 星铁助手项目
# 提供便捷的开发命令入口

.PHONY: help install install-dev clean test coverage lint format check quality duplicate pre-commit setup-hooks ci-check build docs

# 默认目标
help:
	@echo "星铁助手项目开发命令"
	@echo ""
	@echo "安装和设置:"
	@echo "  install      - 安装项目依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  setup-hooks  - 设置预提交钩子"
	@echo ""
	@echo "代码质量:"
	@echo "  format       - 格式化代码 (black + isort)"
	@echo "  lint         - 代码风格检查 (flake8)"
	@echo "  quality      - 代码质量检查 (pylint)"
	@echo "  type-check   - 类型检查 (mypy)"
	@echo "  check        - 运行所有检查"
	@echo "  duplicate    - 重复代码检测"
	@echo ""
	@echo "测试:"
	@echo "  test         - 运行测试"
	@echo "  coverage     - 运行测试并生成覆盖率报告"
	@echo "  test-watch   - 监视模式运行测试"
	@echo ""
	@echo "CI/CD:"
	@echo "  pre-commit   - 运行预提交检查"
	@echo "  ci-check     - 运行CI质量门禁"
	@echo "  quality-gate - 运行质量门禁检查"
	@echo ""
	@echo "构建和部署:"
	@echo "  build        - 构建项目"
	@echo "  docs         - 生成文档"
	@echo "  clean        - 清理临时文件"
	@echo ""
	@echo "开发工具:"
	@echo "  pre-dev      - 开发前检查"
	@echo "  register     - 注册新功能"

# 安装依赖
install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt

# 设置预提交钩子
setup-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg

# 代码格式化
format:
	@echo "正在格式化代码..."
	black src/ tests/ scripts/
	isort src/ tests/ scripts/
	@echo "代码格式化完成"

# 代码风格检查
lint:
	@echo "正在进行代码风格检查..."
	flake8 src/ tests/ scripts/

# 代码质量检查
quality:
	@echo "正在进行代码质量检查..."
	pylint src/ tests/ scripts/

# 类型检查
type-check:
	@echo "正在进行类型检查..."
	mypy src/ tests/ scripts/

# 运行所有检查
check: format lint quality type-check
	@echo "所有代码检查完成"

# 重复代码检测
duplicate:
	@echo "正在检测重复代码..."
	python scripts/duplicate_detector.py

# 运行测试
test:
	@echo "正在运行测试..."
	python scripts/test_runner.py run

# 运行测试并生成覆盖率报告
coverage:
	@echo "正在运行测试并生成覆盖率报告..."
	python scripts/test_runner.py coverage --threshold 80

# 监视模式运行测试
test-watch:
	@echo "启动测试监视模式..."
	pytest-watch -- --cov=src --cov-report=term-missing

# 预提交检查
pre-commit:
	@echo "正在运行预提交检查..."
	pre-commit run --all-files

# CI质量门禁
ci-check:
	@echo "正在运行CI质量门禁..."
	python scripts/quality_gate.py --config .github/quality-config.json

# 质量门禁检查
quality-gate:
	@echo "正在运行质量门禁检查..."
	python scripts/quality_gate.py

# 开发前检查
pre-dev:
	@echo "请输入功能名称:"
	@read -p "功能名称: " feature_name; \
	read -p "功能描述: " description; \
	read -p "功能分类 (UI层/应用服务层/领域服务层/基础设施层): " category; \
	read -p "开发者: " author; \
	python scripts/pre_dev_check.py "$$feature_name" --description "$$description" --category "$$category" --author "$$author" --register

# 注册新功能
register:
	@echo "注册新功能到功能注册表"
	@echo "请使用 make pre-dev 命令进行完整的开发前检查和注册"

# 构建项目
build: clean
	@echo "正在构建项目..."
	python -m build

# 生成文档
docs:
	@echo "正在生成文档..."
	cd docs && make html

# 清理临时文件
clean:
	@echo "正在清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -delete
	find . -type d -name "build" -delete
	find . -type d -name "dist" -delete
	find . -type d -name "*.egg-info" -delete
	@echo "清理完成"

# 完整的开发流程
dev-flow: install-dev setup-hooks format check test coverage quality-gate
	@echo "开发环境设置完成，所有检查通过"

# 发布前检查
release-check: clean format check test coverage duplicate ci-check build
	@echo "发布前检查完成，项目已准备好发布"

# 快速检查（用于频繁的开发迭代）
quick-check: format lint test
	@echo "快速检查完成"

# 安全检查
security:
	@echo "正在进行安全检查..."
	bandit -r src/ -f json -o bandit-report.json
	safety check --json --output safety-report.json
	@echo "安全检查完成"

# 性能分析
profile:
	@echo "正在进行性能分析..."
	py-spy record -o profile.svg -- python src/main.py
	@echo "性能分析完成，结果保存在 profile.svg"

# 依赖检查
dep-check:
	@echo "正在检查依赖安全性..."
	pip-audit
	@echo "依赖检查完成"