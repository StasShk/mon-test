# -*- coding: utf-8 -*-

from __future__ import with_statement
from os import environ
from StringIO import StringIO
from fabric.api import *
from fabric.contrib.files import sed
from config import nginx_config


env.colorize_errors = 'true'
key_filename = "~/.ssh/id_rsa"
db_name = 'wordpress'
db_user = 'wordpressuser'
db_pass = '12345'
db_root_pass = '12Nbwe7v2jkK291bk21e4v'  #MySQL root password

site_name = 'wp-test.ru'
env.work_dir = '/var/www/html'


def add_ssh_key(identity=key_filename+'.pub'):
    REMOTE_PATH = '~/id.pub'
    put(identity, REMOTE_PATH)

    with cd('~'):
        run('mkdir -p .ssh')
        run('cat %(REMOTE_PATH)s >> ~/.ssh/authorized_keys' % locals())
        run('rm %(REMOTE_PATH)s' % locals())

    env.key_filename = key_filename
    
    
def key_auth_only():
    sed('/etc/ssh/sshd_config',
        '#PasswordAuthentication yes',
        'PasswordAuthentication no',
        use_sudo=True)

    sed('/etc/ssh/sshd_config',
        'PermitRootLogin yes',
        'PermitRootLogin no',
        use_sudo=True)

    sudo("systemctl reload sshd")


def user_create():
    if env.user== 'root':
        env.user = environ['USER']
        run('adduser ' + environ['USER'] )
        run('usermod -aG sudo ' + environ['USER'])
        
    with settings(user=environ['USER']):
        add_ssh_key()
        
        key_auth_only()
        

def install_mariadb():

    sudo("DEBIAN_FRONTEND=noninteractive apt-get -y --no-upgrade install mariadb-server", shell=False)
    dbcreatestr = "CREATE DATABASE {0} DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;".format(db_name)
    dbgrantstr = "GRANT ALL ON {0}.* TO '{1}'@'localhost' IDENTIFIED BY '{2}';".format(db_name, db_user, db_pass)
    
    sudo('mysql --default-character-set=utf8 -u%s -e "%s"' % (
        'root',
        dbcreatestr,
        ))
        
    sudo('mysql --default-character-set=utf8 -u%s -e "%s"' % (
        'root',
        dbgrantstr,
        ))
        
    sudo('mysql --default-character-set=utf8 -u%s -e "%s"' % (
        'root',
        "FLUSH PRIVILEGES;",
        ))
        
        
def install_nginx():
    sudo("apt-get -y -q install nginx")
    
    config = nginx_config.format(env.hosts)
    
    with cd('/etc/nginx/sites-available/'):
        with settings(warn_only=True):
            if (put(StringIO(config), site_name, use_sudo=True)).failed:
                pass

    with cd('/etc/nginx/sites-enabled'):
        with settings(warn_only=True):
            sudo('rm /etc/nginx/sites-enabled/default')
            if (sudo("ln -s /etc/nginx/sites-available/" + site_name)).failed:
                pass
    


def install_php():
    sudo("apt-get -y -q install php-fpm php-mysql php-curl php-gd php-mbstring php-mcrypt php-xml php-xmlrpc")
    sed('/etc/php/7.0/fpm/php.ini',
        ';cgi.fix_pathinfo=1',
        'cgi.fix_pathinfo=0',
        use_sudo=True)
    sudo('systemctl restart php7.0-fpm')
    

    
def install_wp():
    with cd('/tmp'):
        run('curl -O https://wordpress.org/latest.tar.gz')
        run('tar xzvf latest.tar.gz')
        run('cp /tmp/wordpress/wp-config-sample.php /tmp/wordpress/wp-config.php')
        run('mkdir /tmp/wordpress/wp-content/upgrade')
        sed('/tmp/wordpress/wp-config.php',
            before="database_name_here",
            after=db_name)
        sed('/tmp/wordpress/wp-config.php',
            "username_here",
           db_user)
        sed('/tmp/wordpress/wp-config.php',
            'password_here',
            db_pass) 
        
    sudo('cp -a /tmp/wordpress/. /var/www/html')
    sudo('chown -R www-data:www-data /var/www/')
    sudo('chmod -R g+w /var/www/html/wp-content/themes')
    sudo('chmod -R g+w /var/www/html/wp-content/plugins')

@task          
def restart_all():
    sudo('service nginx restart')
    sudo('service php7.0-fpm restart')
    sudo('service mysql restart')
    
@task   
def deploy(servername='192.168.122.203', username='stas'):
    
    user_create()
    with settings(user=env.user):
        install_mariadb()
        install_nginx()
        install_php()
        install_wp()
        restart_all()
