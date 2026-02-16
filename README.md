# EPUB Template Master

`EPUB Template Master` 是一个 Calibre Interface Action 插件，用于管理 EPUB 模板并批量执行常见模板化操作。

## 功能概览
- 从模板创建新书籍。
- 为已选书籍批量应用模板（保留书籍主要元数据）。
- 复制书籍（可选仅复制 EPUB 或复制全部格式）。
- 模板管理：导入、重命名、备注、删除、设置默认模板。

## 运行环境
- Calibre >= `5.0.0`
- 支持平台：Windows / macOS / Linux

## 快速开始（用户）

### 1. 安装插件
1. 准备插件安装包（见下文“打包说明”或直接使用 `dist/` 产物）。
2. 打开 Calibre。
3. 进入 `首选项 -> 插件 -> 从文件加载插件`。
4. 选择 `epub_template_master_v1.0.0.zip` 并确认安装。

### 2. 首次配置
1. 点击工具栏中的 `EPUB Master`。
2. 进入 `模板管理`。
3. 导入一个或多个 `.epub` 作为模板。
4. 可设置默认模板，后续操作会优先使用该模板。

### 3. 常用操作流程
- `创建书籍`：从模板快速创建一本新书。
- `应用模板`：对已选书籍批量添加 EPUB 模板。
- `复制书籍`：批量复制已选书籍并保留格式内容。

## 打包说明
详细规范请查看：`doc/calibre-plugin-packaging.md`

常用命令（当前仓库结构）：

```bash
mkdir -p dist
find src -type d -name __pycache__ -prune -exec rm -rf {} +
cd src && zip -r ../dist/epub_template_master_v1.0.0.zip __init__.py action.py config.py dialogs.py logic.py repositories services plugin-import-name-epub_template_master.txt -x "*/__pycache__/*" "*.pyc"
cd ..
unzip -l dist/epub_template_master_v1.0.0.zip
```

校验要点：
- zip 根目录应直接出现 `__init__.py`、`action.py` 等插件文件。
- 不应出现 `src/...` 路径前缀。
- 不应出现 `__pycache__` 或 `*.pyc`。

## 项目结构

```text
src/
  __init__.py                # 插件入口与元数据
  action.py                  # Calibre 动作与 GUI 事件编排
  dialogs.py                 # 配置/选择/操作对话框
  config.py                  # JSONConfig 配置读写
  logic.py                   # 核心业务逻辑
  repositories/
    template_repository.py   # 模板文件与模板列表持久化
  services/
    template_service.py      # 批处理流程服务层

doc/
  calibre-plugin-packaging.md

dist/
  epub_template_master_v1.0.0.zip
```

## 开发流程
1. 修改源码（主要在 `src/`）。
2. 语法检查：

```bash
python3 -m py_compile src/__init__.py src/config.py src/action.py src/dialogs.py src/logic.py src/repositories/template_repository.py src/services/template_service.py
```

3. 更新版本号：`src/__init__.py` 中的 `version = (...)`。
4. 打包并校验（见上文）。
5. 在 Calibre 中做安装与功能冒烟验证。

## 发布流程（GitHub）
1. 确认 `main` 包含目标提交。
2. 创建并推送 tag（示例：`v1.0.1`）。
3. 创建 GitHub Release（标题同 tag）。
4. 上传 `dist/` 下对应 zip 作为 Release 资产。
5. Release 说明建议使用中文 Markdown，包含：
   - 主要修复点
   - 功能变更点
   - 对应资产文件名

## 故障排查
- 运行中遇到异常，可通过 `calibre-debug -g` 启动 Calibre 并查看插件 traceback。
- 模板无效/丢失时，请在模板管理中重新导入并确认默认模板可用。
- 若复制全格式失败，建议先确认书籍各格式文件在库中真实存在。

## 备注
- `dist/` 为本地构建产物目录，不建议提交到 Git。
- 详细工程规范见 `AGENTS.md`。
