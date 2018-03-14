# -*- coding: utf-8 -*-

from url_util import UrlUtil
from celery import Celery
from items import MainItem, main_item_to_json
import json
import logging
import uuid
import redis
import time
import platform

# 防止在win系统下出现“OSError: raw write() returned invalid length”错误
if "Windows" in platform.system():
    import win_unicode_console
    win_unicode_console.enable()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )
app = Celery()
app.config_from_object('celeryconfig')
redis_conn = redis.Redis.from_url("redis://:kongtianyideredis@114.67.225.0:6379/0")


class Engine:
    """
    快照程序运转引擎
    """
    def __init__(self, start_url, exist_time=600, deepth=2, max_num=200):
        """
        :param start_url: 起始url
        :param exist_time: 任务最长持续时间
        :param deepth: 页面收集深度
        """
        self.main_item = MainItem(start_url)
        self.main_item.task_id = str(uuid.uuid1())  # 一次收集任务的标识
        self.main_item.refer = ""
        self.start_url = start_url
        self.top_domain = UrlUtil.get_top_domain(start_url)
        self.exist_time = exist_time
        self.deepth = deepth
        self.max_num = max_num

    def run(self):
        dup_set_name = "engine:dup_set:"+str(self.main_item.task_id)
        queue_name = "engine:queue:"+str(self.main_item.task_id)
        redis_conn.sadd(dup_set_name, self.start_url)  # url去重集合
        redis_conn.expire(dup_set_name, self.exist_time)  # 设置过期时间
        redis_conn.lpush(queue_name, json.dumps(self.main_item, default=main_item_to_json))  # url队列
        redis_conn.expire(queue_name, self.exist_time)  # 设置过期时间
        # 在键过期之前去重集合一定存在, 使用exists判断不了是否设置过过期时间
        # ttl > -1 -> 值为剩余存在时间
        # ttl = -1 -> 该键存在，但没有设置剩余时间
        # ttl = -2 -> 该键不存在
        # 在redis-py里ttl为-1和-2时都返回NoneType
        while isinstance(redis_conn.ttl(dup_set_name), int) and self.max_num > 0:
            next_main_item = redis_conn.rpop(queue_name)  # 队列中弹出一个json对象
            if next_main_item:
                next_main_item = next_main_item.decode("utf-8")  # 从redis读出的是bytes型数据
                next_main_item = json.loads(next_main_item, encoding="utf-8")
                app.send_task("tasks.download", args=(next_main_item["request_url"],
                                                      next_main_item["refer"], next_main_item["task_id"]))
                logging.info("发送下载任务，目标任务:" + str(next_main_item))
                self.max_num -= 1
            else:
                # 队列恰好为空，则等待worker往队列里塞url
                logging.info(queue_name + "队列为空, 等待任务。")
                time.sleep(1)

        redis_conn.delete(queue_name)  # 销毁url队列


if __name__ == "__main__":
    engine = Engine("http://www.sina.com.cn/", exist_time=60, max_num=50)
    engine.run()
    # app.send_task("tasks.download", args=("https://www.baidu.com", 60, 0))