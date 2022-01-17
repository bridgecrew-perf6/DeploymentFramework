def dockerFile():
    return """
  phpldapadmin:
    image: osixia/phpldapadmin:latest
    volumes:
      - ./storage/ldap-admin:/var/www/phpldapadmin
      - ./init/ldap-admin/config.php:/container/service/phpldapadmin/assets/config/config.php
      - ./init/ldap-admin/templates:/var/www/phpldapadmin_bootstrap/templates/creation
      - ./init/ldap-admin/templates:/var/www/phpldapadmin_bootstrap/templates/modification
    environment:
      - PHPLDAPADMIN_LDAP_HOSTS=ldap
"""

def configFile(bind_id, bind_pass):
  return """<?php

$config->custom->debug['level'] = 0;
$config->custom->debug['syslog'] = true;

$config->custom->jpeg['tmpdir'] = '/var/www/tmp';

$config->custom->appearance['hide_template_warning'] = true;
$config->custom->appearance['custom_templates_only'] = true;
$config->custom->appearance['disable_default_template'] = false;


$config->custom->appearance['friendly_attrs'] = array(
        'facsimileTelephoneNumber' => 'Fax',
        'gid'                      => 'Group',
        'mail'                     => 'Email',
        'telephoneNumber'          => 'Extension',
        'uid'                      => 'User Name',
        'userPassword'             => 'Password'
);


$servers = new Datastore();

$servers->newServer('ldap_pla');
$servers->setValue('server','name','ldap');
$servers->setValue('server','host','ldap');

$servers->setValue('proxy','attr',array('mail'=>'HTTP_X_AUTHENTIK_EMAIL'));
$servers->setValue('login','auth_type','proxy');

$servers->setValue('login','bind_id','%s');
$servers->setValue('login','bind_pass', '%s');
""" % (bind_id, bind_pass)

def getAdvanceConfig():
  return """proxy_buffers 8 16k;
proxy_buffer_size 32k;
fastcgi_buffers 16 16k;
fastcgi_buffer_size 32k;

location / {
    proxy_pass          $forward_scheme://$server:$port;

    auth_request        /akprox/auth/nginx;
    error_page          401 = @akprox_signin;

    auth_request_set $authentik_username $upstream_http_x_authentik_username;
    auth_request_set $authentik_groups $upstream_http_x_authentik_groups;
    auth_request_set $authentik_email $upstream_http_x_authentik_email;
    auth_request_set $authentik_name $upstream_http_x_authentik_name;
    auth_request_set $authentik_uid $upstream_http_x_authentik_uid;

    proxy_set_header X-authentik-username $authentik_username;
    proxy_set_header X-authentik-groups $authentik_groups;
    proxy_set_header X-authentik-email $authentik_email;
    proxy_set_header X-authentik-name $authentik_name;
    proxy_set_header X-authentik-uid $authentik_uid;
}

location /akprox {
    proxy_pass          https://sso-server:9443/akprox;
    proxy_set_header    Host $host;
    add_header          Set-Cookie $auth_cookie;
    auth_request_set    $auth_cookie $upstream_http_set_cookie;
}

location @akprox_signin {
    internal;
    add_header Set-Cookie $auth_cookie;
    return 302 /akprox/start?rd=$request_uri;
}"""

def UserTemplate(domain):
      return """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE template SYSTEM "template.dtd">

<template>
  <description>New User Account</description>
  <title>User Account</title>
  <rdn>cn</rdn>
  <visible>1</visible>
  <icon>ldap-user.png</icon>
  <regexp>^ou=User,ou=Accounts.*,</regexp>

  <objectClasses>
    <objectClass id="posixAccount"></objectClass>
    <objectClass id="inetOrgPerson"></objectClass>
    <objectClass id="PostfixBookMailAccount"></objectClass>
  </objectClasses>

  <attributes>
    <attribute id="givenName">
      <display>First Name</display>
      <onchange>=autoFill(cn;%%givenName%% %%sn%)</onchange>
      <onchange>=autoFill(uid;%%givenName|0-1/l%%%%sn/l%)</onchange>
    </attribute>
    <attribute id="sn">
      <display>Last Name</display>
      <onchange>=autoFill(cn;%%givenName%% %%sn%)</onchange>
      <onchange>=autoFill(uid;%%givenName|0-1/l%%%%sn/l%)</onchange>
    </attribute>
    <attribute id="cn">
      <display>Common Name</display>
    </attribute>
    <attribute id="uid">
      <display>Username</display>
      <onchange>=autoFill(mail;%%uid%@%s)</onchange>
      <onchange>=autoFill(homeDirectory;/home/%%uid%/)</onchange>
    </attribute>
    <attribute id="mail">
      <display>Primay Email Address</display>
    </attribute>
    <attribute id="homeDirectory">
      <display>User Directory</display>
    </attribute>
    <attribute id="uidNumber">
      <display>User ID Number</display>
      <readonly>1</readonly>
      <value>=php.GetNextNumber(/;uidNumber)</value>
    </attribute>
    <attribute id="gidNumber">
      <display>Primary Group</display>
      <value><![CDATA[=php.PickList(/;(&(objectClass=groupOfNames));gidNumber;%%cn%;;;;cn)]]></value>
    </attribute>
    <attribute id="telephoneNumber">
      <display>Telephone Extension</display>
    </attribute>
  </attributes>
</template>""" % domain

def GroupTemplate():
  return """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE template SYSTEM "template.dtd">

<template>
  <description>New Security Group</description>
  <icon>ldap-ou.png</icon>
  <rdn>cn</rdn>
  <regexp>^ou=Security,ou=Groups.*,</regexp>
  <title>Security Group</title>
  <visible>1</visible>

  <objectClasses>
    <objectClass id="groupOfNames"></objectClass>
    <objectClass id="extensibleObject"></objectClass>
  </objectClasses>

  <attributes>
    <attribute id="cn">
      <display>Group Name</display>
    </attribute>
    <attribute id="gidNumber">
      <display>GID Number</display>
      <readonly>1</readonly>
      <value>=php.GetNextNumber(/;gidNumber)</value>
    </attribute>
    <attribute id="description">
      <display>Description</display>
    </attribute>
  </attributes>

</template>"""