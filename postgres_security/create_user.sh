#!/bin/bash
set -e 

# Load environment variables from .env file 
export $(grep -v '^#' .env | xargs)

echo "Creating PostgreSQL user '${PG_USER}' and database '${PG_DB}'..."

# Run SQL commands inside the running postgres container
docker exec -i postgres_container psql -U "$POSTGRES_USER" <<-EOSQL
  DO
  \$do\$
  BEGIN
     IF NOT EXISTS (
         SELECT FROM pg_catalog.pg_roles WHERE rolname = '${PG_USER}'
     ) THEN
         CREATE ROLE ${PG_USER} LOGIN PASSWORD '${PG_PASSWORD}';
     END IF;
  END
  \$do\$;

  DO
  \$do\$
  BEGIN
    IF NOT EXISTS (
      SELECT FROM pg_database WHERE datname = '${PG_DB}'
    ) THEN
      CREATE DATABASE ${PG_DB} OWNER ${PG_USER};
    END IF;
  END
  \$do\$;

  GRANT ALL PRIVILEGES ON DATABASE ${PG_DB} TO ${PG_USER};

  \c ${PG_DB}

  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public to ${PG_USER};
  ALTER DEFAULT PRIVILEGES FOR ROLE ${PG_USER} IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO ${PG_USER};
EOSQL

echo "User and database setup complete."
