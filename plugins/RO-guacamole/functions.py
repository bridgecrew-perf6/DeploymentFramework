def dockerFile():
    return """
  guacd:
    container_name: guacd
    image: guacamole/guacd
    restart: unless-stopped
  guacamole:
    container_name: guacamole
    image: 'guacamole/guacamole:latest'
    restart: unless-stopped
    env_file:
      - ./envs/guacamole.env    
    depends_on:
      - mariadb
      - guacd
"""

def envFile(db_name, db_user, db_pass, domain, client_id):
  return """
GUACD_HOSTNAME=guacd
# MYSQL_HOSTNAME=mariadb
# MYSQL_DATABASE=%s
# MYSQL_USER=%s
# MYSQL_PASSWORD=%s

OPENID_AUTHORIZATION_ENDPOINT=https://sso.%s/application/o/authorize/
OPENID_CLIENT_ID=%s
OPENID_ISSUER=https://sso.%s/application/o/guacamole/
OPENID_JWKS_ENDPOINT=https://sso.%s/application/o/guacamole/jwks/
OPENID_REDIRECT_URI=https://desktop.%s/guacamole 
""" % (db_name, db_user, db_pass, domain, client_id, domain, domain, domain)