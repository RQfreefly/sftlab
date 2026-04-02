"""Prompt 目录与模板仓储。"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.storage.database import Database


@dataclass(frozen=True)
class PromptDirectory:
    """Prompt 目录实体。"""

    id: int
    name: str
    parent_id: int | None
    created_at: str


@dataclass(frozen=True)
class PromptTemplate:
    """Prompt 模板实体。"""

    id: int
    directory_id: int | None
    title: str
    content: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class PromptVersion:
    """Prompt 历史版本实体。"""

    id: int
    prompt_id: int
    version_no: int
    content: str
    created_at: str


class PromptRepository:
    """管理 Prompt 目录、模板与历史版本。"""

    def __init__(self, database: Database) -> None:
        self._database = database

    def list_directories(self) -> list[PromptDirectory]:
        """按父目录和名称返回所有目录。"""
        with self._database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, parent_id, created_at
                FROM prompt_directories
                ORDER BY COALESCE(parent_id, 0), name ASC, id ASC
                """
            ).fetchall()
        return [self._to_directory(row) for row in rows]

    def create_directory(self, name: str, parent_id: int | None = None) -> PromptDirectory:
        """创建目录。"""
        directory_name = name.strip()
        if not directory_name:
            raise ValueError("目录名称不能为空")

        with self._database.connect() as conn:
            if parent_id is not None:
                self._ensure_directory_exists(conn, parent_id)
            self._ensure_unique_directory_name(conn, directory_name, parent_id)
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO prompt_directories(name, parent_id)
                    VALUES(?, ?)
                    """,
                    (directory_name, parent_id),
                )
            except sqlite3.IntegrityError as exc:
                self._raise_directory_conflict(exc, directory_name, parent_id)

            directory_id = int(cursor.lastrowid)
            row = conn.execute(
                """
                SELECT id, name, parent_id, created_at
                FROM prompt_directories
                WHERE id = ?
                """,
                (directory_id,),
            ).fetchone()
            if row is None:
                raise RuntimeError("Directory created but cannot be loaded")
            return self._to_directory(row)

    def get_directory(self, directory_id: int) -> PromptDirectory | None:
        """按 id 获取目录。"""
        with self._database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, parent_id, created_at
                FROM prompt_directories
                WHERE id = ?
                """,
                (directory_id,),
            ).fetchone()
        if row is None:
            return None
        return self._to_directory(row)

    def rename_directory(self, directory_id: int, new_name: str) -> PromptDirectory:
        """重命名目录，保持父目录不变。"""
        normalized_name = new_name.strip()
        if not normalized_name:
            raise ValueError("目录名称不能为空")

        with self._database.connect() as conn:
            row = conn.execute(
                "SELECT id, parent_id FROM prompt_directories WHERE id = ?",
                (directory_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Directory not found: {directory_id}")

            parent_value = row["parent_id"]
            parent_id = int(parent_value) if parent_value is not None else None

            self._ensure_unique_directory_name(
                conn,
                normalized_name,
                parent_id,
                exclude_directory_id=directory_id,
            )
            try:
                conn.execute(
                    "UPDATE prompt_directories SET name = ? WHERE id = ?",
                    (normalized_name, directory_id),
                )
            except sqlite3.IntegrityError as exc:
                self._raise_directory_conflict(exc, normalized_name, parent_id)

        renamed = self.get_directory(directory_id)
        if renamed is None:
            raise RuntimeError("Directory renamed but cannot be loaded")
        return renamed

    def delete_directory(self, directory_id: int) -> None:
        """删除空目录。"""
        with self._database.connect() as conn:
            self._ensure_directory_exists(conn, directory_id)

            child = conn.execute(
                "SELECT id FROM prompt_directories WHERE parent_id = ? LIMIT 1",
                (directory_id,),
            ).fetchone()
            if child is not None:
                raise ValueError("目录下仍有子目录，无法删除")

            prompt_row = conn.execute(
                "SELECT id FROM prompts WHERE directory_id = ? LIMIT 1",
                (directory_id,),
            ).fetchone()
            if prompt_row is not None:
                raise ValueError("目录下仍有 Prompt，无法删除")

            conn.execute("DELETE FROM prompt_directories WHERE id = ?", (directory_id,))

    def list_prompts(self, directory_id: int | None = None) -> list[PromptTemplate]:
        """按目录列出 Prompt。"""
        with self._database.connect() as conn:
            if directory_id is None:
                rows = conn.execute(
                    """
                    SELECT id, directory_id, title, content, created_at, updated_at
                    FROM prompts
                    ORDER BY updated_at DESC, id DESC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, directory_id, title, content, created_at, updated_at
                    FROM prompts
                    WHERE directory_id = ?
                    ORDER BY updated_at DESC, id DESC
                    """,
                    (directory_id,),
                ).fetchall()
        return [self._to_prompt(row) for row in rows]

    def get_prompt(self, prompt_id: int) -> PromptTemplate | None:
        """按 id 获取 Prompt。"""
        with self._database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, directory_id, title, content, created_at, updated_at
                FROM prompts
                WHERE id = ?
                """,
                (prompt_id,),
            ).fetchone()
        if row is None:
            return None
        return self._to_prompt(row)

    def create_prompt(self, directory_id: int | None, title: str, content: str) -> PromptTemplate:
        """创建 Prompt 并记录 v1。"""
        validated_title, validated_content = self._validate_prompt_input(title, content)

        with self._database.connect() as conn:
            if directory_id is not None:
                self._ensure_directory_exists(conn, directory_id)

            cursor = conn.execute(
                """
                INSERT INTO prompts(directory_id, title, content)
                VALUES(?, ?, ?)
                """,
                (directory_id, validated_title, validated_content),
            )
            prompt_id = int(cursor.lastrowid)

            conn.execute(
                """
                INSERT INTO prompt_versions(prompt_id, version_no, content)
                VALUES(?, 1, ?)
                """,
                (prompt_id, validated_content),
            )

        created = self.get_prompt(prompt_id)
        if created is None:
            raise RuntimeError("Prompt created but cannot be loaded")
        return created

    def update_prompt(
        self,
        prompt_id: int,
        directory_id: int | None,
        title: str,
        content: str,
    ) -> PromptTemplate:
        """更新 Prompt 并追加版本。"""
        validated_title, validated_content = self._validate_prompt_input(title, content)

        with self._database.connect() as conn:
            existing = conn.execute("SELECT id FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
            if existing is None:
                raise KeyError(f"Prompt not found: {prompt_id}")

            if directory_id is not None:
                self._ensure_directory_exists(conn, directory_id)

            conn.execute(
                """
                UPDATE prompts
                SET directory_id = ?,
                    title = ?,
                    content = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (directory_id, validated_title, validated_content, prompt_id),
            )

            next_version_no = self._next_version_no(conn, prompt_id)
            conn.execute(
                """
                INSERT INTO prompt_versions(prompt_id, version_no, content)
                VALUES(?, ?, ?)
                """,
                (prompt_id, next_version_no, validated_content),
            )

        updated = self.get_prompt(prompt_id)
        if updated is None:
            raise RuntimeError("Prompt updated but cannot be loaded")
        return updated

    def move_prompt(self, prompt_id: int, target_directory_id: int | None) -> PromptTemplate:
        """移动 Prompt 到目标目录，不追加版本记录。"""
        with self._database.connect() as conn:
            row = conn.execute(
                "SELECT id FROM prompts WHERE id = ?",
                (prompt_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Prompt not found: {prompt_id}")

            if target_directory_id is not None:
                self._ensure_directory_exists(conn, target_directory_id)

            conn.execute(
                """
                UPDATE prompts
                SET directory_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target_directory_id, prompt_id),
            )

        moved = self.get_prompt(prompt_id)
        if moved is None:
            raise RuntimeError("Prompt moved but cannot be loaded")
        return moved

    def delete_prompt(self, prompt_id: int) -> None:
        """删除 Prompt 与历史版本。"""
        with self._database.connect() as conn:
            conn.execute("DELETE FROM prompt_versions WHERE prompt_id = ?", (prompt_id,))
            conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))

    def list_versions(self, prompt_id: int) -> list[PromptVersion]:
        """列出 Prompt 版本（新到旧）。"""
        with self._database.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, prompt_id, version_no, content, created_at
                FROM prompt_versions
                WHERE prompt_id = ?
                ORDER BY version_no DESC
                """,
                (prompt_id,),
            ).fetchall()
        return [self._to_version(row) for row in rows]

    def get_version(self, version_id: int) -> PromptVersion | None:
        """按版本 id 获取快照。"""
        with self._database.connect() as conn:
            row = conn.execute(
                """
                SELECT id, prompt_id, version_no, content, created_at
                FROM prompt_versions
                WHERE id = ?
                """,
                (version_id,),
            ).fetchone()
        if row is None:
            return None
        return self._to_version(row)

    def _next_version_no(self, conn: sqlite3.Connection, prompt_id: int) -> int:
        row = conn.execute(
            """
            SELECT COALESCE(MAX(version_no), 0) AS latest_no
            FROM prompt_versions
            WHERE prompt_id = ?
            """,
            (prompt_id,),
        ).fetchone()
        latest = int(row["latest_no"]) if row else 0
        return latest + 1

    def _validate_prompt_input(self, title: str, content: str) -> tuple[str, str]:
        normalized_title = title.strip()
        normalized_content = content.strip()

        if not normalized_title:
            raise ValueError("Prompt 标题不能为空")
        if not normalized_content:
            raise ValueError("Prompt 内容不能为空")

        return normalized_title, normalized_content

    def _ensure_directory_exists(self, conn: sqlite3.Connection, directory_id: int) -> None:
        row = conn.execute(
            "SELECT id FROM prompt_directories WHERE id = ?",
            (directory_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Directory not found: {directory_id}")

    def _ensure_unique_directory_name(
        self,
        conn: sqlite3.Connection,
        name: str,
        parent_id: int | None,
        exclude_directory_id: int | None = None,
    ) -> None:
        if parent_id is None:
            row = conn.execute(
                """
                SELECT id
                FROM prompt_directories
                WHERE name = ?
                  AND parent_id IS NULL
                  AND (? IS NULL OR id != ?)
                LIMIT 1
                """,
                (name, exclude_directory_id, exclude_directory_id),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT id
                FROM prompt_directories
                WHERE name = ?
                  AND parent_id = ?
                  AND (? IS NULL OR id != ?)
                LIMIT 1
                """,
                (name, parent_id, exclude_directory_id, exclude_directory_id),
            ).fetchone()

        if row is not None:
            parent_display = "根目录" if parent_id is None else f"目录 {parent_id}"
            raise ValueError(f"目录名称重复: {parent_display}/{name}")

    def _raise_directory_conflict(
        self,
        exc: sqlite3.IntegrityError,
        name: str,
        parent_id: int | None,
    ) -> None:
        message = str(exc).lower()
        if "unique" in message and "prompt_directories.name" in message:
            parent_display = "根目录" if parent_id is None else f"目录 {parent_id}"
            raise ValueError(f"目录名称重复: {parent_display}/{name}") from exc
        raise

    def _to_directory(self, row: sqlite3.Row) -> PromptDirectory:
        parent_value = row["parent_id"]
        parent_id = int(parent_value) if parent_value is not None else None
        return PromptDirectory(
            id=int(row["id"]),
            name=str(row["name"]),
            parent_id=parent_id,
            created_at=str(row["created_at"]),
        )

    def _to_prompt(self, row: sqlite3.Row) -> PromptTemplate:
        directory_value = row["directory_id"]
        directory_id = int(directory_value) if directory_value is not None else None
        return PromptTemplate(
            id=int(row["id"]),
            directory_id=directory_id,
            title=str(row["title"]),
            content=str(row["content"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def _to_version(self, row: sqlite3.Row) -> PromptVersion:
        return PromptVersion(
            id=int(row["id"]),
            prompt_id=int(row["prompt_id"]),
            version_no=int(row["version_no"]),
            content=str(row["content"]),
            created_at=str(row["created_at"]),
        )
