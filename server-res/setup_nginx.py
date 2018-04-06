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
    update_system()
    install_packages()
    install_osclass()
    setup_nginx()
    setup_mariadb()
    setup_phpfpm()

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
            'tcpdump', 'bind-utils',

            # PHP related packages
            # # osclass require
            # # # install.php says
            'php', 'php-gd', 'php-mysqlnd',
            # # osclass undocumented require
            'php-mbstring',
            # # # required?
            # 'php-mcrypt',
            # 'php-curl',
            # 'php-ldap',
            # 'php-zip', 'php-fileinfo',
            # 'php-xml', 'php-xmlrpc',

            # # debug
            'php-cli',

            # Servers and DBs
            'nginx',
            'mariadb', 'mariadb-server',
            'php-fpm',
    ]:
        cuisine.package_ensure(pkg)

    sudo('find /var/lib/php -user  apache | xargs -r chown nginx')
    sudo('find /var/lib/php -group apache | xargs -r chown :nginx')

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
    sudo('chown -R nginx:nginx /var/www/html/osclass')

def setup_nginx():
    sudo('''
cat	<<"EOF"	> /etc/nginx/conf.d/osclass_http.conf
server {
    listen  80;
    server_name %s;

    location / {
	root  /var/www/html/osclass;
	index  index.php index.html index.htm;
    }

    error_page 404 /404.html;
    location = /404.html {
	root /usr/share/nginx/html;
    }

    error_page  500 502 503 504  /50x.html;
    location = /50x.html {
	root /usr/share/nginx/html;
    }

    location ~ \.php$ {
	root		/var/www/html/osclass;
	fastcgi_pass	unix:/var/run/php-fpm.sock;
        fastcgi_index	index.php;
        fastcgi_param	SCRIPT_FILENAME   $document_root$fastcgi_script_name;
        include		fastcgi_params;
    }
}
EOF
    '''.strip() % IP_ADDR)
    sudo('systemctl restart nginx')
    sudo('systemctl enable nginx')

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

def setup_phpfpm():
    sudo('''
cat	<<"EOF"	> /etc/php-fpm.d/www.conf
[www]
listen = /var/run/php-fpm.sock
listen.owner = nginx
listen.group = nginx
listen.mode = 0660
user = nginx
group = nginx
pm = dynamic
pm.max_children = 50
pm.start_servers = 5
pm.min_spare_servers = 5
pm.max_spare_servers = 35
slowlog = /var/log/php-fpm/www-slow.log
php_admin_value[error_log] = /var/log/php-fpm/www-error.log
php_admin_flag[log_errors] = on
php_value[session.save_handler] = files
php_value[session.save_path] = /var/lib/php/session
EOF
'''.strip())
    sudo('mkdir -p /var/log/php-fpm')
    sudo('chown nginx:nginx /var/log/php-fpm')
    sudo('systemctl restart php-fpm')
    sudo('systemctl enable php-fpm')

############################################################
def setup_osclass():
    sudo('''
crontab	<<EOF
0 * * * * /usr/bin/php /var/www/html/osclass/index.php -p cron -t hourly
0 0 * * * /usr/bin/php /var/www/html/osclass/index.php -p cron -t daily
0 0 * * 0 /usr/bin/php /var/www/html/osclass/index.php -p cron -t weekly
EOF
    '''.strip(),
         user='nginx')
    sudo('/usr/bin/php /var/www/html/osclass/index.php -p cron -t hourly',
         user='nginx')
    sudo('/usr/bin/php /var/www/html/osclass/index.php -p cron -t daily',
         user='nginx')
    sudo('/usr/bin/php /var/www/html/osclass/index.php -p cron -t weekly',
         user='nginx')

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
    sudo('chown -R nginx:nginx /var/www/html/osclass')
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
