# -*- coding: utf-8 -*-

from calibre_plugins.epub_template_master.logic import (
    apply_template_to_book,
    create_book_from_template,
    duplicate_book,
)


class TemplateService:
    """面向 UI 的业务服务层：负责批处理流程与结果汇总。"""

    def _safe_title(self, db, book_id):
        try:
            title = db.title(book_id, index_is_id=True)
            return title or f"ID {book_id}"
        except Exception:
            return f"ID {book_id}"

    def create_from_template(self, db, template_path):
        return create_book_from_template(db, template_path)

    def apply_template_to_books(
        self,
        db,
        book_ids,
        template_path,
        progress_callback=None,
        is_cancelled=None,
    ):
        """批量应用模板，返回[(title, success, message)]。"""
        results = []

        for idx, book_id in enumerate(book_ids):
            if is_cancelled and is_cancelled():
                break

            title = self._safe_title(db, book_id)
            if progress_callback:
                progress_callback(idx, title)

            success, msg = apply_template_to_book(db, book_id, template_path)
            results.append((title, success, msg))

        return results

    def duplicate_books(
        self,
        db,
        book_ids,
        duplicate_all_formats,
        progress_callback=None,
        is_cancelled=None,
    ):
        """批量复制书籍，返回统计结果。"""
        count = 0
        new_ids = []
        errors = []

        for idx, book_id in enumerate(book_ids):
            if is_cancelled and is_cancelled():
                break

            title = self._safe_title(db, book_id)
            if progress_callback:
                progress_callback(idx, title)

            res = duplicate_book(
                db,
                book_id,
                duplicate_all_formats=duplicate_all_formats,
            )
            if res.get("success"):
                count += 1
                new_id = res.get("new_id")
                if new_id is not None:
                    new_ids.append(new_id)
            else:
                errors.append(f"{title}: {res.get('message', 'Unknown error')}")

        return {
            "count": count,
            "new_ids": new_ids,
            "errors": errors,
        }
