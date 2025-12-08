import os
import shutil
import tempfile
import uuid
from calibre.ebooks.metadata.epub import get_metadata, set_metadata
from calibre.ebooks.metadata.book.base import Metadata

from calibre_plugins.epub_template_master.config import (
    get_template_dir, get_templates, set_templates, get_template_path,
    add_template, remove_template, get_default_template, set_default_template,
    get_duplicate_all_formats
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
        if tpl['filename'] == filename:
            tpl['name'] = new_name
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
    with open(template_path, 'rb') as f:
        mi = get_metadata(f)
    
    if not mi:
        mi = Metadata('Unknown', ['Unknown'])
    
    # LibraryDatabase.import_book 方法会正确处理缓存
    book_id = db.import_book(mi, [template_path])
    return book_id

def apply_template_to_book(db, book_id, template_path):
    """为书籍添加 EPUB 模板 (db 是 LibraryDatabase 对象)"""
    if db.has_format(book_id, 'EPUB', index_is_id=True):
        return False
    
    mi = db.get_metadata(book_id, index_is_id=True)
    
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        shutil.copyfile(template_path, tmp_path)
        
        with open(tmp_path, 'r+b') as f:
            set_metadata(f, mi)
        
        # LibraryDatabase.add_format 方法
        db.add_format(book_id, 'EPUB', tmp_path, index_is_id=True)
        return True
    except Exception as e:
        return False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def duplicate_book(db, book_id):
    """复制书籍 (db 是 LibraryDatabase 对象)"""
    try:
        mi = db.get_metadata(book_id, index_is_id=True)
        mi.title = mi.title + ' (副本)'
        
        all_formats = get_duplicate_all_formats()
        
        if all_formats:
            formats = db.formats(book_id, index_is_id=True)
            formats = formats.split(',') if formats else []
        else:
            formats = ['EPUB'] if db.has_format(book_id, 'EPUB', index_is_id=True) else []
        
        if not formats:
            return {'success': False, 'message': '没有可复制的格式'}
        
        # 先创建书籍记录
        new_id = db.create_book_entry(mi)
        
        # 复制格式文件
        for fmt in formats:
            fmt = fmt.strip().upper()
            fmt_path = db.format_abspath(book_id, fmt, index_is_id=True)
            if fmt_path and os.path.exists(fmt_path):
                db.add_format(new_id, fmt, fmt_path, index_is_id=True)
        
        return {'success': True, 'new_id': new_id}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}