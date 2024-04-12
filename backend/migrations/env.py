import logging
from logging.config import fileConfig
import os
from alembic import context
from sqlalchemy import create_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Ensure the database URL is set from an environment variable
sqlalchemy_url = os.getenv('DATABASE_URL')
if not sqlalchemy_url:
    raise Exception("DATABASE_URL must be set in the environment variables.")

config.set_main_option('sqlalchemy.url', sqlalchemy_url)

# Add your model's MetaData object here for 'autogenerate' support
# Example:
# from myapp.models import Base
# target_metadata = Base.metadata
target_metadata = None

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Corrected to use the 'sqlalchemy_url' from the environment
    connectable = create_engine(sqlalchemy_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
