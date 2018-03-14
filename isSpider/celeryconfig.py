# -*- coding: utf-8 -*-

from kombu import Queue, Exchange


broker_url = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'
# result_backend = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = True

acks_late = True
prefetch_multiplier = 1  # 预取任务数
concurrency = 1  # 单一worker的并发数，目前多了会导致webdriver出错，后期优化

# task_default_queue = "default_queue"  # 默认的队列，如果一个消息不符合其他的队列就会放在默认队列里面
# task_default_exchange = "fanout_exchange"
# task_default_exchange_type = "fanout"

task_queues = (
    # 这是上面指定的默认队列
    Queue('default_queue', Exchange("default_exchange", type="direct"), routing_key="default_key"),
    # 以下是2个fanout队列,他们的exchange相同
    Queue('beijing_queue', Exchange("fanout_exchange", type="fanout")),
    Queue('shenzhen_queue', Exchange("fanout_exchange", type="fanout")),
    Queue('weihai_queue', Exchange("fanout_exchange", type="fanout")),
)

task_routes = {
    'tasks.download': {
        'exchange': 'fanout_exchange',
        'exchange_type': 'fanout',
    },
    'tasks.parse': {
        'queue': "default_queue",
        'routing_key': "default_key",
    },
    'tasks.clean_abnormal_engine': {
        'queue': "default_queue",
        'routing_key': "default_key",
    }
}
