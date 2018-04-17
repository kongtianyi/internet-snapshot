# -*- coding: utf-8 -*-

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


class TraversalPipeline(object):
    def __init__(self):
        self.sql = "INSERT INTO traversal (url, status, refer, depth, get_time, inner_chains_num) " \
                   "VALUES (%s, %s, %s, %s, %s, %s)"

    def process_item(self, item, spider):
        connection = pymysql.connect(**mysql_config)
        with connection.cursor() as cursor:
            cursor.execute(self.sql, item.save_tuple())
        connection.commit()
        connection.close()


