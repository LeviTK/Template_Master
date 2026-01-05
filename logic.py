import os
import shutil
import tempfile
import uuid
from calibre.ebooks.metadata.epub import get_metadata, set_metadata
from calibre.ebooks.metadata.book.base import Metadata

from calibre_plugins.epub_template_master.config import (
    get_template_dir,
    get_templates,
    set_templates,
    get_template_path,
    add_template,
    remove_template,
    get_default_template,
    set_default_template,
    get_duplicate_all_formats,
)

# --- 模板管理 ---


def import_template_file(source_path):
    """导入 EPUB 文件作为模板"""
    if not os.path.exists(source_path):
        return False, "源文件不存在"

    original_name = os.path.basename(source_path)
    name_without_ext = os.path.splitext(original_name)[0]
    unique_filename = f"{uuid.uuid4().hex[:8]}_{original_name}"

    dest_path = os.path.join(get_template_dir(), unique_filename)

    try:
        shutil.copyfile(source_path, dest_path)
        add_template(name_without_ext, unique_filename)
        return True, unique_filename
    except Exception as e:
        return False, str(e)


def rename_template_file(filename, new_name):
    """重命名模板"""
    templates = get_templates()
    for tpl in templates:
        if tpl["filename"] == filename:
            tpl["name"] = new_name
            set_templates(templates)
            return True, new_name
    return False, "模板不存在"


def delete_template_file(filename):
    """删除模板"""
    file_path = get_template_path(filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        remove_template(filename)
        return True, "已删除"
    except Exception as e:
        return False, str(e)


# --- 书籍操作 (使用 LibraryDatabase) ---


def create_book_from_template(db, template_path):
    """从模板创建新书籍 (db 是 LibraryDatabase 对象)"""
    if not os.path.exists(template_path):
        # 这种情况通常由调用者处理，但作为防线返回 None
        return None

    with open(template_path, "rb") as f:
        mi = get_metadata(f)

    if not mi:
        mi = Metadata("Unknown", ["Unknown"])

    # LibraryDatabase.import_book 方法会正确处理缓存
    # import_book 返回 book_id (int)
    try:
        book_id = db.import_book(mi, [template_path])
        return book_id
    except Exception:
        return None


def apply_template_to_book(db, book_id, template_path):
    """为书籍添加 EPUB 模板 (db 是 LibraryDatabase 对象)"""
    if not os.path.exists(template_path):
        return False, "模板文件不存在"

    if db.has_format(book_id, "EPUB", index_is_id=True):
        return False, "已存在 EPUB 格式"

    try:
        book_mi = db.get_metadata(book_id, index_is_id=True)
    except Exception as e:
        return False, f"获取书籍元数据失败: {str(e)}"

    try:
        with open(template_path, "rb") as f:
            template_mi = get_metadata(f)
    except Exception as e:
        return False, f"读取模板元数据失败: {str(e)}"

    if not template_mi:
        template_mi = Metadata("Unknown", ["Unknown"])

    merged_mi = template_mi
    if book_mi:
        if book_mi.title:
            merged_mi.title = book_mi.title
        if book_mi.authors:
            merged_mi.authors = list(book_mi.authors)

        book_isbn = None
        if getattr(book_mi, "identifiers", None):
            book_isbn = book_mi.identifiers.get("isbn")
        if book_isbn:
            if merged_mi.identifiers is None:
                merged_mi.identifiers = {}
            merged_mi.identifiers["isbn"] = book_isbn

    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        shutil.copyfile(template_path, tmp_path)

        # 使用目标书籍元数据覆盖模板元数据（缺失字段保留模板值）
        with open(tmp_path, "r+b") as f:
            set_metadata(f, merged_mi)

        # LibraryDatabase.add_format 方法
        db.add_format(book_id, "EPUB", tmp_path, index_is_id=True)
        return True, "成功"
    except Exception as e:
        return False, f"应用模板失败: {str(e)}"
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass


def duplicate_book(db, book_id):
    """复制书籍 (db 是 LibraryDatabase 对象)"""
    try:
        mi = db.get_metadata(book_id, index_is_id=True)
        mi.title = mi.title + " (副本)"

        all_formats = get_duplicate_all_formats()

        if all_formats:
            formats = db.formats(book_id, index_is_id=True)
            formats = formats.split(",") if formats else []
        else:
            formats = (
                ["EPUB"] if db.has_format(book_id, "EPUB", index_is_id=True) else []
            )

        if not formats:
            return {"success": False, "message": "没有可复制的格式"}

        # 先创建书籍记录
        new_id = db.create_book_entry(mi)

        # 复制格式文件
        for fmt in formats:
            fmt = fmt.strip().upper()
            fmt_path = db.format_abspath(book_id, fmt, index_is_id=True)
            if fmt_path and os.path.exists(fmt_path):
                db.add_format(new_id, fmt, fmt_path, index_is_id=True)

        return {"success": True, "new_id": new_id}

    except Exception as e:
        return {"success": False, "message": str(e)}
