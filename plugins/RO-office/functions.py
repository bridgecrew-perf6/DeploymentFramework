def dockerFile():
    return """
  office:
    image: onlyoffice/documentserver:latest
    restart: always
    volumes:
      - ./storage/office/data:/var/www/onlyoffice/Data
      - ./storage/office/log:/var/log/onlyoffice
"""