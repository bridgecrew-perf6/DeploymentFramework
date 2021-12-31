def dockerFile():
    return """
  postgresql:
    image: postgres:alpine
    restart: unless-stopped
    volumes:
      - ./storage/postgresql/data:/var/lib/postgresql/data
      - ./init/postgresql:/docker-entrypoint-initdb.d
    env_file:
      - ./envs/postgresql.env
"""

def envFile(default_database, default_user, default_pass):
    return """POSTGRES_PASSWORD=%s
POSTGRES_USER=%s
POSTGRES_DB=%s
""" % (default_user, default_pass, default_database)

def dbsql(db_name, db_user, db_password):
    return """#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE %s;
    CREATE USER %s WITH ENCRYPTED PASSWORD '%s';
    GRANT ALL PRIVILEGES ON DATABASE %s TO %s;
EOSQL""" % (db_name, db_user, db_password, db_name, db_user)