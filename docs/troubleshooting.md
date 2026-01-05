# Troubleshooting Notes

## Test DB migrations leave schema missing

Symptoms:
- Tests fail with `UndefinedTableError: relation "users" does not exist`.
- Failures appear after a migration test runs.

Root causes:
- Alembic config does not set the section `sqlalchemy.url`, so async migrations target no DB.
- A migration test downgrades to `base` and leaves the schema empty for the rest of the suite.

Fix:
- Set `config.set_section_option(config.config_ini_section, "sqlalchemy.url", database_url)` in test and Alembic env.
- After `command.downgrade(config, "base")`, run `command.upgrade(config, "head")` to restore schema.

Reference:
- `tests/test_migrations.py`
- `alembic/env.py`

## Async engine loop mismatch in tests

Symptoms:
- `RuntimeError: Task got Future attached to a different loop`.
- Unraisable exception warnings about `Connection._cancel`.

Root cause:
- Session-scoped async engine reused across per-test event loops (`pytest-asyncio` strict mode).

Fix:
- Create async engine inside function-scoped fixture and dispose after test.

Reference:
- `tests/conftest.py`
