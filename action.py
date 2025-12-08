from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
try:
    from qt.core import QMenu, QDialog
except ImportError:
    from PyQt5.Qt import QMenu, QDialog
    
from calibre_plugins.epub_template_master.dialogs import MainActionDialog, TemplateSelectDialog
from calibre_plugins.epub_template_master.logic import create_book_from_template, apply_template_to_book, duplicate_book
from calibre_plugins.epub_template_master.config import get_default_template, get_template_path

class EPUBTemplateMasterAction(InterfaceAction):
    name = 'EPUB Template Master'
    action_spec = ('EPUB Template Master', None, 'EPUB 模板管理', None)
    
    def genesis(self):
        self.qaction.setText('EPUB Master')
        
        m = QMenu()
        self.qaction.setMenu(m)
        
        tpl_act = m.addAction("模板管理")
        tpl_act.triggered.connect(self.open_template_manager)
        
        self.qaction.triggered.connect(self.open_main_dialog)

    def open_main_dialog(self):
        """打开主对话框"""
        rows = self.gui.library_view.selectionModel().selectedRows()
        has_selection = rows and len(rows) > 0
        
        d = MainActionDialog(self.gui, has_selection=has_selection)
        if d.exec_() == QDialog.Accepted:
            action = d.get_action()
            template_from_dialog = d.get_selected_template()
            
            if action == MainActionDialog.ACTION_CREATE:
                self.do_create_book(template_from_dialog)
            elif action == MainActionDialog.ACTION_INSERT:
                self.do_apply_template(template_from_dialog)
            elif action == MainActionDialog.ACTION_DUPLICATE:
                self.do_duplicate_books()

    def _get_template_path(self, override=None):
        """获取模板路径：优先使用传入的，否则使用默认，否则打开选择对话框"""
        if override:
            return override
        
        default = get_default_template()
        if default:
            path = get_template_path(default)
            if path:
                return path
        
        d = TemplateSelectDialog(self.gui)
        if d.exec_() == QDialog.Accepted:
            return d.get_selected_template()
        return None

    def do_create_book(self, template_override=None):
        """从模板创建新书籍"""
        template_path = self._get_template_path(template_override)
        if not template_path:
            return
        
        db = self.gui.current_db
        book_id = create_book_from_template(db, template_path)
        
        if book_id:
            self.refresh_gui([book_id], added=True)
            info_dialog(self.gui, '成功', '书籍已从模板创建', show=True)
        else:
            error_dialog(self.gui, '错误', '创建书籍失败', show=True)

    def do_apply_template(self, template_override=None):
        """为选中书籍插入模板"""
        template_path = self._get_template_path(template_override)
        if not template_path:
            return
        
        ids = self.gui.library_view.get_selected_ids()
        if not ids:
            return
        
        db = self.gui.current_db
        success = 0
        skipped = 0
        
        for book_id in ids:
            if apply_template_to_book(db, book_id, template_path):
                success += 1
            else:
                skipped += 1
        
        self.refresh_gui(ids, added=False)
        info_dialog(self.gui, '完成', f'已插入: {success}\n已跳过(已有EPUB): {skipped}', show=True)

    def do_duplicate_books(self):
        """复制选中书籍"""
        ids = self.gui.library_view.get_selected_ids()
        if not ids:
            return
        
        db = self.gui.current_db
        
        count = 0
        new_ids = []
        for book_id in ids:
            res = duplicate_book(db, book_id)
            if res.get('success'):
                count += 1
                new_ids.append(res['new_id'])
        
        if new_ids:
            self.refresh_gui(new_ids, added=True)
        
        info_dialog(self.gui, '完成', f'已复制 {count}/{len(ids)} 本书籍', show=True)

    def open_template_manager(self):
        """打开模板管理"""
        self.interface_action_base_plugin.do_user_config(self.gui)

    def refresh_gui(self, book_ids, added=False):
        """刷新界面"""
        m = self.gui.library_view.model()
        
        if added:
            m.books_added(len(book_ids))
        
        m.resort(reset=False)
        self.gui.tags_view.recount()
        
        if book_ids:
            self.gui.library_view.select_rows(book_ids)

    def apply_settings(self):
        pass