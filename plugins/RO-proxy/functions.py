def dockerFile():
    return """
  proxy:
    image: 'jc21/nginx-proxy-manager:latest'
    restart: unless-stopped
    ports:
      # These ports are in format <public-port>:<container-port>
      - '80:80' # Public HTTP Port
      - '443:443' # Public HTTPS Port
      - '81:81' # Admin Web Port
    volumes:
      - ./storage/proxy/data:/data
      - ./storage/proxy/letsencrypt:/etc/letsencrypt
    env_file:
      - ./envs/proxy.env
    depends_on:
      - mariadb
"""

def envFile(mysql_database, mysql_user, mysql_pass):
    return """DB_MYSQL_HOST=mariadb
DB_MYSQL_PORT=3306
DB_MYSQL_USER=%s
DB_MYSQL_PASSWORD=%s
DB_MYSQL_NAME=%s
""" % (mysql_user, mysql_pass, mysql_database)