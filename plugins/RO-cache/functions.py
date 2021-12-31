def dockerFile():
    return """
  cache:
    image: memcached:latest
    restart: unless-stopped
"""