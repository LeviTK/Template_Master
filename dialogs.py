try:
    from qt.core import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QFileDialog,
        QDialog,
        QListWidget,
        QHBoxLayout,
        QMessageBox,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QInputDialog,
        QListWidgetItem,
        Qt,
        QFont,
        QCheckBox,
        QGroupBox,
    )
except ImportError:
    from PyQt5.Qt import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QFileDialog,
        QDialog,
        QListWidget,
        QHBoxLayout,
        QMessageBox,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QInputDialog,
        QListWidgetItem,
        Qt,
        QFont,
        QCheckBox,
        QGroupBox,
    )

from calibre_plugins.epub_template_master.config import (
    get_templates,
    set_templates,
    get_default_template,
    set_default_template,
    add_template,
    remove_template,
    get_template_path,
    get_template_dir,
    get_duplicate_all_formats,
    set_duplicate_all_formats,
)
from calibre_plugins.epub_template_master.logic import (
    import_template_file,
    delete_template_file,
    rename_template_file,
)
import os

try:
    HEADER_STRETCH = QHeaderView.ResizeMode.Stretch
except AttributeError:
    HEADER_STRETCH = QHeaderView.Stretch

# --- 设置面板 (模板管理) ---


class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)

        tpl_group = QGroupBox("模板管理")
        tpl_layout = QVBoxLayout(tpl_group)

        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["名称", "备注", "默认"])
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 50)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tpl_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()

        import_btn = QPushButton("导入", self)
        import_btn.clicked.connect(self.import_templates)
        btn_layout.addWidget(import_btn)

        rename_btn = QPushButton("重命名", self)
        rename_btn.clicked.connect(self.rename_template)
        btn_layout.addWidget(rename_btn)

        note_btn = QPushButton("编辑备注", self)
        note_btn.clicked.connect(self.edit_note)
        btn_layout.addWidget(note_btn)

        delete_btn = QPushButton("删除", self)
        delete_btn.clicked.connect(self.delete_templates)
        btn_layout.addWidget(delete_btn)

        default_btn = QPushButton("设为默认", self)
        default_btn.clicked.connect(self.set_default)
        btn_layout.addWidget(default_btn)

        btn_layout.addStretch(1)
        tpl_layout.addLayout(btn_layout)
        layout.addWidget(tpl_group)

        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout(settings_group)

        self.dup_all_checkbox = QCheckBox("复制所有格式", self)
        self.dup_all_checkbox.setToolTip("如果未勾选，复制书籍时只复制 EPUB 格式")
        self.dup_all_checkbox.setChecked(get_duplicate_all_formats())
        settings_layout.addWidget(self.dup_all_checkbox)

        layout.addWidget(settings_group)
        layout.addStretch(1)

        self.load_templates()

    def load_templates(self):
        self.table.setRowCount(0)
        templates = get_templates()
        default = get_default_template()

        for tpl in templates:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(tpl["name"])
            name_item.setData(Qt.UserRole, tpl["filename"])
            self.table.setItem(row, 0, name_item)

            note = tpl.get("note", "")
            note_item = QTableWidgetItem(note)
            self.table.setItem(row, 1, note_item)

            is_default = tpl["filename"] == default
            default_item = QTableWidgetItem("★" if is_default else "")
            default_item.setTextAlignment(Qt.AlignCenter)
            if is_default:
                font = default_item.font()
                font.setBold(True)
                default_item.setFont(font)
            self.table.setItem(row, 2, default_item)

    def get_selected_filenames(self):
        filenames = []
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        for row in selected_rows:
            filename = self.table.item(row, 0).data(Qt.UserRole)
            if filename:
                filenames.append(filename)
        return filenames

    def import_templates(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择 EPUB 文件", "", "EPUB Files (*.epub)"
        )
        if not paths:
            return

        count = 0
        errors = []
        for path in paths:
            ok, result = import_template_file(path)
            if ok:
                count += 1
            else:
                errors.append(f"{os.path.basename(path)}: {result}")

        self.load_templates()

        msg = f"已导入 {count} 个模板"
        if errors:
            msg += "\n\n错误:\n" + "\n".join(errors)
            QMessageBox.warning(self, "导入结果", msg)
        else:
            QMessageBox.information(self, "成功", msg)

    def rename_template(self):
        filenames = self.get_selected_filenames()
        if len(filenames) != 1:
            QMessageBox.warning(self, "提示", "请选择一个模板进行重命名")
            return

        filename = filenames[0]
        templates = get_templates()
        current_name = next(
            (t["name"] for t in templates if t["filename"] == filename), filename
        )

        new_name, ok = QInputDialog.getText(
            self, "重命名", "新名称:", text=current_name
        )
        if ok and new_name and new_name != current_name:
            ok, result = rename_template_file(filename, new_name)
            if ok:
                self.load_templates()
            else:
                QMessageBox.critical(self, "错误", result)

    def edit_note(self):
        filenames = self.get_selected_filenames()
        if len(filenames) != 1:
            QMessageBox.warning(self, "提示", "请选择一个模板编辑备注")
            return

        filename = filenames[0]
        templates = get_templates()
        current_note = next(
            (t.get("note", "") for t in templates if t["filename"] == filename), ""
        )

        new_note, ok = QInputDialog.getText(
            self, "编辑备注", "备注:", text=current_note
        )
        if ok:
            for t in templates:
                if t["filename"] == filename:
                    t["note"] = new_note
                    break
            set_templates(templates)
            self.load_templates()

    def delete_templates(self):
        filenames = self.get_selected_filenames()
        if not filenames:
            return

        if (
            QMessageBox.question(self, "确认", f"删除 {len(filenames)} 个模板?")
            == QMessageBox.Yes
        ):
            count = 0
            for filename in filenames:
                ok, _ = delete_template_file(filename)
                if ok:
                    count += 1
            self.load_templates()
            QMessageBox.information(self, "完成", f"已删除 {count} 个模板")

    def set_default(self):
        filenames = self.get_selected_filenames()
        if len(filenames) != 1:
            QMessageBox.warning(self, "提示", "请选择一个模板设为默认")
            return

        set_default_template(filenames[0])
        self.load_templates()
        QMessageBox.information(self, "成功", "已设置默认模板")

    def save_settings(self):
        set_duplicate_all_formats(self.dup_all_checkbox.isChecked())


