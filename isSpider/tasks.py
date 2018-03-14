# -*- encoding: utf-8 -*-

from celery import Celery
from downloader import SingletonDownloader
from items import MainItem, main_item_to_json, json_to_main_item
from my_parser import Parser
import redis
import json
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )

app = Celery()
app.config_from_object('celeryconfig')


@app.task
def download(request_url, refer, task_id):
    """下载页面"""
    main_item = MainItem(request_url, refer=refer, task_id=task_id)
    if not isinstance(main_item, MainItem):
        logging.error("Received param must items.MainItem, but get " + str(type(main_item)))
    # with Downloader(driver="Firefox") as downloader:
    #     download_item = downloader.download(url)
    downloader = SingletonDownloader(driver="Firefox")
    download_item = downloader.download(main_item)
    with open("./ext_conf.json", "r") as f:
        ext_conf = json.load(f)
        download_item.send_ip = ext_conf["local_ip"]
    download_item.server_ip = ""
    download_item = main_item_to_json(download_item)
    app.send_task("tasks.parse", args=(download_item,))
    # parser = Parser(download_item)
    # parser.parse()


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

