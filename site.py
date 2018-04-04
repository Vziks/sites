# -*- coding: utf-8 -*-

import re, os, sys, io, argparse, string, random
import mysql.connector
from mysql.connector import errorcode

config = {
    'user': 'root',
    'password': '123',
    'host': '127.0.0.1',
    'raise_on_warnings': True
}


def pw_gen(size=8, chars=string.ascii_letters + string.digits + '!@#$%^&*()_+'):
    return ''.join(random.choice(chars) for _ in range(size))


CONST_DOMAIN = "%s.demo.isobar.ru"
CONST_NGINX = "/etc/nginx/sites-available/"
CONST_PHP = ['55', '56', '70', '71']

dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'


def create_database(cursor, dbname, domain):
    try:
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET 'utf8'".format(dbname))
        print ('Создал БД: %s' % dbname)

        password = pw_gen(25)
        username = dbname.replace('mb_', 'mu_')

        cursor.execute(
            "CREATE USER IF NOT EXISTS '{}'@'localhost' IDENTIFIED BY '{}'".format(username, password))

        print ('Создал пользователя: %s' % username)
        print ('Пароль пользователя: %s' % password)

        cursor.execute(
            "GRANT ALL PRIVILEGES ON {}.* TO '{}'@'localhost'".format(dbname, username))

        print ('Выдал привилегии пользователю %s на бд %s' % (username, dbname))

        cursor.execute("FLUSH PRIVILEGES")

        if not os.path.exists(dir_path + 'sites/' + domain + '/public/mysql.txt'):
            config = io.open(dir_path + 'sites/' + domain + '/public/mysql.txt', 'w')
            for line in io.open('mysqltem.txt', 'r'):
                line = line.replace('$dbname', dbname)
                line = line.replace('$muser', username)
                line = line.replace('$password', password)
                config.write(line)
            config.close()

        print ('Записал в файл - %s' % dir_path + 'sites/' + domain + '/public/mysql.txt')

    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)


def create_simlink(domain):
    src = CONST_NGINX + domain + '.conf'
    if not os.path.exists(src):
        dst = dir_path + 'sites/' + domain + '/conf/nginx.conf'
        os.symlink(dst, src)
        print ('Симлинк создан')
    else:
        print ('Симлинк уже существует')


def set_php(domain, phpversion):
    if not os.path.exists(dir_path + 'sites/' + domain + '/conf/nginx.conf'):
        config = io.open(dir_path + 'sites/' + domain + '/conf/nginx.conf', 'w')
        for line in io.open('template.conf', 'r'):
            line = line.replace('$domain', domain)
            line = line.replace('$phpversion', 'php' + phpversion)
            config.write(line)
        config.close()
        print ('Nginx конфиг %s' % dir_path + 'sites/' + domain + '/conf/nginx.conf')
    else:
        print ('Nginx.conf существует, пропущен')


def create_domain(domen):
    domenname = CONST_DOMAIN % (domen)

    if not os.path.exists(domenname):
        list = [domenname, domenname + '/conf', domenname + '/logs', domenname + '/private', domenname + '/public']
        i = 0
        while i < len(list):
            if not os.path.exists(dir_path + 'sites/' + list[i]):
                os.makedirs(dir_path + 'sites/' + list[i])
                os.chmod(dir_path + 'sites/' + list[i], 0755)
            i += 1
        print ('Структура папок создана')
    else:
        print ('Домен существует пропущен')

    return domenname


def restartable(func):
    def wrapper(domain):
        answer = 'y'
        while answer == 'y':
            while True:
                answer = str(raw_input('Версия PHP: 5.5/5.6/7.0/7.1:'))
                print (answer)
                if answer in ('71', '7.1'):
                    set_php(domain, '71')
                    break
                elif answer in ('70', '7.0'):
                    set_php(domain, '70')
                    break
                elif answer in ('56', '5.6'):
                    set_php(domain, '56')
                    break
                elif answer in ('55', '5.5'):
                    set_php(domain, '55')
                    break
                else:
                    print ("invalid answer")

    return wrapper


def checkdomain(func):
    def wrapper():
        regcheck = True
        while regcheck:
            while regcheck:
                domen = raw_input('Доменное имя:')
                if not bool(re.search('[а-яА-Я]', domen)):
                    regcheck = False
                    return create_domain(domen)
                else:
                    print ('Не используйте киррилицу')

    return wrapper


if len(sys.argv) > 1:
    ret = create_domain(sys.argv[1])
    try:
        if sys.argv[2] and sys.argv[2] in CONST_PHP:
            set_php(ret, sys.argv[2])
        else:
            @restartable
            def main():
                print()


            main(ret)
    except IndexError as e:
        @restartable
        def main():
            print()


        main(ret)

else:
    @checkdomain
    def check():
        print()


    ret = check()


    @restartable
    def main():
        print()


    main(ret)

mysqlname = ret.split(".")[:1]
dbname = 'mb_' + mysqlname[0]

cnx = mysql.connector.connect(**config)
cursor = cnx.cursor()
try:
    cnx.database = dbname
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor, dbname, ret)
        cnx.database = dbname
    else:
        print(err)
        exit(1)

create_simlink(ret)
