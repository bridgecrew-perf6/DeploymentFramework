def dockerFile():
    return """
  phpldapadmin:
    image: osixia/phpldapadmin:latest
    volumes:
      - ./storage/ldap-admin/phpldapadmin:/var/www/phpldapadmin
    environment:
      - PHPLDAPADMIN_LDAP_HOSTS=ldap
"""