# -*- encoding: utf-8 -*-

from celery import Celery
from downloader import SingletonDownloader
from items import MainItem, main_item_to_json, json_to_main_item
from my_parser import Parser, CompareParser
from engine import Engine
import redis
import logging
import pymysql
import psutil
import json
import time

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )

mysql_config = {
    'host': '120.79.178.39',
    'port': 3306,
    'user': 'root',
    'password': 'KONG64530322931',
    'db': 'internet_snapshot',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

app = Celery()
app.config_from_object('celeryconfig')


@app.task
def snapshot(start_url, exist_time, deepth, max_num):
    engine = Engine(start_url, exist_time, deepth, max_num)
    engine.run()


@app.task
def download(request_url, refer, task_id, deepth):
    """下载页面"""
    main_item = MainItem(request_url, refer=refer, task_id=task_id, deepth=deepth)
    if not isinstance(main_item, MainItem):
        logging.error("Received param must items.MainItem, but get " + str(type(main_item)))
    downloader = SingletonDownloader(driver="Firefox")
    download_item = downloader.download(main_item)
    download_item = main_item_to_json(download_item)
    app.send_task("tasks.parse", args=(download_item,))


@app.task
def parse(main_item):
    """后处理页面（存库迭代等）"""
    parser = Parser(json_to_main_item(main_item))
    parser.parse()


@app.task
def clean_abnormal_engine():
    """清理redis中engine命名空间下的僵尸key"""
    redis_conn = redis.Redis.from_url("redis://:kongtianyideredis@114.67.225.0:6379/0")
    keys = redis_conn.keys(pattern="engine:*")
    for key in keys:
        if redis_conn.ttl(key) == -1:  # 在engine命名空间下却没有设置过期时间，故为异常key
            redis_conn.delete(key)


@app.task
def save_vps_status():
    """获取vps的CPU、内存、交换区、磁盘、网络使用情况，存到mysql"""
    with open("/etc/internet-snapshot.conf", "r", encoding="utf-8") as f:
        is_config = json.load(f)
        vps_id = is_config["vps_id"]
    # cpu情况
    cpu_status = list()
    cpu_percent_total = psutil.cpu_percent(interval=0, percpu=False)
    cpu_percent_percpu = psutil.cpu_percent(interval=0, percpu=True)
    cpu_status.append(cpu_percent_total)
    cpu_status.extend(cpu_percent_percpu)
    cpu_status = json.dumps(cpu_status)
    # 内存情况
    memory_used = psutil.virtual_memory()[3]
    # 交换区情况
    swap_used = psutil.swap_memory()[1]
    # 磁盘情况
    disks = dict()
    disk_partitions = psutil.disk_partitions()
    for disk_partition in disk_partitions:
        disks[disk_partition[0]] = psutil.disk_usage(disk_partition[1])[1]
    disks = json.dumps(disks)
    # 网络情况
    network_status = json.dumps(psutil.net_io_counters(pernic=True))
    # 存库
    connection = pymysql.connect(**mysql_config)
    sql = "INSERT INTO vps_status (vps_id, cpu_status, memory_used, swap_used, disks_status, network_status) " \
          "VALUES (%s, %s, %s, %s, %s, %s);"
    with connection.cursor() as cursor:
        cursor.execute(sql, (vps_id, cpu_status, memory_used, swap_used, disks, network_status))
    connection.commit()
    connection.close()


@app.task
def vps_status_clean():
    """清理vps_status表，使其只保持近七天的数据（0点清除六天前的数据）"""
    connection = pymysql.connect(**mysql_config)
    SIX_DAYS = 60 * 60 * 24 * 6
    now = int(time.time())
    six_days_ago = now - SIX_DAYS
    time_local = time.localtime(six_days_ago)
    format_time = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    sql = "DELETE FROM vps_status WHERE _time <= %s;"
    with connection.cursor() as cursor:
        re = cursor.execute(sql, (format_time,))
        if re == 0:
            logging.error("delete 0 rows.")
        else:
            logging.info("delete " + str(re) + " rows")
    connection.commit()
    connection.close()


@app.task
def compare_parse():
    """对未进行比对的任务进行比对"""
    connection = pymysql.connect(**mysql_config)
    # 查找出还未进行比对的所有任务id
    sql = "SELECT task_id FROM download_tasks WHERE compared=0;"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        items = cursor.fechall()
    connection.commit()
    connection.close()
    # 对这些任务进行逐个比对
    for item in items:
        logging.info("Now begin to handle " + item["task_id"])
        CompareParser.parse_by_task_id(item["task_id"])
