import os
from contextlib import contextmanager

import pymysql
from redis import Redis

JWT_SECRET = os.getenv('JWT_SECRET', 'studio-local-demo-replace-before-deployment-x8fc3d')
cache = Redis(host=os.getenv('REDIS_HOST', 'redis'), socket_timeout=2, socket_connect_timeout=2)


@contextmanager
def database():
    connection = pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'db'), port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'studio'), password=os.getenv('MYSQL_PASSWORD', 'studio_local_dev'),
        database=os.getenv('MYSQL_DATABASE', 'studio_noise'), charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor, connect_timeout=3,
        init_command="SET time_zone = '+08:00'",
    )
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
