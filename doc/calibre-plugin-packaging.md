# Calibre 插件打包规范

## 目标
- 产出可直接在 Calibre 中安装的插件 zip 包。
- 避免目录结构错误导致 `InvalidPlugin`。

## 目录与文件要求
- 安装包必须是 `.zip`。
- `zip` 根目录必须直接包含 `__init__.py`。
- 不允许再包一层源码目录（错误示例：`epub_template_master/__init__.py`）。
- 建议包含文件：
  - `__init__.py`
  - `action.py`
  - `config.py`
  - `dialogs.py`
  - `logic.py`
  - `repositories/`
  - `services/`
  - `plugin-import-name-epub_template_master.txt`

## 排除规则
- 不要把 `__pycache__/` 打进安装包。
- 不要把 `*.pyc` 打进安装包。
- `dist/` 仅作为本地打包产物，不提交到 Git。

## 标准打包命令（当前项目）
```bash
mkdir -p dist
find src -type d -name __pycache__ -prune -exec rm -rf {} +
cd src && zip -r ../dist/epub_template_master_v1.0.0.zip __init__.py action.py config.py dialogs.py logic.py repositories services plugin-import-name-epub_template_master.txt -x "*/__pycache__/*" "*.pyc"
```

## 校验命令
```bash
unzip -l dist/epub_template_master_v1.0.0.zip
```

## 校验通过标准
- 列表中显示顶层文件：`__init__.py`、`action.py`、`config.py`、`dialogs.py`、`logic.py`、`plugin-import-name-epub_template_master.txt`。
- 列表中显示目录：`repositories/`、`services/`（且目录内无 `__pycache__` / `*.pyc`）。
- 不出现 `src/__init__.py`。

## 发布前检查
- 更新 `src/__init__.py` 中版本号。
- 重新打包并执行 `unzip -l` 校验。
- 在 Calibre 中执行“从文件加载插件”安装验证。
