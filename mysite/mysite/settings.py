import os
from kombu import Queue, Exchange


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '4h=q81&(l)9f6lwwk-mbk@*gsi)zb9&cfeu374j4$ohre&oa-z'

DEBUG = False

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

USE_TZ = True

STATIC_URL = '/static/'

CORS_ORIGIN_ALLOW_ALL = True

# 以下是celery的配置
CELERY_BROKER_URL = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'
# result_backend = 'amqp://kongtianyi:kongtianyiderabbitmq@114.67.225.0:5672/kvhost'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_ENABLE_UTC = False

CELERY_ACKS_LATE = True
CELERY_PREFETCH_MULTIPLIER = 1  # 预取任务数
CELERY_CONCURRENCY = 1  # 单一worker的并发数，目前多了会导致webdriver出错，后期优化

# 以下三个配置项用于ssh连接beat宿主机进行启动、停止、重启操作
CELERY_BEAT_IP = "118.24.106.218"  # beat宿主机IP
CELERY_BEAT_USER = "root"  # beat宿主机登陆用户
CELERY_BEAT_PW =  "KONG64530322931."  # beat宿主机登陆用户密码

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25
# 发送邮件的邮箱
EMAIL_HOST_USER = '17862703685@163.com'
# 在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'kong19960412'
# 收件人看到的发件人
EMAIL_FROM = '互联网站点劫持检测系统<17862703685@163.com>'

# SITE_DOMAIN = 118.24.106.218
SITE_DOMAIN = 'localhost:8000'
RETRIEVE_ADDRESS = 'http://%s/isadmin/retrieve' % (SITE_DOMAIN,)

DES_KEY = b"sPp0$yve&xpuKBCY4$YGuzlS"

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
