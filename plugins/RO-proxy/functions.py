def dockerFile():
    return """
  proxy:
    image: 'jc21/nginx-proxy-manager:latest'
    restart: unless-stopped
    ports:
      # These ports are in format <public-port>:<container-port>
      - '80:80' # Public HTTP Port
      - '443:443' # Public HTTPS Port
      - '81:81' # Admin Web Port
    volumes:
      - ./storage/proxy/data:/data
      - ./storage/proxy/letsencrypt:/etc/letsencrypt
    env_file:
      - ./envs/proxy.env
    depends_on:
      - mariadb
"""

def envFile(mysql_database, mysql_user, mysql_pass):
    return """DB_MYSQL_HOST=mariadb
DB_MYSQL_PORT=3306
DB_MYSQL_USER=%s
DB_MYSQL_PASSWORD=%s
DB_MYSQL_NAME=%s
""" % (mysql_user, mysql_pass, mysql_database)

def getToken(user_name, user_password):
    import requests, time
    token = None
    print("Getting Proxy API Token...", end="", flush=True)
    attempt = 0
    while token is None and attempt < 20:
        try:
          jsondata = {"identity": user_name, "secret": user_password}
          r = requests.post('http://127.0.0.1:81/api/tokens', json=jsondata)
          if r.status_code == 200:
              response = r.json()
              return response['token']
          else:
              print(".", end="", flush=True)
              time.sleep(2)
        except:
          time.sleep(2)
        attempt+=1
    
    return None