import os
import shutil
import tempfile
import traceback
from calibre.ebooks.metadata.epub import get_metadata, set_metadata
from calibre.ebooks.metadata.book.base import Metadata

from calibre_plugins.epub_template_master.config import get_duplicate_all_formats
from calibre_plugins.epub_template_master.repositories.template_repository import (
    default_template_repository,
)

# --- 模板管理 ---


def import_template_file(source_path):
    """导入 EPUB 文件作为模板"""
    return default_template_repository.import_template_file(source_path)


def rename_template_file(filename, new_name):
    """重命名模板"""
    return default_template_repository.rename_template_file(filename, new_name)


def delete_template_file(filename):
    """删除模板"""
    return default_template_repository.delete_template_file(filename)


# --- 书籍操作 (使用 LibraryDatabase) ---


def create_book_from_template(db, template_path):
    """从模板创建新书籍 (db 是 LibraryDatabase 对象)"""
    if not os.path.exists(template_path):
        # 这种情况通常由调用者处理，但作为防线返回 None
        return None

    try:
        with open(template_path, "rb") as f:
            mi = get_metadata(f)
    except Exception:
        traceback.print_exc()
        return None

    if not mi:
        mi = Metadata("Unknown", ["Unknown"])

    # LibraryDatabase.import_book 方法会正确处理缓存
    # import_book 返回 book_id (int)
    try:
        book_id = db.import_book(mi, [template_path])
        return book_id
    except Exception:
        traceback.print_exc()
        return None


def apply_template_to_book(db, book_id, template_path):
    """为书籍添加 EPUB 模板 (db 是 LibraryDatabase 对象)"""
    if not os.path.exists(template_path):
        return False, "模板文件不存在"

    try:
        if db.has_format(book_id, "EPUB", index_is_id=True):
            return False, "已存在 EPUB 格式"
    except Exception as e:
        return False, f"检查书籍格式失败: {str(e)}"

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
        for attr in ('title', 'authors', 'publisher', 'tags',
                     'series', 'series_index', 'languages',
                     'comments', 'pubdate', 'rating'):
            val = getattr(book_mi, attr, None)
            if val is not None:
                setattr(merged_mi, attr, val)
        # identifiers 需要合并而非覆盖，原书优先
        book_ids = getattr(book_mi, 'identifiers', None) or {}
        if book_ids:
            tpl_ids = merged_mi.identifiers or {}
            tpl_ids.update(book_ids)
            merged_mi.identifiers = tpl_ids

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            tmp_path = tmp.name

        shutil.copyfile(template_path, tmp_path)

        # 使用目标书籍元数据覆盖模板元数据（缺失字段保留模板值）
        with open(tmp_path, "r+b") as f:
            set_metadata(f, merged_mi)

        # LibraryDatabase.add_format 方法
        db.add_format(book_id, "EPUB", tmp_path, index_is_id=True)
        return True, "成功"
    except Exception as e:
        traceback.print_exc()
        return False, f"应用模板失败: {str(e)}"
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def _rollback_created_book(db, book_id):
    """尝试删除新创建但失败的书籍记录，避免留下空壳记录。"""
    remove_books = getattr(db, "remove_books", None)
    if callable(remove_books):
        try:
            remove_books([book_id])
            return True
        except TypeError:
            try:
                remove_books([book_id], permanent=False)
                return True
            except Exception:
                pass
        except Exception:
            pass

    delete_books = getattr(db, "delete_books", None)
    if callable(delete_books):
        try:
            delete_books([book_id])
            return True
        except TypeError:
            try:
                delete_books([book_id], permanent=False)
                return True
            except Exception:
                pass
        except Exception:
            pass

    return False


def duplicate_book(db, book_id, duplicate_all_formats=None):
    """复制书籍 (db 是 LibraryDatabase 对象)"""
    try:
        mi = db.get_metadata(book_id, index_is_id=True)
        base_title = mi.title if getattr(mi, "title", None) else "Unknown"
        mi.title = base_title + " (副本)"

        all_formats = (
            get_duplicate_all_formats()
            if duplicate_all_formats is None
            else bool(duplicate_all_formats)
        )

        if all_formats:
            formats = db.formats(book_id, index_is_id=True)
            if not formats:
                formats = []
            elif isinstance(formats, str):
                formats = [f.strip().upper() for f in formats.split(",") if f.strip()]
            else:
                formats = [str(f).strip().upper() for f in formats if f]
        else:
            formats = (
                ["EPUB"] if db.has_format(book_id, "EPUB", index_is_id=True) else []
            )

        if not formats:
            return {"success": False, "message": "没有可复制的格式"}

        source_formats = []
        skipped_formats = []
        for fmt in formats:
            if not fmt:
                continue
            fmt_path = db.format_abspath(book_id, fmt, index_is_id=True)
            if not fmt_path or not os.path.exists(fmt_path):
                skipped_formats.append(fmt)
                continue
            source_formats.append((fmt, fmt_path))

        if not source_formats:
            return {"success": False, "message": "没有可复制的有效格式"}

        # 先创建书籍记录
        new_id = db.create_book_entry(mi)

        # 复制格式文件
        for fmt, fmt_path in source_formats:
            try:
                db.add_format(new_id, fmt, fmt_path, index_is_id=True)
            except Exception as e:
                rollback_ok = _rollback_created_book(db, new_id)
                if rollback_ok:
                    return {"success": False, "message": f"复制格式失败({fmt}): {str(e)}"}
                return {
                    "success": False,
                    "message": f"复制格式失败({fmt})且回滚失败，可能留下空记录: {str(e)}",
                }

        result = {"success": True, "new_id": new_id}
        if skipped_formats:
            result["skipped"] = skipped_formats
        return result

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "message": str(e)}
