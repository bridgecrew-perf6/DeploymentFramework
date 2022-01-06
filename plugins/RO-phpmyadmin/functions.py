def dockerFile():
    return """
  phpmyadmin:
    image: bitnami/phpmyadmin:latest
    environment:
        DATABASE_HOST: mariadb
"""