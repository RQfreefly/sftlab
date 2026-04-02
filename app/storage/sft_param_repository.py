"""SFT 参数模板仓储。"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.storage.database import Database


@dataclass(frozen=True)
class SftParamTemplate:
    """参数模板实体。"""

    id: int
    name: str
    cli_text: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class SftParamTemplateVersion:
    """参数模板历史版本实体。"""

    id: int
    template_id: int
    version_no: int
    cli_text: str
    created_at: str


class SftParamTemplateRepository:
    """管理参数模板与版本历史。"""

    def __init__(self, database: Database) -> None:
        self._database = database

    def list_templates(self) -> list[SftParamTemplate]:
        """按更新时间倒序列出模板。"""
        with self._database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, cli_text, created_at, updated_at
                FROM sft_param_templates
                ORDER BY updated_at DESC, id DESC
                """
            ).fetchall()
        return [self._to_template(row) for row in rows]

    def get_template(self, template_id: int) -> SftParamTemplate | None:
        """按 id 查询模板。"""
        with self._database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, cli_text, created_at, updated_at
                FROM sft_param_templates
                WHERE id = ?
                """,
                (template_id,),
            ).fetchone()
        if row is None:
            return None
        return self._to_template(row)

    def create_template(self, name: str, cli_text: str) -> SftParamTemplate:
        """创建模板并写入版本 1。"""
        validated_name, validated_cli = self._validate_inputs(name, cli_text)

        with self._database.connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO sft_param_templates(name, cli_text)
                    VALUES(?, ?)
                    """,
                    (validated_name, validated_cli),
                )
            except sqlite3.IntegrityError as exc:
                self._raise_name_conflict(exc, validated_name)

            template_id = int(cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO sft_param_template_versions(template_id, version_no, cli_text)
                VALUES(?, 1, ?)
                """,
                (template_id, validated_cli),
            )

        created = self.get_template(template_id)
        if created is None:
            raise RuntimeError("Template created but cannot be loaded")
        return created

    def update_template(self, template_id: int, name: str, cli_text: str) -> SftParamTemplate:
        """更新模板并追加版本快照。"""
        validated_name, validated_cli = self._validate_inputs(name, cli_text)

        with self._database.connect() as conn:
            exists = conn.execute(
                "SELECT id FROM sft_param_templates WHERE id = ?",
                (template_id,),
            ).fetchone()
            if exists is None:
                raise KeyError(f"Template not found: {template_id}")

            try:
                conn.execute(
                    """
                    UPDATE sft_param_templates
                    SET name = ?,
                        cli_text = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (validated_name, validated_cli, template_id),
                )
            except sqlite3.IntegrityError as exc:
                self._raise_name_conflict(exc, validated_name)

            next_version_no = self._next_version_no(conn, template_id)
            conn.execute(
                """
                INSERT INTO sft_param_template_versions(template_id, version_no, cli_text)
                VALUES(?, ?, ?)
                """,
                (template_id, next_version_no, validated_cli),
            )

        updated = self.get_template(template_id)
        if updated is None:
            raise RuntimeError("Template updated but cannot be loaded")
        return updated

    def delete_template(self, template_id: int) -> None:
        """删除模板及其版本记录。"""
        with self._database.connect() as conn:
            conn.execute(
                "DELETE FROM sft_param_template_versions WHERE template_id = ?",
                (template_id,),
            )
            conn.execute(
                "DELETE FROM sft_param_templates WHERE id = ?",
                (template_id,),
            )

    def list_versions(self, template_id: int) -> list[SftParamTemplateVersion]:
        """列出模板版本（新到旧）。"""
        with self._database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, template_id, version_no, cli_text, created_at
                FROM sft_param_template_versions
                WHERE template_id = ?
                ORDER BY version_no DESC
                """,
                (template_id,),
            ).fetchall()
        return [self._to_version(row) for row in rows]

    def get_version(self, version_id: int) -> SftParamTemplateVersion | None:
        """按 version id 读取历史快照。"""
        with self._database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, template_id, version_no, cli_text, created_at
                FROM sft_param_template_versions
                WHERE id = ?
                """,
                (version_id,),
            ).fetchone()

        if row is None:
            return None
        return self._to_version(row)

    def _next_version_no(self, conn: sqlite3.Connection, template_id: int) -> int:
        row = conn.execute(
            """
            SELECT COALESCE(MAX(version_no), 0) AS latest_no
            FROM sft_param_template_versions
            WHERE template_id = ?
            """,
            (template_id,),
        ).fetchone()
        latest = int(row["latest_no"]) if row else 0
        return latest + 1

    def _validate_inputs(self, name: str, cli_text: str) -> tuple[str, str]:
        normalized_name = name.strip()
        normalized_cli = cli_text.strip()

        if not normalized_name:
            raise ValueError("模板名称不能为空")
        if not normalized_cli:
            raise ValueError("CLI 内容不能为空")

        return normalized_name, normalized_cli

    def _raise_name_conflict(self, exc: sqlite3.IntegrityError, name: str) -> None:
        message = str(exc).lower()
        if "unique" in message and "sft_param_templates.name" in message:
            raise ValueError(f"模板名称已存在: {name}") from exc
        raise

    def _to_template(self, row: sqlite3.Row) -> SftParamTemplate:
        return SftParamTemplate(
            id=int(row["id"]),
            name=str(row["name"]),
            cli_text=str(row["cli_text"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def _to_version(self, row: sqlite3.Row) -> SftParamTemplateVersion:
        return SftParamTemplateVersion(
            id=int(row["id"]),
            template_id=int(row["template_id"]),
            version_no=int(row["version_no"]),
            cli_text=str(row["cli_text"]),
            created_at=str(row["created_at"]),
        )
