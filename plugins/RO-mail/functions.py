def dockerFile():
    return """
  mailserver:
    image: docker.io/mailserver/docker-mailserver:latest
    container_name: mailserver
    ports:
      - "25:25"
      - "143:143"
      - "587:587"
      - "993:993"
    volumes:
      - ./storage/mailserver/mail/:/var/mail/
      - ./storage/mailserver/state/:/var/mail-state/
      - ./storage/mailserver/logs/:/var/log/mail/
      - ./init/mailserver/config/:/tmp/docker-mailserver/
      - ./init/mailserver/dovecot-oauth2.conf.ext:/etc/dovecot/conf.d/auth-oauth2.conf.ext
      - ./init/mailserver/10-auth.conf:/etc/dovecot/conf.d/10-auth.conf
      - /etc/localtime:/etc/localtime:ro
    env_file:
      - ./envs/mailserver.env
    cap_add:
      - NET_ADMIN
      - SYS_PTRACE
    restart: always

  webmail:
    image: roundcube/roundcubemail:latest-apache
    environment:
      - ROUNDCUBEMAIL_DEFAULT_HOST=mailserver
      - ROUNDCUBEMAIL_SMTP_SERVER=mailserver
    volumes:
      - ./init/webmail/config/:/var/roundcube/config/
"""

def envFile(base_dn, ldap_pass, domain):
    return """ENABLE_SPAMASSASSIN=1
SPAMASSASSIN_SPAM_TO_INBOX=1
ENABLE_CLAMAV=1
ENABLE_FAIL2BAN=0
ENABLE_POSTGREY=1
ONE_DIR=1
DMS_DEBUG=1
ENABLE_LDAP=1
LDAP_SERVER_HOST=ldap
LDAP_SEARCH_BASE=%s
LDAP_BIND_DN=cn=MAIL-BIND,ou=Service,ou=Accounts,%s
LDAP_BIND_PW=%s 
LDAP_QUERY_FILTER_USER=(&(mail=%%s)(mailEnabled=TRUE))
LDAP_QUERY_FILTER_GROUP=(&(mailGroupMember=%%s)(mailEnabled=TRUE))
LDAP_QUERY_FILTER_ALIAS=(|(&(mailAlias=%%s)(objectClass=PostfixBookMailForward))(&(mailAlias=%%s)(objectClass=PostfixBookMailAccount)(mailEnabled=TRUE)))
LDAP_QUERY_FILTER_DOMAIN=(|(&(mail=*@%%s)(objectClass=PostfixBookMailAccount)(mailEnabled=TRUE))(&(mailGroupMember=*@%%s)(objectClass=PostfixBookMailAccount)(mailEnabled=TRUE))(&(mailalias=*@%%s)(objectClass=PostfixBookMailForward)))
DOVECOT_PASS_FILTER=(&(objectClass=PostfixBookMailAccount)(mail=%%u))
DOVECOT_USER_FILTER=(&(objectClass=PostfixBookMailAccount)(uid=%%n))
ENABLE_SASLAUTHD=1
SASLAUTHD_MECHANISMS=ldap
SASLAUTHD_LDAP_SERVER=ldap
SASLAUTHD_LDAP_BIND_DN=cn=MAIL-BIND,ou=Service,ou=Accounts,%s
SASLAUTHD_LDAP_PASSWORD=%s
SASLAUTHD_LDAP_SEARCH_BASE=%s
SASLAUTHD_LDAP_FILTER=(&(objectClass=PostfixBookMailAccount)(uid=%%U))
POSTMASTER_ADDRESS=itsupport@%s
POSTFIX_MESSAGE_SIZE_LIMIT=100000000
OVERRIDE_HOSTNAME=%s
DOVECOT_PASS_ATTRS=uid=user,userPassword=password
DOVECOT_USER_ATTRS==uid=5000,=gid=5000,=home=/var/mail/%%Ln,=mail=maildir:~/Maildir
DOVECOT_AUTH_BIND=yes
""" % (base_dn, base_dn, ldap_pass, base_dn, ldap_pass, base_dn, domain, domain)

def authConf():
    return """
disable_plaintext_auth = no

auth_mechanisms = plain login oauthbearer xoauth2

ssl_client_require_valid_cert=no

service auth {
  unix_listener /var/spool/postfix/private/auth {
    mode = 0660
    # Assuming the default Postfix user and group
    user = postfix
    group = postfix
  }
}

passdb {
    driver = oauth2
    mechanisms = xoauth2 oauthbearer
    args = /etc/dovecot/conf.d/auth-oauth2.conf.ext
}

!include auth-ldap.conf.ext
"""

def postfixMain():
    return """
smtpd_sasl_type = dovecot
smtpd_sasl_auth_enable = yes
smtpd_sasl_path = private/auth
smtpd_relay_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination
"""

def webmailOAuth(domain, client_id, client_secret):
  return """<?php
$config['oauth_provider'] = 'generic';
$config['oauth_provider_name'] = 'SSO';
$config['oauth_client_id'] = '%s';
$config['oauth_client_secret'] = '%s';
$config['oauth_auth_uri'] = 'https://sso.%s/application/o/authorize/';
$config['oauth_token_uri'] = 'https://sso-server:9443/application/o/token/';
$config['oauth_identity_uri'] = 'https://sso-server:9443/application/o/userinfo/';
$config['oauth_login_redirect'] = true;
$config['oauth_verify_peer'] = false;
$config['oauth_scope'] = "email profile openid";
$config['assets_path'] = "/";
""" % (client_id, client_secret, domain)


def dovecotOAuth(domain, client_id, client_secret):
    return """
tokeninfo_url = https://sso.%s/application/o/userinfo/?access_token=

introspection_url = https://%s:%s@sso.%s/application/o/introspect/
introspection_mode = post

# debug = yes

tls_allow_invalid_cert=yes
""" % (domain, client_id, client_secret, domain)