# --- 主操作对话框 ---


class MainActionDialog(QDialog):
    ACTION_NONE = 0
    ACTION_CREATE = 1
    ACTION_INSERT = 2
    ACTION_DUPLICATE = 3

    def __init__(self, parent=None, has_selection=False):
        QDialog.__init__(self, parent)
        self.has_selection = has_selection
        self.action = self.ACTION_NONE
        self.selected_template = None

        self.setWindowTitle("EPUB Template Master")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 创建书籍
        row1 = QHBoxLayout()
        create_btn = QPushButton("1. 创建书籍", self)
        create_btn.setMinimumHeight(40)
        create_btn.clicked.connect(self.on_create)
        row1.addWidget(create_btn, 1)

        create_settings_btn = QPushButton("⚙", self)
        create_settings_btn.setFixedSize(40, 40)
        create_settings_btn.setToolTip("选择模板")
        create_settings_btn.clicked.connect(
            lambda: self.select_template_and_do(self.ACTION_CREATE)
        )
        row1.addWidget(create_settings_btn)
        layout.addLayout(row1)

        # 插入书籍 -> 应用模板
        row2 = QHBoxLayout()
        insert_btn = QPushButton("2. 应用模板", self)
        insert_btn.setMinimumHeight(40)
        insert_btn.setEnabled(has_selection)
        if not has_selection:
            insert_btn.setToolTip("未选中书籍")
        else:
            insert_btn.setToolTip("为选中书籍添加 EPUB 模板 (保留元数据)")
        insert_btn.clicked.connect(self.on_insert)
        row2.addWidget(insert_btn, 1)

        insert_settings_btn = QPushButton("⚙", self)
        insert_settings_btn.setFixedSize(40, 40)
        insert_settings_btn.setToolTip("选择模板")
        insert_settings_btn.setEnabled(has_selection)
        insert_settings_btn.clicked.connect(
            lambda: self.select_template_and_do(self.ACTION_INSERT)
        )
        row2.addWidget(insert_settings_btn)
        layout.addLayout(row2)

        # 复制书籍
        row3 = QHBoxLayout()
        dup_btn = QPushButton("3. 复制书籍", self)
        dup_btn.setMinimumHeight(40)
        dup_btn.setEnabled(has_selection)
        if not has_selection:
            dup_btn.setToolTip("未选中书籍")
        dup_btn.clicked.connect(self.on_duplicate)
        row3.addWidget(dup_btn, 1)

        dup_settings_btn = QPushButton("⚙", self)
        dup_settings_btn.setFixedSize(40, 40)
        dup_settings_btn.setToolTip("复制设置")
        dup_settings_btn.clicked.connect(self.open_duplicate_settings)
        row3.addWidget(dup_settings_btn)
        layout.addLayout(row3)

        # 取消按钮
        layout.addSpacing(10)
        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch(1)
        cancel_btn = QPushButton("取消", self)
        cancel_btn.clicked.connect(self.reject)
        cancel_layout.addWidget(cancel_btn)
        layout.addLayout(cancel_layout)

    def on_create(self):
        self.action = self.ACTION_CREATE
        self.accept()

    def on_insert(self):
        self.action = self.ACTION_INSERT
        self.accept()

    def on_duplicate(self):
        self.action = self.ACTION_DUPLICATE
        self.accept()

    def select_template_and_do(self, action):
        """点击⚙按钮：打开模板选择，选中后执行操作"""
        d = TemplateSelectDialog(self)
        if d.exec_() == QDialog.Accepted:
            self.selected_template = d.get_selected_template()
            if self.selected_template:
                self.action = action
                self.accept()

    def open_duplicate_settings(self):
        d = DuplicateSettingsDialog(self)
        d.exec_()

    def get_action(self):
        return self.action

    def get_selected_template(self):
        return self.selected_template


