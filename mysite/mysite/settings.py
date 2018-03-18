import os
from kombu import Queue, Exchange


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '4h=q81&(l)9f6lwwk-mbk@*gsi)zb9&cfeu374j4$ohre&oa-z'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'isadmin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'internet_snapshot',
        'USER': 'root',
        'PASSWORD': 'KONG64530322931',
        'HOST': '120.79.178.39',
        'PORT': '3306',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/static/'

# 以下是celery的配置
CELERY_BROKER_URL = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'
# result_backend = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = False

CELERY_ACKS_LATE = True
CELERY_PREFETCH_MULTIPLIER = 1  # 预取任务数
CELERY_CONCURRENCY = 1  # 单一worker的并发数，目前多了会导致webdriver出错，后期优化

CELERY_TASK_DEFAULT_QUEUE = "default_queue"  # 默认的队列，如果一个消息不符合其他的队列就会放在默认队列里面
CELERY_TASK_DEFAULT_EXCHANGE = "default_exchange"
CELERY_TASK_DEFAULT_EXCHANGE_TYPE = "direct"

# CELERY_TASK_QUEUES = (
#     # 这是上面指定的默认队列
#     Queue('default_queue', Exchange("default_exchange", type="direct"), routing_key="default_key"),
#     # 以下是2个fanout队列,他们的exchange相同
#     Queue('beijing_queue', Exchange("fanout_exchange", type="fanout")),
#     Queue('shenzhen_queue', Exchange("fanout_exchange", type="fanout")),
#     Queue('weihai_queue', Exchange("fanout_exchange", type="fanout")),
# )
#
# CELERY_TASK_ROUTES = {
#     'tasks.download': {
#         'exchange': 'fanout_exchange',
#         'exchange_type': 'fanout',
#     },
#     'tasks.parse': {
#         'queue': "default_queue",
#         'routing_key': "default_key",
#     },
#     'tasks.clean_abnormal_engine': {
#         'queue': "default_queue",
#         'routing_key': "default_key",
#     }
# }
