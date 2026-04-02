"""SFT 参数模板仓储测试。"""

from __future__ import annotations

import pytest

from app.storage import Database, SftParamTemplateRepository


SAMPLE_CLI = "swift sft --model /ssd/model --learning_rate 1e-4"
UPDATED_CLI = "swift sft --model /ssd/model2 --learning_rate 5e-5"


def test_create_template_and_list_versions(tmp_path) -> None:
    # Given: 初始化数据库与仓储
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = SftParamTemplateRepository(database)

    # When: 创建模板并读取版本
    created = repo.create_template(name="baseline", cli_text=SAMPLE_CLI)
    versions = repo.list_versions(created.id)

    # Then: 初始版本应为 v1
    assert created.name == "baseline"
    assert len(versions) == 1
    assert versions[0].version_no == 1


def test_update_template_should_append_new_version(tmp_path) -> None:
    # Given: 已存在模板
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = SftParamTemplateRepository(database)
    created = repo.create_template(name="baseline", cli_text=SAMPLE_CLI)

    # When: 更新模板
    updated = repo.update_template(created.id, name="baseline-v2", cli_text=UPDATED_CLI)
    versions = repo.list_versions(created.id)

    # Then: 模板更新成功且新增 v2
    assert updated.name == "baseline-v2"
    assert updated.cli_text == UPDATED_CLI
    assert len(versions) == 2
    assert versions[0].version_no == 2
    assert versions[1].version_no == 1


def test_create_template_should_reject_duplicate_name(tmp_path) -> None:
    # Given: 已存在同名模板
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = SftParamTemplateRepository(database)
    repo.create_template(name="baseline", cli_text=SAMPLE_CLI)

    # When / Then: 再创建同名模板应失败
    with pytest.raises(ValueError):
        repo.create_template(name="baseline", cli_text=UPDATED_CLI)


def test_delete_template_should_remove_versions(tmp_path) -> None:
    # Given: 已存在模板及历史版本
    database = Database(tmp_path / "sftlab.db")
    database.initialize()
    repo = SftParamTemplateRepository(database)
    created = repo.create_template(name="baseline", cli_text=SAMPLE_CLI)
    repo.update_template(created.id, name="baseline", cli_text=UPDATED_CLI)

    # When: 删除模板
    repo.delete_template(created.id)

    # Then: 模板与版本记录都应不存在
    assert repo.get_template(created.id) is None
    assert repo.list_versions(created.id) == []
