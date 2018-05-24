# -*- encoding: utf-8 -*-

import pymysql


mysql_config = {
    'host': '120.79.178.39',
    'port': 3306,
    'user': 'root',
    'password': 'KONG64530322931',
    'db': 'internet_snapshot',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

REDIS_URL = "redis://:kongtianyideredis@114.67.225.0:6379/0"

