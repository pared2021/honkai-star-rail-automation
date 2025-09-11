# 常见问题 (FAQ)

本文档收集了用户在使用崩坏星穹铁道自动化助手过程中遇到的常见问题及其解决方案。

## 目录

1. [安装和配置](#安装和配置)
2. [游戏检测](#游戏检测)
3. [自动化操作](#自动化操作)
4. [任务管理](#任务管理)
5. [界面问题](#界面问题)
6. [性能优化](#性能优化)
7. [错误排除](#错误排除)
8. [兼容性问题](#兼容性问题)
9. [高级配置](#高级配置)
10. [故障排除](#故障排除)

---

## 安装和配置

### Q1: 安装时提示Python版本不兼容怎么办？

**A**: 本项目需要Python 3.13或更高版本。

**解决方案**:
1. 访问 [Python官网](https://www.python.org/downloads/) 下载最新版本
2. 安装时勾选"Add Python to PATH"
3. 重新启动命令行并验证版本：
   ```bash
   python --version
   ```
4. 如果系统中有多个Python版本，使用：
   ```bash
   python3.13 --version
   ```

### Q2: pip安装依赖时出现权限错误？

**A**: 这通常是权限问题导致的。

**解决方案**:
1. **推荐方法** - 使用虚拟环境：
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **临时方法** - 使用用户安装：
   ```bash
   pip install --user -r requirements.txt
   ```

3. **管理员权限**（不推荐）：
   - 以管理员身份运行命令行
   - 执行安装命令

### Q3: 虚拟环境激活失败？

**A**: 可能是执行策略限制或路径问题。

**解决方案**:
1. **PowerShell执行策略问题**：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **使用cmd而不是PowerShell**：
   ```cmd
   venv\Scripts\activate.bat
   ```

3. **检查虚拟环境路径**：
   ```bash
   # 确保在正确的项目目录下
   dir venv\Scripts
   ```

### Q4: 配置文件在哪里？如何修改？

**A**: 配置文件位于项目的`config`目录下。

**主要配置文件**:
- `config/app_config.json` - 应用主配置
- `config/game_config.json` - 游戏相关配置
- `config/automation_config.json` - 自动化配置

**修改方法**:
1. 使用应用内设置界面（推荐）
2. 直接编辑JSON文件（需要重启应用）
3. 使用配置管理脚本：
   ```bash
   python scripts/config_manager.py --set game.resolution 1920x1080
   ```

---

## 游戏检测

### Q5: 应用无法检测到游戏窗口？

**A**: 这是最常见的问题之一。

**检查清单**:
1. **游戏是否正在运行**？
   - 确保崩坏星穹铁道已启动
   - 游戏窗口可见且未最小化

2. **游戏窗口标题是否正确**？
   - 支持的标题："崩坏：星穹铁道"、"Honkai: Star Rail"
   - 检查游戏语言设置

3. **管理员权限**：
   - 右键应用图标 → "以管理员身份运行"
   - 某些情况下需要管理员权限才能检测游戏

4. **防火墙和安全软件**：
   - 将应用添加到防火墙白名单
   - 暂时关闭实时保护测试

**调试方法**:
```bash
# 运行调试模式
python main.py --debug --verbose

# 查看检测日志
type logs\game_detection.log
```

### Q6: 游戏检测成功但模板匹配失败？

**A**: 通常是分辨率或游戏设置问题。

**解决方案**:
1. **检查游戏分辨率**：
   - 推荐分辨率：1920x1080
   - 游戏设置 → 图像 → 分辨率

2. **检查游戏显示模式**：
   - 推荐：窗口化或无边框窗口
   - 避免全屏模式

3. **检查游戏画质设置**：
   - UI缩放：100%
   - 抗锯齿：关闭或最低

4. **更新模板文件**：
   ```bash
   python scripts/update_templates.py
   ```

### Q7: 检测延迟很高怎么办？

**A**: 可以通过多种方式优化检测性能。

**优化方法**:
1. **调整检测区域**：
   ```json
   {
     "detection": {
       "region": [0, 0, 1920, 1080],
       "roi_optimization": true
     }
   }
   ```

2. **降低检测频率**：
   ```json
   {
     "detection": {
       "interval": 500,
       "threshold": 0.8
     }
   }
   ```

3. **启用硬件加速**：
   ```json
   {
     "performance": {
       "use_gpu": true,
       "opencv_threads": 4
     }
   }
   ```

---

## 自动化操作

### Q8: 点击位置不准确？

**A**: 通常是坐标系统或DPI设置问题。

**解决方案**:
1. **检查DPI设置**：
   - Windows设置 → 系统 → 显示 → 缩放
   - 推荐设置为100%

2. **校准点击坐标**：
   ```bash
   python scripts/calibrate_coordinates.py
   ```

3. **调整点击偏移**：
   ```json
   {
     "automation": {
       "click_offset": {
         "x": 0,
         "y": 0
       }
     }
   }
   ```

4. **使用相对坐标**：
   ```json
   {
     "automation": {
       "use_relative_coordinates": true
     }
   }
   ```

### Q9: 自动化操作太快或太慢？

**A**: 可以调整操作延迟和速度。

**配置示例**:
```json
{
  "automation": {
    "delays": {
      "click": 500,
      "key_press": 200,
      "between_actions": 1000,
      "page_load": 3000
    },
    "speed_mode": "normal"
  }
}
```

**速度模式**:
- `"slow"`: 延迟增加50%
- `"normal"`: 默认延迟
- `"fast"`: 延迟减少30%
- `"turbo"`: 延迟减少50%（不推荐）

### Q10: 键盘输入不生效？

**A**: 可能是输入法或焦点问题。

**解决方案**:
1. **检查输入法**：
   - 切换到英文输入法
   - 关闭中文输入法的特殊功能

2. **确保游戏窗口有焦点**：
   ```python
   # 在自动化前先点击游戏窗口
   operator.click_window_center()
   time.sleep(0.5)
   operator.send_key('space')
   ```

3. **使用虚拟键码**：
   ```json
   {
     "automation": {
       "use_virtual_keys": true,
       "key_mapping": {
         "space": "VK_SPACE",
         "enter": "VK_RETURN"
       }
     }
   }
   ```

---

## 任务管理

### Q11: 任务创建失败？

**A**: 检查任务配置和权限。

**常见原因**:
1. **配置格式错误**：
   ```json
   {
     "name": "每日任务",
     "type": "daily",
     "enabled": true,
     "schedule": "0 6 * * *",
     "parameters": {
       "auto_claim": true
     }
   }
   ```

2. **权限不足**：
   - 以管理员身份运行
   - 检查文件写入权限

3. **依赖模板缺失**：
   ```bash
   python scripts/check_templates.py
   ```

### Q12: 任务执行中断？

**A**: 分析中断原因并采取相应措施。

**调试步骤**:
1. **查看任务日志**：
   ```bash
   type logs\task_execution.log
   ```

2. **检查错误代码**：
   - `E001`: 游戏窗口丢失
   - `E002`: 模板匹配失败
   - `E003`: 操作超时
   - `E004`: 网络连接问题

3. **启用详细日志**：
   ```json
   {
     "logging": {
       "level": "DEBUG",
       "task_details": true
     }
   }
   ```

### Q13: 如何设置任务优先级？

**A**: 在任务配置中设置优先级。

**配置示例**:
```json
{
  "tasks": [
    {
      "name": "紧急任务",
      "priority": "urgent",
      "weight": 100
    },
    {
      "name": "日常任务",
      "priority": "normal",
      "weight": 50
    },
    {
      "name": "后台任务",
      "priority": "low",
      "weight": 10
    }
  ]
}
```

**优先级说明**:
- `urgent`: 立即执行
- `high`: 高优先级
- `normal`: 普通优先级
- `low`: 低优先级

---

## 界面问题

### Q14: 界面显示异常或乱码？

**A**: 通常是字体或编码问题。

**解决方案**:
1. **检查系统字体**：
   - 确保安装了中文字体
   - 推荐字体：微软雅黑、思源黑体

2. **设置字体配置**：
   ```json
   {
     "ui": {
       "font_family": "Microsoft YaHei",
       "font_size": 12,
       "encoding": "utf-8"
     }
   }
   ```

3. **重置界面设置**：
   ```bash
   python scripts/reset_ui_config.py
   ```

### Q15: 界面在高DPI显示器上显示模糊？

**A**: 需要启用高DPI支持。

**解决方案**:
1. **应用程序设置**：
   ```json
   {
     "ui": {
       "high_dpi_support": true,
       "scale_factor": "auto"
     }
   }
   ```

2. **Windows兼容性设置**：
   - 右键应用程序 → 属性 → 兼容性
   - 勾选"替代高DPI缩放行为"
   - 选择"应用程序"

3. **手动设置缩放**：
   ```json
   {
     "ui": {
       "manual_scale": 1.5
     }
   }
   ```

### Q16: 主题切换不生效？

**A**: 可能需要重启应用或清除缓存。

**解决方案**:
1. **重启应用**：
   - 完全关闭应用
   - 重新启动

2. **清除主题缓存**：
   ```bash
   python scripts/clear_theme_cache.py
   ```

3. **手动设置主题**：
   ```json
   {
     "ui": {
       "theme": "dark",
       "custom_theme_path": "themes/custom.qss"
     }
   }
   ```

---

## 性能优化

### Q17: 应用运行缓慢？

**A**: 可以通过多种方式优化性能。

**优化建议**:
1. **减少检测频率**：
   ```json
   {
     "performance": {
       "detection_interval": 1000,
       "idle_detection_interval": 5000
     }
   }
   ```

2. **启用缓存**：
   ```json
   {
     "performance": {
       "template_cache": true,
       "screenshot_cache": true,
       "cache_size": 100
     }
   }
   ```

3. **优化线程数**：
   ```json
   {
     "performance": {
       "worker_threads": 4,
       "opencv_threads": 2
     }
   }
   ```

### Q18: 内存使用过高？

**A**: 检查内存泄漏并优化内存使用。

**解决方案**:
1. **启用内存监控**：
   ```bash
   python main.py --monitor-memory
   ```

2. **调整缓存大小**：
   ```json
   {
     "memory": {
       "max_cache_size": "100MB",
       "gc_interval": 60,
       "auto_cleanup": true
     }
   }
   ```

3. **定期清理**：
   ```bash
   python scripts/memory_cleanup.py
   ```

### Q19: CPU使用率过高？

**A**: 优化算法和减少不必要的计算。

**优化方法**:
1. **降低图像处理质量**：
   ```json
   {
     "image_processing": {
       "quality": "medium",
       "resize_factor": 0.8,
       "color_space": "gray"
     }
   }
   ```

2. **使用ROI优化**：
   ```json
   {
     "detection": {
       "use_roi": true,
       "roi_regions": [
         [0, 0, 400, 300],
         [1520, 0, 400, 300]
       ]
     }
   }
   ```

---

## 错误排除

### Q20: 常见错误代码及解决方案

#### E001: 游戏窗口未找到
**原因**: 游戏未运行或窗口标题不匹配
**解决**: 
- 启动游戏
- 检查游戏语言设置
- 更新窗口检测规则

#### E002: 模板匹配失败
**原因**: 游戏界面变化或分辨率不匹配
**解决**:
- 更新模板文件
- 调整匹配阈值
- 检查游戏分辨率

#### E003: 操作超时
**原因**: 网络延迟或游戏响应慢
**解决**:
- 增加超时时间
- 检查网络连接
- 降低操作频率

#### E004: 权限不足
**原因**: 缺少管理员权限
**解决**:
- 以管理员身份运行
- 检查文件权限
- 添加防火墙例外

#### E005: 配置文件错误
**原因**: JSON格式错误或配置项缺失
**解决**:
- 验证JSON格式
- 恢复默认配置
- 检查配置文档

### Q21: 如何启用调试模式？

**A**: 使用调试参数启动应用。

**调试命令**:
```bash
# 基本调试模式
python main.py --debug

# 详细调试信息
python main.py --debug --verbose

# 保存调试日志
python main.py --debug --log-file debug.log

# 特定模块调试
python main.py --debug --module game_detector
```

**调试配置**:
```json
{
  "debug": {
    "enabled": true,
    "level": "DEBUG",
    "modules": ["game_detector", "task_manager"],
    "save_screenshots": true,
    "performance_metrics": true
  }
}
```

---

## 兼容性问题

### Q22: 在不同Windows版本上的兼容性？

**A**: 支持Windows 10和Windows 11。

**兼容性说明**:
- **Windows 11**: 完全支持
- **Windows 10**: 需要版本1903或更高
- **Windows 8.1**: 有限支持
- **Windows 7**: 不支持

**解决兼容性问题**:
1. **更新系统**：
   - 安装最新的Windows更新
   - 更新显卡驱动

2. **兼容模式**：
   - 右键应用 → 属性 → 兼容性
   - 选择"Windows 10"兼容模式

### Q23: 与其他软件的冲突？

**A**: 某些软件可能会干扰自动化操作。

**常见冲突软件**:
- 杀毒软件（实时保护）
- 游戏加速器
- 屏幕录制软件
- 其他自动化工具

**解决方案**:
1. **添加白名单**：
   - 将应用添加到杀毒软件白名单
   - 关闭实时保护测试

2. **调整优先级**：
   ```bash
   # 设置高优先级
   python scripts/set_priority.py --high
   ```

3. **独占模式**：
   ```json
   {
     "compatibility": {
       "exclusive_mode": true,
       "block_other_automation": true
     }
   }
   ```

---

## 高级配置

### Q24: 如何自定义模板？

**A**: 可以创建和使用自定义模板。

**创建步骤**:
1. **截取模板图像**：
   ```bash
   python scripts/template_creator.py
   ```

2. **保存模板文件**：
   - 格式：PNG（推荐）或JPG
   - 位置：`assets/templates/custom/`
   - 命名：描述性名称

3. **注册模板**：
   ```json
   {
     "templates": {
       "custom_button": {
         "path": "custom/my_button.png",
         "threshold": 0.8,
         "region": [100, 100, 200, 50]
       }
     }
   }
   ```

4. **使用模板**：
   ```python
   result = detector.detect_template('custom_button')
   ```

### Q25: 如何编写自定义任务？

**A**: 可以通过插件系统或脚本扩展功能。

**插件开发**:
```python
# plugins/my_custom_task.py
from src.core.base_task import BaseTask

class MyCustomTask(BaseTask):
    def __init__(self, config):
        super().__init__(config)
        self.name = "自定义任务"
    
    async def execute(self):
        # 任务逻辑
        self.log_info("开始执行自定义任务")
        
        # 检测游戏状态
        if not self.detector.find_game_window():
            raise TaskError("游戏窗口未找到")
        
        # 执行操作
        result = self.operator.click_template('my_button')
        if not result.success:
            raise TaskError("点击失败")
        
        self.log_info("自定义任务完成")
        return True
```

**注册插件**:
```json
{
  "plugins": {
    "my_custom_task": {
      "enabled": true,
      "module": "plugins.my_custom_task",
      "class": "MyCustomTask"
    }
  }
}
```

### Q26: 如何设置定时任务？

**A**: 使用内置的任务调度器。

**配置示例**:
```json
{
  "scheduled_tasks": [
    {
      "name": "每日签到",
      "task_type": "daily_checkin",
      "schedule": "0 6 * * *",
      "enabled": true,
      "retry_count": 3
    },
    {
      "name": "体力消耗",
      "task_type": "stamina_usage",
      "schedule": "0 */4 * * *",
      "enabled": true,
      "conditions": {
        "min_stamina": 160
      }
    }
  ]
}
```

**Cron表达式说明**:
- `0 6 * * *`: 每天6点
- `0 */4 * * *`: 每4小时
- `0 0 * * 1`: 每周一午夜
- `0 0 1 * *`: 每月1号

---

## 故障排除

### Q27: 应用无法启动？

**A**: 按以下步骤排查问题。

**排查步骤**:
1. **检查Python环境**：
   ```bash
   python --version
   pip list
   ```

2. **检查依赖**：
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. **检查配置文件**：
   ```bash
   python scripts/validate_config.py
   ```

4. **查看启动日志**：
   ```bash
   python main.py --debug 2>&1 | tee startup.log
   ```

5. **重置配置**：
   ```bash
   python scripts/reset_config.py
   ```

### Q28: 数据丢失或损坏？

**A**: 使用备份和恢复功能。

**备份数据**:
```bash
# 手动备份
python scripts/backup_data.py

# 自动备份（每日）
python scripts/setup_auto_backup.py --daily
```

**恢复数据**:
```bash
# 列出可用备份
python scripts/list_backups.py

# 恢复特定备份
python scripts/restore_backup.py --date 2024-01-15

# 恢复最新备份
python scripts/restore_backup.py --latest
```

### Q29: 性能监控和诊断？

**A**: 使用内置的性能监控工具。

**启用监控**:
```bash
# 启动性能监控
python main.py --performance-monitor

# 生成性能报告
python scripts/performance_report.py
```

**监控指标**:
- CPU使用率
- 内存使用量
- 检测延迟
- 操作成功率
- 任务执行时间

**性能优化建议**:
```json
{
  "performance_tips": {
    "detection_interval": "根据需要调整检测频率",
    "template_cache": "启用模板缓存提升速度",
    "roi_optimization": "使用ROI减少计算量",
    "thread_pool": "合理设置线程数量"
  }
}
```

---

## 获取帮助

### 联系支持

如果以上FAQ无法解决您的问题，请通过以下方式获取帮助：

1. **GitHub Issues**: [项目地址]/issues
   - 报告Bug
   - 功能请求
   - 技术讨论

2. **GitHub Discussions**: [项目地址]/discussions
   - 使用问题
   - 经验分享
   - 社区交流

3. **文档资源**:
   - [用户手册](用户手册.md)
   - [API文档](API文档.md)
   - [贡献指南](CONTRIBUTING.md)

### 提交问题时请包含

1. **系统信息**：
   ```bash
   python scripts/collect_system_info.py
   ```

2. **错误日志**：
   - `logs/app.log`
   - `logs/error.log`
   - 控制台输出

3. **配置信息**：
   ```bash
   python scripts/export_config.py --anonymize
   ```

4. **复现步骤**：
   - 详细的操作步骤
   - 期望结果
   - 实际结果

### 社区资源

- **Wiki**: 详细的使用指南和教程
- **示例项目**: 参考实现和最佳实践
- **视频教程**: 可视化的操作指导
- **用户论坛**: 社区讨论和经验分享

---

**最后更新**: 2024年1月

**注意**: 本FAQ会根据用户反馈和软件更新持续更新。如果您发现任何错误或有改进建议，请提交Issue或Pull Request。