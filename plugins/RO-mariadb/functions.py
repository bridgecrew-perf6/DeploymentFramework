def dockerFile():
    return """
  mariadb:
    image: mariadb:latest
    restart: unless-stopped
    volumes:
      - ./storage/mariadb/data:/var/lib/mysql
      - ./init/mariadb:/docker-entrypoint-initdb.d
    env_file:
      - ./envs/mariadb.env
"""

def envFile(root_pass, default_database, default_user, default_pass):
    return """MARIADB_USER=%s
MARIADB_PASSWORD=%s
MARIADB_DATABASE=%s
MARIADB_ROOT_PASSWORD=%s
""" % (default_user, default_pass, default_database, root_pass)

def dbsql(db_name, db_user, db_password):
    return """CREATE DATABASE %s;
CREATE USER '%s'@'%%' IDENTIFIED BY '%s';
GRANT ALL PRIVILEGES ON %s.* TO '%s'@'%%';
FLUSH PRIVILEGES;""" % (db_name, db_user, db_password, db_name, db_user)