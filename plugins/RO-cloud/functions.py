def dockerFile():
    return """
  cloud:
    image: nextcloud:latest
    restart: always
    # ports:
    #   - 8080:80
    volumes:
      - ./storage/cloud:/var/www/html
    env_file:
      - ./envs/cloud.env
    depends_on:
      - postgresql
      - sso-server
"""

def envFile(db_name, db_user, db_password, default_admin, default_pass, domain):
    return """POSTGRES_HOST=postgresql
POSTGRES_DB=%s
POSTGRES_USER=%s
POSTGRES_PASSWORD=%s
NEXTCLOUD_ADMIN_USER=%s
NEXTCLOUD_ADMIN_PASSWORD=%s
REDIS_HOST=redis
OVERWRITEHOST=cloud.%s
OVERWRITEPROTOCOL=https
""" % (db_name, db_user, db_password, default_admin, default_pass, domain)