import os

import pytest
from alembic.config import Config

from alembic import command


def test_alembic_upgrade_and_downgrade() -> None:
    database_url = os.environ.get("OPUS_BLOCKS_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("OPUS_BLOCKS_TEST_DATABASE_URL is not set")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")
