def dockerFile():
    return """
  wordpress:
    depends_on:
      - mariadb
    image: wordpress:latest
    volumes:
      - ./storage/wordpress/html:/var/www/html
      - ./storage/wordpress/themes:/var/www/html/wp-content/themes/
      - ./storage/wordpress/plugins:/var/www/html/wp-content/plugins/
    restart: always
    env_file:
      - ./envs/wordpress.env
"""

def envFile(db_name, db_user, db_pass):
  return """WORDPRESS_DB_HOST=mariadb
WORDPRESS_DB_USER=%s
WORDPRESS_DB_PASSWORD=%s
WORDPRESS_DB_NAME=%s
# WORDPRESS_AUTH_KEY=
# WORDPRESS_SECURE_AUTH_KEY
# WORDPRESS_LOGGED_IN_KEY
# WORDPRESS_NONCE_KEY
# WORDPRESS_AUTH_SALT
# WORDPRESS_SECURE_AUTH_SALT
# WORDPRESS_LOGGED_IN_SALT
# WORDPRESS_NONCE_SALT
# WORDPRESS_TABLE_PREFIX
# WORDPRESS_DEBUG
""" % (db_user, db_pass, db_name)