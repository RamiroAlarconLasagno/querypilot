# migrations/env.py
"""Entorno de Alembic.

La URL de conexion se toma de QP_SYSTEM_DB_URL, nunca de alembic.ini: ese
archivo se versiona y no puede contener credenciales.

Solo migra la base PROPIA del sistema. La base de negocio del cliente es
externa y de solo lectura: el sistema jamas la modifica.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

url = os.getenv("QP_SYSTEM_DB_URL")
if not url:
    raise RuntimeError("QP_SYSTEM_DB_URL no definida")
config.set_main_option("sqlalchemy.url", url)

# Se completa en el sub-peldano 5.6, al definir el esquema de Sesion.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
