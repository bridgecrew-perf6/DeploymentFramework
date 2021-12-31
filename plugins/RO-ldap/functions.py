def dockerFile():
    return """
  ldap:
    image: tiredofit/openldap:latest
    restart: unless-stopped
    hostname: ldap.${DOMAIN}
    volumes:
      - ./storage/ldap/data:/var/lib/openldap
      - ./storage/ldap/config:/etc/openldap/slapd.d
      - ./init/ldap/ldifs:/assets/S7K-LDIF
      - ./storage/ldap/certs:/certs
      - ./storage/ldap/backup:/data/backup
    env_file:
      - ./envs/ldap.env
"""

def envFile(domain, organization, admin_pass, config_pass):
    return """DOMAIN=%s
ORGANIZATION=%s

ADMIN_PASS=%s
CONFIG_PASS=%s

ENABLE_READONLY_USER=FALSE
READONLY_USER_USER=reader
READONLY_USER_PASS=reader

HOSTNAME=ldap.%s
LOG_LEVEL=256

SCHEMA_TYPE=nis

DEBUG_MODE=TRUE

ENABLE_TLS=TRUE
TLS_CREATE_CA=TRUE
TLS_CRT_FILENAME=cert.pem
TLS_KEY_FILENAME=key.pem
TLS_ENFORCE=FALSE
TLS_CIPHER_SUITE=ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:-DHE-DSS:-RSA:!aNULL:!MD5:!DSS:!SHA
TLS_VERIFY_CLIENT=never
SSL_HELPER_PREFIX=ldap

REMOVE_CONFIG_AFTER_SETUP=false

ENABLE_BACKUP=TRUE
BACKUP_INTERVAL=0400
BACKUP_RETENTION=10080

CONTAINER_ENABLE_MONITORING=TRUE
CONTAINER_NAME=ldap
""" % (domain, organization, admin_pass, config_pass, domain)

def serviceAccountLDIF(base_dn, username, password):
      return """
dn: cn=%s,ou=Service,ou=Accounts,%s
cn: %s
objectClass: simpleSecurityObject
objectClass: organizationalRole
userpassword: {CRYPT}%s
""" % (base_dn, username, username, password)