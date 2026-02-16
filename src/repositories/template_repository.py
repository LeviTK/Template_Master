# -*- coding: utf-8 -*-

import hashlib
import os
import shutil
import uuid

from calibre_plugins.epub_template_master.config import (
    add_template,
    get_template_path,
    get_templates,
    remove_template,
    set_templates,
)


def _file_sha256(path):
    """计算文件 SHA-256，用于去重判断。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class TemplateRepository:
    """模板元数据和模板文件的持久化操作。"""

    def import_template_file(self, source_path):
        """导入 EPUB 文件作为模板，失败时做文件级回滚。按内容哈希去重。"""
        if not os.path.exists(source_path):
            return False, "源文件不存在"

        source_hash = _file_sha256(source_path)

        # 检查是否已存在内容相同的模板
        templates = get_templates()
        for tpl in templates:
            existing_path = get_template_path(tpl["filename"])
            if os.path.exists(existing_path):
                try:
                    if _file_sha256(existing_path) == source_hash:
                        return False, f"与已有模板「{tpl['name']}」内容相同"
                except Exception:
                    pass

        original_name = os.path.basename(source_path)
        name_without_ext = os.path.splitext(original_name)[0]
        unique_filename = f"{uuid.uuid4().hex[:8]}_{original_name}"

        dest_path = get_template_path(unique_filename)

        try:
            shutil.copyfile(source_path, dest_path)
            try:
                add_template(name_without_ext, unique_filename)
            except Exception:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                raise
            return True, unique_filename
        except Exception as e:
            return False, str(e)

    def rename_template_file(self, filename, new_name):
        """重命名模板（仅改元数据中的展示名）。"""
        templates = get_templates()
        for tpl in templates:
            if tpl["filename"] == filename:
                tpl["name"] = new_name
                set_templates(templates)
                return True, new_name
        return False, "模板不存在"

    def delete_template_file(self, filename):
        """删除模板文件和元数据。"""
        file_path = get_template_path(filename)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            remove_template(filename)
            return True, "已删除"
        except Exception as e:
            return False, str(e)


default_template_repository = TemplateRepository()
