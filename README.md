# 依赖库整理

django 2.0.3
celery 4.1.0
django-celery-beat-1.1.0
lxml
publicsuffix 1.1.0
selenium 3.9.0
phantomJS(ubuntu下apt安装)(弃)
pymysql-0.8.0
redis 2.10.6（python）
pexpect-4.4.0
psutil
pyDes
mysqlclient（启动django-celery-beat所需，首先apt-get install libmysqlclient-dev python3-dev）
uwsgi

# 依赖工具

linux下Mozilla Firefox 58.0.1
windows下Mozilla Firefox 58.0.2
geckodriver (路径：/usr/lib/firefox/geckodriver)
mysql
redis
rabbitmq
nginx


# 前端框架：
ace admin

# 配置文件

在每台vps创建以下配置文件：/etc/internet-snapshot.conf
{
    "outer_ip": "xx",
    "address": "xx",
    "address_pinyin": "xx",
    "vps_id": ""
}