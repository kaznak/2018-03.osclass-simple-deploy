# -*- coding: utf-8 -*-

from fabric.api import run
from fabric.api import sudo
from fabric.utils import puts
from fabric.operations import reboot
from fabric.operations import put
from fabric.context_managers import cd

from fabric import network
from fabric.state import connections

from fabric.colors import red, green
from fabric.context_managers import *

import os
import cuisine

############################################################
cuisine.select_package('yum')

IP_ADDR = env.IP_ADDR

'''
+ setup : total setup function
  + update_system : system update function
+ redeploy_osclass : osclass redeployment function
'''

############################################################
def setup():
    setup_repository()
    setup_selinux()
    # update_system()
    install_packages()
    install_osclass()
    setup_apache()
    setup_mariadb()

############################################################
def setup_repository(): # setup yum and repositoies
    for pkg in [
            'yum-utils',
            'epel-release',
            ('remi-release', 'http://rpms.remirepo.net/enterprise/remi-release-7.rpm')
    ]:
        sudo('''
        yum list installed | grep -q '^%s\.'	||
        yum install -y %s
        '''.strip() % (pkg if type(pkg) == tuple else (pkg, pkg)))

    # Use Remi's RPM repository
    # # http://rpms.famillecollet.com/
    sudo('yum-config-manager --enable remi-php72')

def setup_selinux():
    sudo("sed -i '/^[[:space:]]*SELINUX=/s/SELINUX=.*$/SELINUX=permissive/' /etc/selinux/config")
    sudo('setenforce Permissive')

def update_system():
    cuisine.package_upgrade()
    reboot(command='shutdown -r +0')

def install_packages(): # install packages
    for pkg in [
            # basic packages
            # # following sequence require
            'expect', 'unzip',  # 'wget',
            # # useful
            'git', 'screen', 'patch',
            # # debug
            'gdb', 'strace', 'lsof',

            # PHP related packages
            # # osclass require
            # # # install.php says
            'php', 'php-gd', 'php-mysqlnd',
            # # # and other requirements
            'php-mbstring', 'php-mcrypt',
            'php-curl',
            'php-ldap',
            'php-zip', 'php-fileinfo',
            'php-xml', 'php-xmlrpc',
            # # debug
            'php-cli',
            # Servers and DBs
            'httpd',
            'mariadb', 'mariadb-server',
    ]:
        cuisine.package_ensure(pkg)

def install_osclass():
    run('''
[ -e osclass.3.7.4.zip ] ||
curl -O https://static.osclass.org/download/osclass.3.7.4.zip
    '''.strip())
    sudo('mkdir -p /var/www/html/osclass')
    sudo('''
[ -s /var/www/html/osclass/index.php ] ||
unzip /home/centos/osclass.3.7.4.zip -d /var/www/html/osclass
    '''.strip())
    sudo('chown -R apache:apache /var/www/html/osclass')

def setup_apache():
    sudo("sed -i '/^[[:space:]]*DocumentRoot[[:space:]]/s%DocumentRoot.*$%DocumentRoot \"/var/www/html/osclass\"%' /etc/httpd/conf/httpd.conf")
    sudo('systemctl restart httpd')
    sudo('systemctl enable httpd')

def setup_mariadb():
    sudo('systemctl restart mariadb')
    sudo('systemctl enable mariadb')
    sudo('''
expect	<<"EOF"
spawn mysql_secure_installation

expect "Enter current password for root"
send "\\n"

expect {
	"Access denied"	{ send "password\\n" ; exp_continue }
    	"Set root password?"		{ send "y\\n" }
	"Change the root password?"	{ send "y\\n" }
}
expect "New password:"
send "password\\n"
expect "Re-enter new password:"
send "password\\n"

expect "Remove anonymous users?"
send "y\\n"
expect "Disallow root login remotely?"
send "y\\n"
expect "Remove test database and access to it?"
send "y\\n"
expect "Reload privilege tables now?"
send "y\\n"
EOF
    '''.strip())
    run('''
expect	<<"EOF"
spawn mysql --user=root --password=password
expect ">"
send "CREATE DATABASE osclass;\\n"

expect ">"
send "CREATE USER 'osclass'@'localhost' IDENTIFIED BY 'password';\\n"
expect ">"
send "GRANT ALL PRIVILEGES ON `osclass`.* TO 'osclass'@'localhost';\\n"
expect ">"
send "FLUSH PRIVILEGES;\\n"
expect ">"
send "\\q"

EOF
    '''.strip())

############################################################
def setup_osclass():
    sudo('''
crontab	<<EOF
0 * * * * /usr/bin/php /var/www/html/osclass/index.php -p cron -t hourly
0 0 * * * /usr/bin/php /var/www/html/osclass/index.php -p cron -t daily
0 0 * * 0 /usr/bin/php /var/www/html/osclass/index.php -p cron -t weekly
EOF
    '''.strip(),
         user='apache' )
    sudo('/usr/bin/php /var/www/html/osclass/index.php -p cron -t hourly',
         user='apache' )
    sudo('/usr/bin/php /var/www/html/osclass/index.php -p cron -t daily',
         user='apache' )
    sudo('/usr/bin/php /var/www/html/osclass/index.php -p cron -t weekly',
         user='apache' )

def setup_selinux_permissive():
    sudo("sed -i '/^[[:space:]]*SELINUX=/s/SELINUX=.*$/SELINUX=permissive/' /etc/selinux/config")
    sudo('setenforce Permissive')

def setup_selinux_enforcing():
    sudo("sed -i '/^[[:space:]]*SELINUX=/s/SELINUX=.*$/SELINUX=enforcing/' /etc/selinux/config")
    sudo('setenforce Enforcing')
    
############################################################
def redeploy_osclass():
    run('curl -O https://static.osclass.org/download/osclass.3.7.4.zip')
    sudo('rm -rf /var/www/html/osclass')
    sudo('mkdir -p /var/www/html/osclass')
    sudo('unzip /home/centos/osclass.3.7.4.zip -d /var/www/html/osclass')
    sudo('chown -R apache:apache /var/www/html/osclass')
    run('''
expect	<<"EOF"
spawn mysql --user=root --password=password
expect ">"
send "DROP DATABASE osclass;\\n"
expect ">"
send "CREATE DATABASE osclass;\\n"

expect ">"
send "CREATE USER 'osclass'@'localhost' IDENTIFIED BY 'password';\\n"
expect ">"
send "GRANT ALL PRIVILEGES ON `osclass`.* TO 'osclass'@'localhost';\\n"
expect ">"
send "FLUSH PRIVILEGES;\\n"
expect ">"
send "\\q"
EOF
    '''.strip())
