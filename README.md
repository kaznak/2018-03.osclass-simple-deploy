
# osclass simple deployment scripts

+ [osclass](https://osclass.org/)

## Usage

Before use, you have to change password of database in server-res/setup.py.

### Totally new
~~~
echo yes|sh/terraform apply && sh/provision setup_nginx
cat	<<EOF
1. setup osclass from browser by hands
2. disable osclass built-in cron
   from adomin panel -> settings -> general -> Automatic cron process.
EOF
sh/provision setup_nginx setup_osclass
~~~

### reload EC2
~~~
sh/reload-ec2 && sh/provision setup_nginx
~~~

### reload osclass

!CAUTION! DB contents will be erased!

~~~
sh/provision  setup_nginx redeploy_osclass
~~~
