def dockerFile():
    return """
  vpn:
    build: ./docker/vpn
    ports:
      - 1194:1194/udp
    volumes:
      - ./storage/vpn/certs:/etc/openvpn/certs
      - ./init/vpn/ldap.conf:/etc/openvpn/auth/ldap.conf
      - ./init/vpn/server.conf:/etc/openvpn/server.conf
    cap_add:
      - NET_ADMIN
    restart: unless-stopped
"""
def dockerBuildFile():
  return """FROM ubuntu:latest

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install openvpn openvpn-auth-ldap openssl iptables python3 python3-pip -y && \
	pip3 install ldap3 && \
    mkdir /etc/openvpn/auth && \
    mkdir /etc/openvpn/certs

COPY startup.sh /opt/startup.sh
COPY http.py /opt/http.py

VOLUME /etc/openvpn
EXPOSE 1194/udp

CMD /bin/bash /opt/startup.sh
"""

def ldapFile(base_dn):
  return """
<LDAP>
	# LDAP server URL
	URL		ldap://ldap

	# Bind DN (If your LDAP server doesn't support anonymous binds)
	# BindDN		cn=...

	# Bind Password
	# Password	...

	# Network timeout (in seconds)
	Timeout		15

	# Enable Start TLS
	TLSEnable	no

	# Follow LDAP Referrals (anonymously)
	FollowReferrals yes

	# TLS CA Certificate File
	# TLSCACertFile	/usr/local/etc/ssl/ca.pem

	# TLS CA Certificate Directory
	# TLSCACertDir	/etc/ssl/certs

	# Client Certificate and key
	# If TLS client authentication is required
	# TLSCertFile	/usr/local/etc/ssl/client-cert.pem
	# TLSKeyFile	/usr/local/etc/ssl/client-key.pem

	# Cipher Suite
	# The defaults are usually fine here
	# TLSCipherSuite	ALL:!ADH:@STRENGTH
</LDAP>

<Authorization>
	# Base DN
	BaseDN		"%s"

	# User Search Filter
	SearchFilter	"(uid=%%u)"

	# Require Group Membership
	RequireGroup	false

	# Add non-group members to a PF table (disabled)
	#PFTable	ips_vpn_users

	# Uncomment and set to true to support OpenVPN Challenge/Response
	PasswordIsCR	false
	<Group>
		# Match full user DN if true, uid only if false
		RFC2307bis	false

		BaseDN		"ou=Security,ou=Groups,%s"
		SearchFilter	"(|(memberOf=cn=Administrators,ou=Security,ou=Groups,%s)(memberOf=cn=VPN Users,ou=Security,ou=Groups,%s))"
		MemberAttribute	uniqueMember
	</Group>
</Authorization>  
""" % (base_dn, base_dn, base_dn, base_dn)

def serverFile():
  return """
port 1194
proto udp
dev tun

ca /etc/openvpn/certs/ca.crt
cert /etc/openvpn/certs/server.crt
key /etc/openvpn/certs/server.key  # This file should be kept secret

dh /etc/openvpn/certs/dh2048.pem

topology subnet
server 172.25.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt

;push "route 192.168.10.0 255.255.255.0"
;push "route 192.168.20.0 255.255.255.0"

push "redirect-gateway local def1"
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"
client-to-client
keepalive 10 120

persist-key
persist-tun

status openvpn-status.log

verb 4

explicit-exit-notify 1

plugin /usr/lib/openvpn/openvpn-auth-ldap.so /etc/openvpn/auth/ldap.conf
"""

def startupFile():
  return """#!/bin/bash

if [ ! -f "/etc/openvpn/certs/dh2048.pem" ]; then
    openssl dhparam -out /etc/openvpn/certs/dh2048.pem 2048
fi

if [ ! -f "/etc/openvpn/certs/ca.crt" ]; then
    openssl genrsa -out /etc/openvpn/certs/ca.key 2048
    openssl req -x509 -new -nodes -key /etc/openvpn/certs/ca.key -sha256 -days 1825 -out /etc/openvpn/certs/ca.crt -subj '/CN=CA/O=Virtual Remote Office/C=US'
fi

if [ ! -f "/etc/openvpn/certs/server.crt" ]; then
    openssl genrsa -out /etc/openvpn/certs/server.key 2048
    openssl req -new -key /etc/openvpn/certs/server.key -out /etc/openvpn/certs/server.csr -subj '/CN=server/O=Virtual Remote Office/C=US'
    openssl x509 -req -in /etc/openvpn/certs/server.csr -CA /etc/openvpn/certs/ca.crt -CAkey /etc/openvpn/certs/ca.key -CAcreateserial -out /etc/openvpn/certs/server.crt -days 825 -sha256
fi

mkdir -p /dev/net
if [ ! -c /dev/net/tun ]; then
    mknod /dev/net/tun c 10 200
fi

iptables -t nat -A POSTROUTING -s 172.25.0.0/24 -o eth0 -j MASQUERADE

python3 /opt/http.py &

openvpn --config /etc/openvpn/server.conf --client-cert-not-required
"""

def httpScript():
	return """
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import base64
import ldap3
from ldap3.core.exceptions import LDAPException


def _ldap_login(username, password):
    try:
        with ldap3.Connection('ldap', user=username, password=password) as conn:
            print(conn.result["description"]) # "success" if bind is ok
            return True
    except LDAPException:
        print('Unable to connect to LDAP server')
        return True

class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_HEAD(self):
        logging.info("Head Request!")
        print("".encode())

    def do_GET(self):
        if '/rest/GetUserlogin?' in self.path:
            # Validate Autheorization
            print(self.headers['Authorization'])
            auth = base64.decodebytes(self.headers['Authorization'][6:].encode()).decode()
            username,password = auth.split(':',1)
            if not _ldap_login(username, password):
                self.send_response(401)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("Login Failed".encode())
                return
            
            self._set_response()
            with open('/etc/openvpn/certs/ca.crt') as f:
                cafile = f.read()
            self.wfile.write((\"\"\"client
dev tun
proto udp
auth-user-pass
remote %%s 1194  # Server settings
remote-cert-tls server
resolv-retry infinite
auth-nocache
persist-key
persist-tun
topology subnet
script-security 3 system
<ca>
%%s
</ca>\"\"\" % (self.headers['host'], cafile)).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=80):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)


    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
"""