def dockerFile():
    return """
  phoneserver:
    container_name: phoneserver
    image: tiredofit/freepbx:latest
    ports:
      - 5060:5060/udp
      - 5160:5160/udp
      - 18000-18100:18000-18100/udp
    #  #### Flash Operator Panel
      - 4445:4445
      - 8088:8088
      - 8089:8089
    volumes:
      - ./storage/phoneserver/certs:/certs
      - ./storage/phoneserver/data:/data
      - ./storage/phoneserver/logs:/var/log
      - ./storage/phoneserver/data/www:/var/www/html
      - ./storage/phoneserver/assets:/assets/custom
    env_file:
      ./envs/phoneserver.env
    restart: always
    ### These final lines are for Fail2ban. If you don't want, comment and also add ENABLE_FAIL2BAN=FALSE to your environment
    cap_add:
      - NET_ADMIN
    privileged: true
"""

def envFile(db_name, db_user, db_pass):
  return """
DB_HOST=mariadb
DB_PORT=3306
DB_NAME=%s
DB_USER=%s
DB_PASS=%s
ENABLE_FAIL2BAN=TRUE
ENABLE_FOP=TRUE
RTP_START=18000
RTP_FINISH=18100
DB_EMBEDDED=FALSE
ENABLE_XMPP=TRUE
""" % (db_name, db_user, db_pass)