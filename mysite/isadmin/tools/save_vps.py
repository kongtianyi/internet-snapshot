# -*- coding: utf-8 -*-

import pymysql
import psutil
import json


mysql_config = {
    'host': '120.79.178.39',
    'port': 3306,
    'user': 'root',
    'password': 'KONG64530322931',
    'db': 'internet_snapshot',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}


def insert_this_vps(ip, nickname):
    connection = pymysql.connect(**mysql_config)
    sql = "INSERT INTO vps (ip, nickname, cpu_count, cpu_logical_count, memory, swap, disks) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s);"
    cpu_count = psutil.cpu_count(logical=False)
    cpu_logical_count = psutil.cpu_count()
    memory = psutil.virtual_memory()[0]
    swap = psutil.swap_memory()[0]
    disks = dict()
    disk_partitions = psutil.disk_partitions()
    for disk_partition in disk_partitions:
        disk_partition_total = psutil.disk_usage(disk_partition[1])[0]
        disks[disk_partition[0]] = {
            "mountpoint": disk_partition[1],
            "fstype": disk_partition[2],
            "opts": disk_partition[3],
            "total": disk_partition_total
        }
    disks = json.dumps(disks)
    with connection.cursor() as cursor:
        cursor.execute(sql, (ip, nickname, cpu_count, cpu_logical_count, memory, swap, disks))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    insert_this_vps("", "")