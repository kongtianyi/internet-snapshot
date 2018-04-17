# -*- coding: utf-8 -*-

BOT_NAME = 'traversal'

SPIDER_MODULES = ['traversal.spiders']
NEWSPIDER_MODULE = 'traversal.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3371.0 Safari/537.36'

ROBOTSTXT_OBEY = False

DEFAULT_REQUEST_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en',
}

ITEM_PIPELINES = {
   'traversal.pipelines.TraversalPipeline': 300,
}

DEPTH_PRIORITY = 1

RETRY_ENABLED = True
RETRY_TIMES = 3

DOWNLOAD_TIMEOUT = 30

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 20
CONCURRENT_REQUESTS_PER_DOMAIN = 4

# 配置过滤器为基于redis的布隆过滤器
DUPEFILTER_CLASS = 'traversal.BloomRedisDupeFilter.BloomRedisDupeFilter'
# reids中bitmap的key，默认为‘bloom’
BLOOM_REDIS_KEY = 'bloom'
# redis的连接配置，默认为本机
BLOOM_REDIS_HOST = '114.67.225.0'
BLOOM_REDIS_PORT = 6379
BLOOM_REDIS_PWD = "kongtianyideredis"
# 布隆过滤器的哈希列表，默认为8个，定义在GeneralHashFunctions中
BLOOM_HASH_LIST = ["rs_hash", "js_hash", "pjw_hash", "elf_hash", "bkdr_hash", "sdbm_hash", "djb_hash", "dek_hash"]
