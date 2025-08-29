# 图像识别模板库

这个目录包含了用于游戏自动化的图像识别模板文件。

## 目录结构

- `scenes/` - 游戏场景模板（主菜单、战斗界面等）
- `ui/` - 用户界面元素模板（按钮、菜单等）
- `buttons/` - 按钮模板
- `icons/` - 图标模板

## 模板文件命名规范

- 使用小写字母和下划线
- 描述性命名，如：`main_menu.png`、`battle_start_button.png`
- 文件格式：PNG（推荐）或 JPG

## 模板制作指南

1. **截图质量**：使用游戏内截图，确保清晰度
2. **尺寸适中**：模板不宜过大或过小，建议 50x50 到 200x200 像素
3. **背景简洁**：避免包含过多背景信息
4. **多分辨率**：为不同分辨率准备多个版本

## 使用示例

```typescript
// 查找主菜单
const result = await imageRecognition.findImage('templates/scenes/main_menu.png');

// 等待按钮出现
const button = await imageRecognition.waitForImage('templates/buttons/start_game.png');

// 识别当前场景
const scene = await imageRecognition.recognizeGameScene();
```

## 注意事项

- 模板文件应该定期更新，以适应游戏版本变化
- 建议为每个模板添加多个变体（不同光照、状态等）
- 测试模板的识别准确率，确保 > 90%