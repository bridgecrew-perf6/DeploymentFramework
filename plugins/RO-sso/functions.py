def dockerFile(image, tag):
    return """
  sso-server:
    image: %s:%s
    restart: unless-stopped
    command: server
    volumes:
      - ./storage/sso/media:/media
      - ./storage/sso/custom-templates:/templates
      #- geoip:/geoip
    env_file:
      - ./envs/sso.env
    depends_on:
      - ldap
      - postgresql
    # ports:
    #   - "0.0.0.0:9000:9000"
    #   - "0.0.0.0:9443:9443"
  
  sso-worker:
    image: %s:%s
    restart: unless-stopped
    command: worker
    # This is optional, and can be removed. If you remove this, the following will happen
    # - The permissions for the /backups and /media folders aren't fixed, so make sure they are 1000:1000
    # - The docker socket can't be accessed anymore
    user: root
    volumes:
      - ./storage/sso/backups:/backups
      - ./storage/sso/media:/media
      - ./storage/sso/custom-templates:/templates
      - /var/run/docker.sock:/var/run/docker.sock
      #- geoip:/geoip
    env_file:
      - ./envs/sso.env
    depends_on:
      - sso-server
""" % (image, tag, image, tag)

def envFile(secret_key, admin_pass, admin_token, db_user, db_name, db_pass):
    from core.models.Module import Module
    from core.models.Settings import Settings
    RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
    domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
    return """
AUTHENTIK_SECRET_KEY=%s
AK_ADMIN_PASS=%s
AK_ADMIN_TOKEN=%s

# Connection Information
AUTHENTIK_REDIS__HOST=redis
AUTHENTIK_POSTGRESQL__HOST=postgresql
AUTHENTIK_POSTGRESQL__USER=%s
AUTHENTIK_POSTGRESQL__NAME=%s
AUTHENTIK_POSTGRESQL__PASSWORD=%s

# SMTP Host Emails are sent to
AUTHENTIK_EMAIL__HOST=mailserver
AUTHENTIK_EMAIL__PORT=25
# Optionally authenticate (don't add quotation marks to you password)
AUTHENTIK_EMAIL__USERNAME=
AUTHENTIK_EMAIL__PASSWORD=
AUTHENTIK_EMAIL__USE_TLS=TRUE
AUTHENTIK_EMAIL__USE_SSL=false
AUTHENTIK_EMAIL__TIMEOUT=10
# Email address authentik will send from, should have a correct @domain
AUTHENTIK_EMAIL__FROM=sso@%s
""" % (secret_key, admin_pass, admin_token, db_user, db_name, db_pass, domain)

def getLDAPGroups(domain, token):
    import requests, time
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    for x in range(20):
        try:
            url = "https://sso.%s/api/v3/propertymappings/ldap" % domain
            r = requests.get(url, headers={'Authorization': "Bearer %s" % token}, verify=False)
            if r.status_code == 200:
                # print("200")
                response = r.json()

                mappings = response['results']
                mapIDS = []
                for map in mappings:
                    if "LDAP Mapping" in map['name']:
                        mapIDS.append(map['pk'])
                return mapIDS
            else:
                # print("NON-200")
                # print(r)
                time.sleep(5)
        except Exception as e:
            # print("LDAP GROUPS - EXCEPTION")
            time.sleep(5)
    print(r)
    print("Error... Exiting...")
    exit()

def configureLDAPSource(domain, token, base_dn, bind_pass):
    import requests, time
    groups = getLDAPGroups(domain, token)
    jsondata = {
        "name": "LDAP Source",
        "slug": "ldap-source",
        "enabled": True,
        # "authentication_flow": "17db1e5b-5450-4000-8d41-86f5c8db4f01",
        # "enrollment_flow": "17db1e5b-5450-4000-8059-09e3d05c2601",
        # "policy_engine_mode": "all",
        # "user_matching_mode": "identifier",
        "server_uri": "ldap://ldap",
        # "peer_certificate": "17db1e5b-5450-4000-8238-173e8e33c301",
        "bind_cn": "cn=SSO-BIND,ou=Service,ou=Accounts,%s" % base_dn,
        "bind_password": bind_pass,
        "start_tls": True,
        "base_dn": base_dn,
        # "additional_user_dn": "string",
        # "additional_group_dn": "string",
        "user_object_filter": "(objectClass=inetOrgPerson)",
        "group_object_filter": "(objectClass=groupOfNames)",
        "group_membership_field": "member",
        "object_uniqueness_field": "cn",
        "sync_users": True,
        "sync_users_password": True,
        "sync_groups": True,
        # "sync_parent_group": "17db1e5b-5450-4000-8716-ba7011568201",
        "property_mappings": groups,
        "property_mappings_group": groups
    }
    for x in range(10):
        try:
            r = requests.post('https://sso.%s/api/v3/sources/ldap/' % domain, json=jsondata, headers={'Authorization': "Bearer %s" % token}, verify=False)
            status = r.status_code
            if status != 201:
                #print(r.json())
                time.sleep(10)
            else:
                print("syncing...")
                r = requests.patch('https://sso.%s/api/v3/sources/ldap/ldap-source'% domain, headers={'Authorization': "Bearer %s" % token}, verify=False)
                r = requests.patch('https://sso.%s/api/v3/sources/ldap/ldap-source'% domain, headers={'Authorization': "Bearer %s" % token}, verify=False)
                r = requests.patch('https://sso.%s/api/v3/sources/ldap/ldap-source'% domain, headers={'Authorization': "Bearer %s" % token}, verify=False)
                break
        except Exception as e:
            #print("Exception")
            time.sleep(10)

def makeGroupAdmins(domain, token, groupName):
  import requests
  data = {
    "name": groupName
  }
  r = requests.get('https://sso.%s/api/v3/core/groups'% domain, params=data, headers={'Authorization': "Bearer %s" % token}, verify=False)
  if r.status_code != 200:
    print("Unable To Search For Group")
    exit()
  
  for group in r.json()['results']:
    data = {
      'is_superuser': True
    }
    r = requests.patch('https://sso.%s/api/v3/core/groups/%s/'% (domain, group['pk']), json=data, headers={'Authorization': "Bearer %s" % token}, verify=False)
    if r.status_code != 200:
      print("Unable Make Group an Admin")
      print(r.status_code)
      print(r.text)
      exit()