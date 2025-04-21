# organize_desktop
# 桌面整理工具

该工具帮助自动根据预定义的分类和文件扩展名整理桌面上的文件。对于不符合现有分类的文件，它会使用 AI 模型来进行分类。

## 特性

- **自动整理**：根据文件名或内容将文件移动到分类文件夹中。
- **自定义分类**：允许创建和管理自定义分类，以便更好地管理文件。
- **AI 集成**：对于不符合现有分类的文件，基于文件名或内容使用 AI 来分类。
- **清理空文件夹**：帮助删除桌面上的空文件夹。
- **日志记录**：记录所有操作，包括移动的文件或失败的操作。

## 需求

- Python 3.7+
- `requests` 库（使用 `pip install requests` 安装）

## 设置

1. 将该仓库克隆到本地。
2. 安装所需的依赖库：
   ```bash
   pip install -r requirements.txt
   ```
3. 在根目录创建一个名为 `settings.json` 的文件，并提供你的 AI API 密钥。示例：
   ```json
   {
     "api_base": "YOUR_API_BASE",
     "api_key": "YOUR_API_KEY_HERE",
     "api_model": "gpt-4o-mini",
     "max_ai_size": 1048576
   }
   ```

4. 创建一个名为 `categories.json` 的文件来指定默认分类和文件扩展名。（subjects优先级大于custom_categories）示例：
   ```json
   {
     "subjects": ["数学", "语文", "英语", "物理", "化学", "生物"],
     "custom_categories": [],
     "ext_map": {
       ".jpg": "图片",
       ".pdf": "文档",
       ".mp4": "视频"
     },
     "default_folder": "其他"
   }
   ```

## 使用方法

通过执行 Python 脚本来运行工具：
```bash
python organize_desktop.py
```

工具将显示一个菜单，提供以下选项：
1. **整理桌面**：将文件移动到合适的文件夹。
2. **创建自定义分类**：创建新的分类来整理文件。
3. **删除空文件夹**：删除桌面上的空文件夹。
4. **退出**：退出工具。

## 日志

该工具会将操作记录在 `organize_desktop.log` 文件中。日志包括有关移动文件的信息、错误记录和 AI 分类结果。

## 许可证

该项目采用 MIT 许可证 - 详细信息请参见 [LICENSE](LICENSE) 文件。
```
