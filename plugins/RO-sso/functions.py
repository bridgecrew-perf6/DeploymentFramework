def dockerFile(image, tag):
    return """
  sso-server:
    image: %s:%s
    restart: unless-stopped
    command: server
    volumes:
      - ./storage/sso/media:/media
      - ./storage/sso/custom-templates:/templates
      #- geoip:/geoip
    env_file:
      - ./envs/sso.env
    depends_on:
      - ldap
      - postgresql
    # ports:
    #   - "0.0.0.0:9000:9000"
    #   - "0.0.0.0:9443:9443"
  
  sso-worker:
    image: %s:%s
    restart: unless-stopped
    command: worker
    # This is optional, and can be removed. If you remove this, the following will happen
    # - The permissions for the /backups and /media folders aren't fixed, so make sure they are 1000:1000
    # - The docker socket can't be accessed anymore
    user: root
    volumes:
      - ./storage/sso/backups:/backups
      - ./storage/sso/media:/media
      - ./storage/sso/custom-templates:/templates
      - /var/run/docker.sock:/var/run/docker.sock
      #- geoip:/geoip
    env_file:
      - ./envs/sso.env
    depends_on:
      - sso-server
""" % (image, tag, image, tag)

def envFile(secret_key, admin_pass, admin_token, db_user, db_name, db_pass):
    return """
AUTHENTIK_SECRET_KEY=%s
AK_ADMIN_PASS=%s
AK_ADMIN_TOKEN=%s

# Connection Information
AUTHENTIK_REDIS__HOST=redis
AUTHENTIK_POSTGRESQL__HOST=postgresql
AUTHENTIK_POSTGRESQL__USER=%s
AUTHENTIK_POSTGRESQL__NAME=%s
AUTHENTIK_POSTGRESQL__PASSWORD=%s

# SMTP Host Emails are sent to
AUTHENTIK_EMAIL__HOST=mailserver
AUTHENTIK_EMAIL__PORT=25
# Optionally authenticate (don't add quotation marks to you password)
AUTHENTIK_EMAIL__USERNAME=
AUTHENTIK_EMAIL__PASSWORD=
AUTHENTIK_EMAIL__USE_TLS=TRUE
AUTHENTIK_EMAIL__USE_SSL=false
AUTHENTIK_EMAIL__TIMEOUT=10
# Email address authentik will send from, should have a correct @domain
AUTHENTIK_EMAIL__FROM=noreply@sniper7kills.com
""" % (secret_key, admin_pass, admin_token, db_user, db_name, db_pass)