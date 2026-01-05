from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog

try:
    from qt.core import QMenu, QDialog, QProgressDialog, Qt, QApplication
except ImportError:
    from PyQt5.Qt import QMenu, QDialog, QProgressDialog, Qt, QApplication

from calibre_plugins.epub_template_master.dialogs import (
    MainActionDialog,
    TemplateSelectDialog,
)
from calibre_plugins.epub_template_master.logic import (
    create_book_from_template,
    apply_template_to_book,
    duplicate_book,
)
from calibre_plugins.epub_template_master.config import (
    get_default_template,
    get_template_path,
)


class EPUBTemplateMasterAction(InterfaceAction):
    name = "EPUB Template Master"
    action_spec = ("EPUB Template Master", None, "EPUB 模板管理", None)

    def genesis(self):
        self.qaction.setText("EPUB Master")

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
            # info_dialog(self.gui, '成功', '书籍已从模板创建', show=True)
            # 成功通常不需要弹窗干扰，或者可以在状态栏显示
            self.gui.status_bar.showMessage("书籍已从模板创建", 3000)
        else:
            error_dialog(
                self.gui,
                "错误",
                "创建书籍失败\n可能原因：模板文件丢失或损坏",
                show=True,
            )

    def do_apply_template(self, template_override=None):
        """为选中书籍应用模板"""
        ids = self.gui.library_view.get_selected_ids()
        if not ids:
            info_dialog(self.gui, "提示", "请先选择书籍", show=True)
            return

        template_path = self._get_template_path(template_override)
        if not template_path:
            return

        db = self.gui.current_db

        # 进度条
        pd = QProgressDialog("正在应用模板...", "取消", 0, len(ids), self.gui)
        pd.setWindowTitle("处理中")
        pd.setWindowModality(Qt.WindowModal)
        pd.setMinimumDuration(0)
        pd.show()

        results = []  # list of (title, success, message)

        for i, book_id in enumerate(ids):
            if pd.wasCanceled():
                break

            title = db.title(book_id, index_is_id=True)
            pd.setValue(i)
            pd.setLabelText(f"处理: {title}")

            # processEvents 确保界面不卡死
            QApplication.processEvents()

            success, msg = apply_template_to_book(db, book_id, template_path)
            results.append((title, success, msg))

        pd.setValue(len(ids))

        self.refresh_gui(ids, added=False)

        # 生成报告
        success_count = sum(1 for r in results if r[1])
        failed_items = [r for r in results if not r[1]]

        if not failed_items:
            # 全部成功，简单提示
            self.gui.status_bar.showMessage(
                f"成功为 {success_count} 本书籍应用模板", 3000
            )
        else:
            msg = f"处理完成。\n成功: {success_count}\n失败/跳过: {len(failed_items)}"
            details = "\n".join([f"- {r[0]}: {r[2]}" for r in failed_items])
            if len(details) > 800:
                details = details[:800] + "\n... (更多日志已省略)"
            msg += f"\n\n详情:\n{details}"

            if success_count == 0:
                error_dialog(self.gui, "操作结果", msg, show=True)
            else:
                info_dialog(self.gui, "操作结果", msg, show=True)

    def do_duplicate_books(self):
        """复制选中书籍"""
        ids = self.gui.library_view.get_selected_ids()
        if not ids:
            info_dialog(self.gui, "提示", "请先选择书籍", show=True)
            return

        db = self.gui.current_db

        pd = QProgressDialog("正在复制书籍...", "取消", 0, len(ids), self.gui)
        pd.setWindowTitle("处理中")
        pd.setWindowModality(Qt.WindowModal)
        pd.show()

        count = 0
        new_ids = []
        errors = []

        for i, book_id in enumerate(ids):
            if pd.wasCanceled():
                break

            title = db.title(book_id, index_is_id=True)
            pd.setValue(i)
            pd.setLabelText(f"复制: {title}")

            QApplication.processEvents()

            res = duplicate_book(db, book_id)
            if res.get("success"):
                count += 1
                new_ids.append(res["new_id"])
            else:
                errors.append(f"{title}: {res.get('message', 'Unknown error')}")

        pd.setValue(len(ids))

        if new_ids:
            self.refresh_gui(new_ids, added=True)

        if not errors:
            self.gui.status_bar.showMessage(f"已复制 {count} 本书籍", 3000)
        else:
            msg = f"已复制: {count}\n失败: {len(errors)}\n\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += "\n..."
            info_dialog(self.gui, "复制完成", msg, show=True)

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
