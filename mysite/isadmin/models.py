from django.db import models


class PublicSafeOutChains(models.Model):
    """公共正常外链主域名列表"""
    mydomain = models.CharField("外链主域名", max_length=50)
    remark = models.CharField("备注", max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'public_safe_out_chains'


class PrivateSafeOutChains(models.Model):
    """各网站私有的正常外链主域名列表"""
    mydomain = models.CharField("外链主域名", max_length=50)
    owner = models.CharField("属主，即对它来说此外链安全", max_length=50)
    remark = models.CharField("备注", max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'private_safe_out_chains'


class Snapshot(models.Model):
    """快照存留表"""
    request_url = models.CharField("请求url", max_length=1000)
    final_url = models.CharField("最终下载的url", max_length=1000)
    screen_shot_path = models.CharField("快照地址", max_length=100, blank=True, null=True)
    load_time = models.FloatField("首屏加载时间", )
    refer = models.CharField("上级页面", max_length=1000)
    get_time = models.CharField("抓取时间", max_length=10)
    task_id = models.CharField("任务标识", max_length=100)
    send_ip = models.CharField("请求发送ip", max_length=20)
    server_ip = models.CharField("相应服务器ip", max_length=20)

    class Meta:
        managed = False
        db_table = 'snapshot'


class SsHtml(models.Model):
    """快照html页面表"""
    ss_id = models.IntegerField("快照存留表id")
    html = models.TextField("页面代码", )

    class Meta:
        managed = False
        db_table = 'ss_html'


class SuspiciousRecords(models.Model):
    """可疑外链记录表"""
    ss_id = models.IntegerField("快照id")
    unknown_domain = models.CharField("可疑外链主域名", max_length=50)
    checked = models.IntegerField("是否已检查 0-未检查 1-已检查")
    result = models.IntegerField("检查结果 0-误判 1-恶意信息")
    check_time = models.IntegerField("检查时间")

    class Meta:
        managed = False
        db_table = 'suspicious_records'


def to_json_dict(o):
    return dict([(attr, getattr(o, attr)) for attr in [f.name for f in o._meta.fields]])
