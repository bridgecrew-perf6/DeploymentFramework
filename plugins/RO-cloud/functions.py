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

def envFile(db_name, db_user, db_password, default_admin, default_pass, domain, s3_bucket, s3_region):
    return """POSTGRES_HOST=postgresql
POSTGRES_DB=%s
POSTGRES_USER=%s
POSTGRES_PASSWORD=%s
NEXTCLOUD_ADMIN_USER=%s
NEXTCLOUD_ADMIN_PASSWORD=%s
REDIS_HOST=redis
OVERWRITEHOST=cloud.%s
OVERWRITEPROTOCOL=https
OBJECTSTORE_S3_REGION=%s
OBJECTSTORE_S3_BUCKET=%s
""" % (db_name, db_user, db_password, default_admin, default_pass, domain, s3_region, s3_bucket)