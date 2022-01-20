def dockerFile():
    return """
  phpmyadmin:
    restart: unless-stopped
    image: bitnami/phpmyadmin:latest
    environment:
        DATABASE_HOST: mariadb
"""