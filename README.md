
# osclass simple deployment scripts on AWS

+ [osclass](https://osclass.org/)

## Usage

Before use, you have to change password of database in server-res/setup.py.

!CAUTION! All of below operations will erase DB contents!

### Totally new
~~~
echo yes|sh/terraform apply && sh/provision setup_nginx
cat	<<EOF
1. setup osclass from browser by hands
2. disable osclass built-in cron
   from admin panel -> settings -> general -> Automatic cron process.
EOF
sh/provision setup_nginx setup_osclass
~~~

### reload EC2
~~~
sh/reload-ec2 && sh/provision setup_nginx
~~~

### reload osclass

~~~
sh/provision  setup_nginx redeploy_osclass
~~~

## Future Works
### SELinux

Now it is set to permissive, but it should be enforcing.

### osclass built-in cron

I disabled osclass built-in cron feature to resolve performance issue
according to below post and the link.

+ [Topic: Very slow [Solved]  (Read 2501 times)](https://forums.osclass.org/3-5-x/very-slow/)
> - you site is fast enough now (for me)
> - disable built-in cron feature and create cron job on cron server (http://doc.osclass.org/Cron)
> 
> Reason why it might be slow using this feature is:
> - when you access your web just once a day, all daily crons are run when y> ou visit your site (when you acessing, you wait till cron functions are run)
> - same when you have hourly cron functions

+ [Cron](http://doc.osclass.org/Cron)

But I don't understand the precise difference between the 2 settings.
It should be investigated.
