def dockerFile():
    return """
  redis:
    image: redis:alpine
    restart: unless-stopped
"""