# --- 模板选择对话框 ---


class TemplateSelectDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("选择模板")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["名称", "默认"])
        self.table.horizontalHeader().setSectionResizeMode(0, HEADER_STRETCH)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.doubleClicked.connect(self.accept)
        layout.addWidget(self.table)

        self.empty_label = QLabel("暂无模板，请先在模板管理中导入。", self)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        self.ok_btn = QPushButton("确定", self)
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)

        cancel_btn = QPushButton("取消", self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        self.load_templates()

    def load_templates(self):
        self.table.setRowCount(0)
        templates = get_templates()
        default = get_default_template()

        if not templates:
            self.table.setVisible(False)
            self.empty_label.setVisible(True)
            self.ok_btn.setEnabled(False)
            return

        self.table.setVisible(True)
        self.empty_label.setVisible(False)
        self.ok_btn.setEnabled(True)

        for tpl in templates:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(tpl["name"])
            name_item.setData(Qt.UserRole, tpl["filename"])
            self.table.setItem(row, 0, name_item)

            is_default = tpl["filename"] == default
            default_item = QTableWidgetItem("★ 默认" if is_default else "")
            if is_default:
                font = default_item.font()
                font.setBold(True)
                default_item.setFont(font)
            self.table.setItem(row, 1, default_item)

        if default:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0).data(Qt.UserRole) == default:
                    self.table.selectRow(row)
                    break
        elif self.table.rowCount() > 0:
            self.table.selectRow(0)

    def get_selected_template(self):
        row = self.table.currentRow()
        if row >= 0:
            filename = self.table.item(row, 0).data(Qt.UserRole)
            if filename:
                return get_template_path(filename)
        return None


# --- 复制设置对话框 ---


class DuplicateSettingsDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("复制设置")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        self.all_formats_cb = QCheckBox("复制所有格式", self)
        self.all_formats_cb.setToolTip("如果未勾选，只复制 EPUB 格式")
        self.all_formats_cb.setChecked(get_duplicate_all_formats())
        layout.addWidget(self.all_formats_cb)

        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        ok_btn = QPushButton("确定", self)
        ok_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消", self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def save_and_close(self):
        set_duplicate_all_formats(self.all_formats_cb.isChecked())
        self.accept()
