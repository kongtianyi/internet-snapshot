# -*- coding: utf-8 -*-

from kombu import Queue, Exchange


# broker_url = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'
# result_backend = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'
#
# task_serializer = 'json'
# result_serializer = 'json'
# accept_content = ['json']
# timezone = 'Asia/Shanghai'
# enable_utc = True
#
# acks_late = True
# prefetch_multiplier = 1  # 预取任务数
# concurrency = 1  # 单一worker的并发数，目前多了会导致webdriver出错，后期优化
#
# task_default_queue = "default_queue"  # 默认的队列，如果一个消息不符合其他的队列就会放在默认队列里面
# task_default_exchange = "default_exchange"
# task_default_exchange_type = "direct"
#
# default_exchange = Exchange("default_exchange", type="direct")
# fanout_exchange = Exchange("fanout_exchange", type="fanout")
# fanout_download_exchange = Exchange("fanout_download_exchange", type="fanout")
#
# task_queues = (
#     # 这是上面指定的默认队列
#     Queue("default_queue", default_exchange, routing_key="default_key"),
#     # parse后处理任务专用队列
#     Queue("parse_queue", default_exchange, routing_key="parse_key"),
#     # 各地vps快照下载器专用队列
#     Queue("beijing_download_queue", fanout_download_exchange),
#     Queue("shenzhen_download_queue", fanout_download_exchange),
#     Queue("chengdu_download_queue", fanout_download_exchange),
#     # 各地vps其他广播任务队列
#     Queue("beijing_queue", fanout_exchange),
#     Queue("shenzhen_queue", fanout_exchange),
#     Queue("chengdu_queue", fanout_exchange),
# )
#
# task_routes = {
#     'tasks.download': {
#         'exchange': 'fanout_download_exchange',
#         'exchange_type': 'fanout',
#     },
#     'tasks.parse': {
#         'queue': "parse_queue",
#         'routing_key': "parse_key",
#     },
# }


BROKER_URL = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'
# RESULT_BACKEND = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'

TASK_SERIALIZER = 'json'
RESULT_SERIALIZER = 'json'
ACCEPT_CONTENT = ['json']
TIMEZONE = 'Asia/Shanghai'
ENABLE_UTC = True

ACKS_LATE = True
PREFETCH_MULTIPLIER = 1  # 预取任务数

TASK_DEFAULT_QUEUE = "default_queue"  # 默认的队列，如果一个消息不符合其他的队列就会放在默认队列里面
TASK_DEFAULT_EXCHANGE = "default_exchange"
TASK_DEFAULT_EXCHANGE_TYPE = "direct"

default_exchange = Exchange("default_exchange", type="direct")
fanout_exchange = Exchange("fanout_exchange", type="fanout")
fanout_download_exchange = Exchange("fanout_download_exchange", type="fanout")

TASK_QUEUES = (
    # 这是上面指定的默认队列
    Queue("default_queue", default_exchange, routing_key="default_key"),
    # parse后处理任务专用队列
    Queue("parse_queue", default_exchange, routing_key="parse_key"),
    # 各地vps快照下载器专用队列
    Queue("beijing_download_queue", fanout_download_exchange),
    Queue("shenzhen_download_queue", fanout_download_exchange),
    Queue("chengdu_download_queue", fanout_download_exchange),
    # 各地vps其他广播任务队列
    Queue("beijing_queue", fanout_exchange),
    Queue("shenzhen_queue", fanout_exchange),
    Queue("chengdu_queue", fanout_exchange),
)

TASK_ROUTES = {
    'tasks.download': {
        'exchange': 'fanout_download_exchange',
        'exchange_type': 'fanout',
    },
    'tasks.parse': {
        'queue': "parse_queue",
        'routing_key': "parse_key",
    },
}
