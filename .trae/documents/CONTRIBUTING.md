# 贡献指南 (CONTRIBUTING)

感谢您对崩坏星穹铁道自动化助手项目的关注！我们欢迎各种形式的贡献，包括但不限于代码、文档、测试、反馈和建议。

## 目录

1. [行为准则](#行为准则)
2. [如何贡献](#如何贡献)
3. [开发环境设置](#开发环境设置)
4. [代码规范](#代码规范)
5. [提交规范](#提交规范)
6. [Pull Request流程](#pull-request流程)
7. [问题报告](#问题报告)
8. [功能请求](#功能请求)
9. [文档贡献](#文档贡献)
10. [测试指南](#测试指南)
11. [发布流程](#发布流程)

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们作为贡献者和维护者承诺，无论年龄、体型、残疾、种族、性别认同和表达、经验水平、国籍、个人形象、种族、宗教或性取向如何，参与我们项目和社区的每个人都能享受无骚扰的体验。

### 我们的标准

**积极行为包括：**
- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同情

**不可接受的行为包括：**
- 使用性化的语言或图像
- 恶意评论、人身攻击或政治攻击
- 公开或私下骚扰
- 未经明确许可发布他人的私人信息
- 其他在专业环境中可能被认为不当的行为

### 执行

如果您遇到不当行为，请联系项目维护团队。所有投诉都将被审查和调查，并将产生被认为必要和适当的回应。

## 如何贡献

### 贡献类型

我们欢迎以下类型的贡献：

1. **🐛 错误修复**
   - 修复已知的bug
   - 改进错误处理
   - 提升稳定性

2. **✨ 新功能**
   - 添加新的自动化功能
   - 改进用户界面
   - 增强性能

3. **📚 文档改进**
   - 完善API文档
   - 改进用户指南
   - 添加示例代码

4. **🧪 测试**
   - 编写单元测试
   - 添加集成测试
   - 改进测试覆盖率

5. **🔧 工具和基础设施**
   - 改进构建系统
   - 优化CI/CD流程
   - 添加开发工具

### 贡献流程概览

1. **Fork** 项目到您的GitHub账户
2. **Clone** 您的fork到本地
3. **创建** 新的功能分支
4. **开发** 并测试您的更改
5. **提交** 您的更改
6. **推送** 到您的fork
7. **创建** Pull Request
8. **等待** 代码审查
9. **合并** 到主分支

## 开发环境设置

### 系统要求

- **操作系统**: Windows 10/11 (推荐)
- **Python**: 3.13 或更高版本
- **Git**: 最新版本
- **IDE**: VS Code (推荐) 或 PyCharm

### 环境配置

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/xingtie.git
   cd xingtie
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **配置开发工具**
   ```bash
   # 安装pre-commit钩子
   pre-commit install
   
   # 运行初始化脚本
   python scripts/setup_dev.py
   ```

5. **验证安装**
   ```bash
   # 运行测试
   make test
   
   # 检查代码质量
   make lint
   
   # 启动应用
   python main.py
   ```

### 开发工具配置

#### VS Code配置

创建 `.vscode/settings.json`：
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.banditEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

#### PyCharm配置

1. 设置Python解释器为虚拟环境
2. 启用代码检查工具
3. 配置测试运行器为pytest
4. 设置代码格式化工具

## 代码规范

### Python代码风格

我们遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 和项目特定的编码规范：

#### 基本规则

1. **缩进**: 使用4个空格
2. **行长度**: 最大88字符（Black格式化器标准）
3. **引号**: 优先使用双引号
4. **导入**: 按标准库、第三方库、本地模块分组

#### 命名规范

```python
# 类名：PascalCase
class GameDetector:
    pass

# 函数和变量：snake_case
def detect_game_window():
    window_handle = None
    return window_handle

# 常量：UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 私有成员：前缀下划线
class TaskManager:
    def __init__(self):
        self._tasks = []
        self.__internal_state = {}
```

#### 类型注解

```python
from typing import Optional, List, Dict, Any, Union

def process_tasks(tasks: List[Dict[str, Any]], 
                 timeout: Optional[float] = None) -> bool:
    """处理任务列表
    
    Args:
        tasks: 任务列表
        timeout: 超时时间（秒）
        
    Returns:
        bool: 是否处理成功
    """
    pass

class ConfigManager:
    def __init__(self, config_path: Union[str, Path]):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
```

#### 文档字符串

使用Google风格的文档字符串：

```python
def detect_template(self, template_name: str, 
                   region: Optional[Tuple[int, int, int, int]] = None,
                   threshold: float = 0.8) -> DetectionResult:
    """检测模板在屏幕上的位置
    
    使用模板匹配算法在指定区域内查找模板图像。支持多种匹配算法
    和阈值调整，以适应不同的检测需求。
    
    Args:
        template_name: 模板文件名（不含扩展名）
        region: 检测区域，格式为(x, y, width, height)。
               如果为None，则在整个屏幕范围内检测
        threshold: 匹配阈值，范围0.0-1.0，值越高要求匹配度越高
        
    Returns:
        DetectionResult: 包含检测结果的对象，包括：
            - success: 是否检测成功
            - confidence: 匹配置信度
            - position: 匹配位置坐标
            - template_name: 模板名称
            
    Raises:
        TemplateNotFoundError: 当指定的模板文件不存在时
        ScreenshotError: 当无法获取屏幕截图时
        
    Example:
        >>> detector = GameDetector(config)
        >>> result = detector.detect_template('start_button')
        >>> if result.success:
        ...     print(f"找到按钮，位置: {result.position}")
    """
    pass
```

### 错误处理

#### 异常设计

```python
# 自定义异常层次
class XingTieException(Exception):
    """项目基础异常类"""
    pass

class GameDetectionError(XingTieException):
    """游戏检测相关异常"""
    pass

class TemplateNotFoundError(GameDetectionError):
    """模板文件未找到异常"""
    def __init__(self, template_name: str):
        self.template_name = template_name
        super().__init__(f"模板文件未找到: {template_name}")
```

#### 错误处理模式

```python
import logging
from typing import Optional

def safe_operation(operation_name: str):
    """安全操作装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                logging.info(f"开始执行: {operation_name}")
                result = func(*args, **kwargs)
                logging.info(f"执行成功: {operation_name}")
                return result
            except Exception as e:
                logging.error(f"执行失败: {operation_name}, 错误: {e}")
                raise
        return wrapper
    return decorator

@safe_operation("游戏窗口检测")
def find_game_window() -> Optional[WindowInfo]:
    # 实现逻辑
    pass
```

### 日志记录

```python
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用示例
class GameDetector:
    def __init__(self, config: dict):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("初始化游戏检测器")
        
    def detect_template(self, template_name: str) -> DetectionResult:
        self.logger.debug(f"开始检测模板: {template_name}")
        try:
            # 检测逻辑
            result = self._perform_detection(template_name)
            self.logger.info(f"模板检测成功: {template_name}, 置信度: {result.confidence}")
            return result
        except Exception as e:
            self.logger.error(f"模板检测失败: {template_name}, 错误: {e}")
            raise
```

## 提交规范

### 提交消息格式

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

#### 提交类型

- **feat**: 新功能
- **fix**: 错误修复
- **docs**: 文档更新
- **style**: 代码格式化（不影响功能）
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动
- **perf**: 性能优化
- **ci**: CI/CD相关

#### 示例

```bash
# 新功能
feat(detector): 添加多分辨率支持

# 错误修复
fix(ui): 修复设置页面保存按钮无响应问题

# 文档更新
docs: 更新API文档和使用示例

# 重构
refactor(core): 重构任务管理器，提升代码可读性

# 测试
test(detector): 添加游戏检测模块单元测试

# 性能优化
perf(operator): 优化点击操作响应时间
```

#### 详细提交消息

```bash
feat(automation): 添加自定义任务模板功能

- 支持用户创建自定义自动化任务
- 提供可视化任务编辑器
- 添加模板导入导出功能
- 包含预设任务模板库

Closes #123
Breaking Change: 旧版本的任务配置格式不再兼容
```

### 分支命名规范

```bash
# 功能分支
feature/task-template-editor
feature/multi-resolution-support

# 修复分支
fix/ui-button-response
fix/memory-leak-issue

# 文档分支
docs/api-documentation
docs/user-guide-update

# 重构分支
refactor/task-manager
refactor/config-system
```

## Pull Request流程

### 创建Pull Request

1. **确保分支是最新的**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   ```

2. **运行完整测试**
   ```bash
   make test-all
   make lint
   make type-check
   ```

3. **创建PR**
   - 使用清晰的标题
   - 填写详细的描述
   - 关联相关issue
   - 添加适当的标签

### PR模板

```markdown
## 变更描述

简要描述此PR的目的和实现的功能。

## 变更类型

- [ ] 错误修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 性能优化
- [ ] 其他（请说明）

## 测试

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成
- [ ] 添加了新的测试用例

## 检查清单

- [ ] 代码遵循项目编码规范
- [ ] 自我审查了代码变更
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 没有引入新的警告
- [ ] 添加了适当的测试
- [ ] 所有测试都通过

## 相关Issue

Closes #(issue编号)

## 截图（如适用）

如果有UI变更，请提供截图。

## 额外说明

任何需要特别注意的地方或额外的上下文信息。
```

### 代码审查

#### 审查者指南

1. **功能性审查**
   - 代码是否实现了预期功能
   - 是否有潜在的bug
   - 边界条件是否处理正确

2. **代码质量审查**
   - 代码是否清晰易读
   - 是否遵循项目规范
   - 是否有重复代码

3. **性能审查**
   - 是否有性能问题
   - 资源使用是否合理
   - 是否有内存泄漏

4. **安全审查**
   - 是否有安全漏洞
   - 输入验证是否充分
   - 敏感信息是否安全

#### 审查反馈

```markdown
# 审查反馈示例

## 总体评价
整体实现良好，功能完整，代码质量较高。

## 主要问题
1. **性能问题**: L45-50的循环可能导致性能问题，建议优化
2. **错误处理**: L78缺少异常处理，可能导致程序崩溃

## 建议改进
1. 添加更多的单元测试覆盖边界情况
2. 考虑使用缓存机制提升性能
3. 添加更详细的日志记录

## 小问题
- L23: 变量命名可以更清晰
- L56: 注释可以更详细
- L89: 可以使用更简洁的写法

## 批准条件
修复主要问题后即可合并。
```

## 问题报告

### 报告Bug

使用GitHub Issues报告bug时，请包含以下信息：

#### Bug报告模板

```markdown
## Bug描述

简要描述遇到的问题。

## 复现步骤

1. 打开应用
2. 点击'...'
3. 输入'...'
4. 看到错误

## 期望行为

描述您期望发生的情况。

## 实际行为

描述实际发生的情况。

## 环境信息

- 操作系统: [例如 Windows 11]
- Python版本: [例如 3.13.0]
- 应用版本: [例如 1.0.0]
- 游戏版本: [例如 2.6.0]

## 附加信息

- 错误日志
- 屏幕截图
- 配置文件
- 其他相关信息

## 可能的解决方案

如果您有解决方案的想法，请在此描述。
```

### 日志收集

报告问题时，请提供相关日志：

```bash
# 收集应用日志
cp logs/app.log logs/app_$(date +%Y%m%d_%H%M%S).log

# 收集系统信息
python scripts/collect_system_info.py > system_info.txt

# 收集配置信息（注意隐私）
python scripts/collect_config_info.py > config_info.txt
```

## 功能请求

### 功能请求模板

```markdown
## 功能描述

简要描述您希望添加的功能。

## 问题背景

描述当前遇到的问题或限制。

## 解决方案

描述您期望的解决方案。

## 替代方案

描述您考虑过的其他解决方案。

## 用户价值

这个功能将如何帮助用户？

## 实现复杂度

- [ ] 简单（1-2天）
- [ ] 中等（1周）
- [ ] 复杂（2-4周）
- [ ] 非常复杂（1个月以上）

## 相关资源

- 相关文档
- 参考实现
- 设计图
```

### 功能优先级

我们使用以下标准评估功能请求：

1. **用户价值**: 对用户的帮助程度
2. **实现复杂度**: 开发所需的时间和资源
3. **维护成本**: 长期维护的复杂度
4. **项目一致性**: 与项目目标的一致性
5. **社区需求**: 社区的支持程度

## 文档贡献

### 文档类型

1. **用户文档**
   - 用户手册
   - 安装指南
   - 常见问题

2. **开发者文档**
   - API文档
   - 架构设计
   - 贡献指南

3. **项目文档**
   - README
   - CHANGELOG
   - 许可证

### 文档规范

#### Markdown规范

```markdown
# 一级标题

## 二级标题

### 三级标题

#### 四级标题

**粗体文本**
*斜体文本*
`行内代码`

```python
# 代码块
def example_function():
    pass
```

> 引用文本

- 无序列表项
- 另一个列表项

1. 有序列表项
2. 另一个列表项

[链接文本](URL)

![图片描述](图片URL)

| 表格 | 标题 |
|------|------|
| 内容 | 内容 |
```

#### 中文文档规范

1. **标点符号**: 使用中文标点符号
2. **空格**: 中英文之间添加空格
3. **术语**: 保持术语一致性
4. **语言**: 使用简洁明了的语言

示例：
```markdown
# 正确
这是一个 Python 项目，使用 PyQt6 框架开发。

# 错误
这是一个Python项目,使用PyQt6框架开发.
```

## 测试指南

### 测试策略

我们采用多层次的测试策略：

1. **单元测试**: 测试单个函数或类
2. **集成测试**: 测试模块间的交互
3. **端到端测试**: 测试完整的用户流程
4. **性能测试**: 测试性能和资源使用

### 编写测试

#### 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch
from src.core.game_detector import GameDetector, DetectionResult

class TestGameDetector:
    """游戏检测器测试类"""
    
    @pytest.fixture
    def detector(self):
        """测试用的检测器实例"""
        config = {
            'threshold': 0.8,
            'timeout': 30,
            'template_path': 'tests/fixtures/templates/'
        }
        return GameDetector(config)
    
    def test_detect_template_success(self, detector):
        """测试模板检测成功的情况"""
        # Arrange
        template_name = 'test_button'
        expected_position = (100, 200)
        
        with patch.object(detector, '_perform_detection') as mock_detect:
            mock_detect.return_value = DetectionResult(
                success=True,
                confidence=0.95,
                position=expected_position,
                template_name=template_name,
                timestamp=1234567890.0
            )
            
            # Act
            result = detector.detect_template(template_name)
            
            # Assert
            assert result.success is True
            assert result.confidence == 0.95
            assert result.position == expected_position
            assert result.template_name == template_name
            mock_detect.assert_called_once_with(template_name)
    
    def test_detect_template_not_found(self, detector):
        """测试模板未找到的情况"""
        # Arrange
        template_name = 'nonexistent_template'
        
        with patch.object(detector, '_perform_detection') as mock_detect:
            mock_detect.return_value = DetectionResult(
                success=False,
                confidence=0.0,
                position=None,
                template_name=template_name,
                timestamp=1234567890.0
            )
            
            # Act
            result = detector.detect_template(template_name)
            
            # Assert
            assert result.success is False
            assert result.confidence == 0.0
            assert result.position is None
    
    @pytest.mark.parametrize("threshold,expected_calls", [
        (0.5, 1),
        (0.8, 1),
        (0.95, 1),
    ])
    def test_detect_template_with_different_thresholds(self, detector, threshold, expected_calls):
        """测试不同阈值下的模板检测"""
        with patch.object(detector, '_perform_detection') as mock_detect:
            detector.detect_template('test_template', threshold=threshold)
            assert mock_detect.call_count == expected_calls
```

#### 集成测试示例

```python
import pytest
from src.core.game_detector import GameDetector
from src.core.game_operator import GameOperator
from src.core.task_manager import TaskManager

class TestGameAutomation:
    """游戏自动化集成测试"""
    
    @pytest.fixture
    def automation_system(self):
        """完整的自动化系统"""
        detector = GameDetector({'threshold': 0.8})
        operator = GameOperator(detector)
        task_manager = TaskManager()
        return {
            'detector': detector,
            'operator': operator,
            'task_manager': task_manager
        }
    
    def test_complete_task_flow(self, automation_system):
        """测试完整的任务执行流程"""
        # 这里会测试从任务创建到执行完成的整个流程
        pass
```

### 测试运行

```bash
# 运行所有测试
make test

# 运行特定测试文件
pytest tests/test_game_detector.py

# 运行特定测试类
pytest tests/test_game_detector.py::TestGameDetector

# 运行特定测试方法
pytest tests/test_game_detector.py::TestGameDetector::test_detect_template_success

# 运行带覆盖率的测试
pytest --cov=src tests/

# 生成HTML覆盖率报告
pytest --cov=src --cov-report=html tests/
```

### 测试数据

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / 'fixtures'

@pytest.fixture
def sample_screenshot(test_data_dir):
    """示例截图"""
    return test_data_dir / 'screenshots' / 'sample.png'

@pytest.fixture
def sample_template(test_data_dir):
    """示例模板"""
    return test_data_dir / 'templates' / 'button.png'
```

## 发布流程

### 版本发布

1. **准备发布**
   ```bash
   # 更新版本号
   python scripts/bump_version.py 1.1.0
   
   # 更新CHANGELOG
   python scripts/update_changelog.py
   
   # 运行完整测试
   make test-all
   ```

2. **创建发布分支**
   ```bash
   git checkout -b release/1.1.0
   git add .
   git commit -m "chore: 准备发布 v1.1.0"
   git push origin release/1.1.0
   ```

3. **创建Release PR**
   - 创建从release分支到main的PR
   - 进行最终审查
   - 合并到main分支

4. **创建Git标签**
   ```bash
   git checkout main
   git pull origin main
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

5. **发布到GitHub**
   - 在GitHub上创建Release
   - 上传构建产物
   - 发布Release Notes

### 热修复流程

```bash
# 从main分支创建热修复分支
git checkout main
git checkout -b hotfix/critical-bug-fix

# 修复问题
# ...

# 提交修复
git add .
git commit -m "fix: 修复关键bug"

# 创建PR并合并
# ...

# 发布热修复版本
python scripts/bump_version.py 1.0.1 --patch
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin v1.0.1
```

## 社区参与

### 讨论和交流

- **GitHub Discussions**: 项目讨论和问答
- **Issues**: Bug报告和功能请求
- **Pull Requests**: 代码贡献和审查

### 贡献者认可

我们重视每一位贡献者的努力：

1. **贡献者列表**: 在README中维护贡献者列表
2. **Release Notes**: 在发布说明中感谢贡献者
3. **特殊贡献**: 对重大贡献给予特别认可

### 成为维护者

活跃的贡献者可能被邀请成为项目维护者：

**条件**:
- 持续的高质量贡献
- 对项目的深入理解
- 良好的沟通能力
- 社区责任感

**职责**:
- 代码审查
- Issue管理
- 发布管理
- 社区支持

## 联系方式

如果您有任何问题或建议，请通过以下方式联系我们：

- **GitHub Issues**: 报告问题和功能请求
- **GitHub Discussions**: 项目讨论和问答
- **Email**: [项目邮箱]

---

感谢您对崩坏星穹铁道自动化助手项目的贡献！您的参与让这个项目变得更好。