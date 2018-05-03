from django.db.models import F
from django.db.models import QuerySet
from django.http import QueryDict
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from isadmin.models import PublicSafeOutChains, PrivateSafeOutChains, MaliciousDomains, \
    Snapshot, SsHtml, SuspiciousRecords, PrivateOutChainRecords, Vps, VpsStatus, to_json_dict
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from isadmin.tools.html_util import HtmlUtil
from isadmin.tools.url_util import UrlUtil
from django.db import connection
from .tools.tools import get_ssh_connection
import json
import math
import time
import pexpect
import platform
import logging


def index(request):
    """首页-VPS监控"""
    if request.method != 'GET':
        return Http404
    return render(request, 'isadmin/index.html')


def pubsoc_list(request):
    """公共正常外链列表页面"""
    if request.method != 'GET':
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/pubsoc_list.html')


def prisoc_list(request):
    """私有正常外链列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/prisoc_list.html')


def malicious_domains_list(request):
    """恶意外链列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/malicious_domains_list.html')


def snapshot_list(request):
    """网页快照列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/snapshot_list.html')


def suspicious_records_list(request):
    """可疑外链列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/suspicious_records_list.html')


def pocr_list(request):
    """比对结果列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/pocr_list.html')


def dcbp_list(request):
    """定时任务列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/dcbp_list.html')


def show_snapshot(request, id=None):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    if not id:
        id = request.GET.get("id")
    aim = request.GET.get("aim")
    # else:
    #     aim = None
    ss = Snapshot.objects.filter(id=id)
    item = SsHtml.objects.filter(ss_id=id)
    if not isinstance(ss, QuerySet) or not isinstance(item, QuerySet):
        return render(request, 'isadmin/error/error-500.html')
    elif len(ss) == 0 or len(item) == 0:
        return render(request, 'isadmin/error/error-404.html')
    html = item[0].html
    final_url = ss[0].final_url
    domain = UrlUtil.get_domain(final_url)
    protocol = UrlUtil.get_protocol(final_url)
    format_html = html.replace("''", "'")  # 去掉因mysql存储问题而多存的单引号
    format_html = HtmlUtil.parse_protocol(format_html, protocol)  # 处理须补协议的链接
    format_html = HtmlUtil.parse_dmain(format_html, protocol, domain)  # 处理须补协议和域名的链接
    if aim:
        format_html = HtmlUtil.parse_aim(format_html, aim)  # 将目标主域名下的链接高亮显示
    return render(request, 'isadmin/snapshots.html', context={"snapshot": format_html})


def vps_monitor(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    vpss = Vps.objects.all()
    vps_statuss = []
    for vps in vpss:
        sql = "SELECT * FROM vps_status WHERE vps_id=%s AND _time=(SELECT max(_time) " \
              "FROM vps_status WHERE vps_id=%s);"
        with connection.cursor() as cursor:
            cursor.execute(sql, (vps.id, vps.id))
            vps_status_obj = cursor.fetchone()
        disks_total = 0
        disks = json.loads(vps.disks)
        for disk in disks.keys():
            disks_total += int(disks[disk]["total"])
        cpus = json.loads(vps_status_obj[2])
        disks_used = 0
        disks = json.loads(vps_status_obj[5])
        for disk in disks.keys():
            disks_used += int(disks[disk])
        vps_status = {
            "id": vps.id,
            "ip": vps.ip,
            "nickname": vps.nickname,
            "cpu_count": vps.cpu_count,
            "cpu_logical_count": vps.cpu_logical_count,
            "cpu_percent": cpus[0],
            "memory_total": byte_to_gb(vps.memory),
            "memory_used": byte_to_gb(vps.memory - vps_status_obj[3]),
            "memory_percent": float_to_percent(vps_status_obj[3] / vps.memory),
            "swap_total": byte_to_gb(vps.swap),
            "swap_used": byte_to_gb(vps.swap - vps_status_obj[4]),
            "swap_percent": float_to_percent(0 if vps.swap == 0 else vps_status_obj[4] / vps.swap),
            "disks_total": byte_to_gb(disks_total),
            "disks_used": byte_to_gb(disks_total - disks_used),
            "disks_percent": float_to_percent(disks_used / disks_total),
        }
        vps_statuss.append(vps_status)
    context = {
        "vpss": vps_statuss,
    }
    return render(request, 'isadmin/monitor/vps_monitor.html', context=context)


def vps_monitor_reload(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    vpss = Vps.objects.all()
    vps_statuss = []
    for vps in vpss:
        sql = "SELECT * FROM vps_status WHERE vps_id=%s AND _time=(SELECT max(_time) " \
              "FROM vps_status WHERE vps_id=%s);"
        with connection.cursor() as cursor:
            cursor.execute(sql, (vps.id, vps.id))
            vps_status_obj = cursor.fetchone()
        disks_total = 0
        disks = json.loads(vps.disks)
        for disk in disks.keys():
            disks_total += int(disks[disk]["total"])
        cpus = json.loads(vps_status_obj[2])
        disks_used = 0
        disks = json.loads(vps_status_obj[5])
        for disk in disks.keys():
            disks_used += int(disks[disk])
        vps_status = {
            "id": vps.id,
            "ip": vps.ip,
            "nickname": vps.nickname,
            "cpu_count": vps.cpu_count,
            "cpu_logical_count": vps.cpu_logical_count,
            "cpu_percent": cpus[0],
            "memory_total": byte_to_gb(vps.memory),
            "memory_used": byte_to_gb(vps.memory - vps_status_obj[3]),
            "memory_percent": float_to_percent(vps_status_obj[3] / vps.memory),
            "swap_total": byte_to_gb(vps.swap),
            "swap_used": byte_to_gb(vps.swap - vps_status_obj[4]),
            "swap_percent": float_to_percent(0 if vps.swap == 0 else vps_status_obj[4] / vps.swap),
            "disks_total": byte_to_gb(disks_total),
            "disks_used": byte_to_gb(disks_total - disks_used),
            "disks_percent": float_to_percent(disks_used / disks_total),
        }
        vps_statuss.append(vps_status)
    result = json_result("success", "查询成功:-)", data=vps_statuss)
    return HttpResponse(result, content_type="application/json;charset=utf-8")


def vps_detail(request):
    if request.method != "GET":
        return render(request, "isadmin/error/error-403.html")
    vps_id = request.GET.get("vps_id")
    context = {
        "vps_id": vps_id,
    }
    return render(request, "isadmin/monitor/vps_detail.html", context=context)


def cpu_chart(request):
    """cpu利用率走势"""
    vps_id = request.GET.get("vps_id")
    try:
        vps_status_count = VpsStatus.objects.filter(vps_id=vps_id).count()
        vps_statuses = VpsStatus.objects.filter(vps_id=vps_id)[vps_status_count-288:]
    except:
        return render(request, "isadmin/error/error-500.html")
    result = {
        "times": [],
        "rates": [],
    }
    for vps_status in vps_statuses:
        unformat_time = vps_status.field_time
        format_time = time.strftime("%Y-%m-%d %H:%M", unformat_time.timetuple())
        result["times"].append(format_time)
        result["rates"].append(json.loads(vps_status.cpu_status)[0])
    return HttpResponse(json_result("success", "查询成功:-)", data=result), content_type="application/json;charset=utf-8")


def memory_chart(request):
    """内存利用率走势"""
    vps_id = request.GET.get("vps_id")
    try:
        vps = Vps.objects.filter(id=vps_id)
        vps_status_count = VpsStatus.objects.filter(vps_id=vps_id).count()
        vps_statuses = VpsStatus.objects.filter(vps_id=vps_id)[vps_status_count-288:]
    except:
        return render(request, "isadmin/error/error-500.html")
    memory_total = vps[0].memory
    result = {
        "times": [],
        "rates": [],
    }
    for vps_status in vps_statuses:
        unformat_time = vps_status.field_time
        format_time = time.strftime("%Y-%m-%d %H:%M", unformat_time.timetuple())
        result["times"].append(format_time)
        result["rates"].append(float_to_percent(vps_status.memory_used/memory_total))
    return HttpResponse(json_result("success", "查询成功:-)", data=result), content_type="application/json;charset=utf-8")


def disks_chart(request):
    """磁盘剩余量走势"""
    vps_id = request.GET.get("vps_id")
    try:
        vps = Vps.objects.filter(id=vps_id)
        vps_status_count = VpsStatus.objects.filter(vps_id=vps_id).count()
        vps_statuses = VpsStatus.objects.filter(vps_id=vps_id)[vps_status_count-288:]
    except:
        return render(request, "isadmin/error/error-500.html")
    disks = json.loads(vps[0].disks)
    disks_total = 0
    for disk in disks.keys():
        disks_total += disks[disk]["total"]
    result = {
        "times": [],
        "lefts": [],
    }
    for vps_status in vps_statuses:
        unformat_time = vps_status.field_time
        format_time = time.strftime("%Y-%m-%d %H:%M", unformat_time.timetuple())
        disks = json.loads(vps_status.disks_status)
        disks_used = 0
        for disk in disks.keys():
            disks_used += disks[disk]
        result["times"].append(format_time)
        result["lefts"].append(byte_to_gb(disks_total-disks_used))
    return HttpResponse(json_result("success", "查询成功:-)", data=result), content_type="application/json;charset=utf-8")


def redirect_records(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/report/redirect_records.html')


def compare_unique(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/report/compare_unique.html')


def filted_suspicious(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/report/filted_suspicious.html')


def one_button(request):
    """一键功能页"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/one_button.html')


def add_task(request):
    """增加定时快照任务页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/task/add_task.html')


def get_tasks(request):
    """定时快照任务视图"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')

    with connection.cursor() as cursor:
        sql = "SELECT task.name,task.description,task.args,task.expires,cron.minute,cron.hour," \
              "cron.day_of_week,cron.day_of_month,cron.month_of_year,task.id,task.enabled, task.expires" \
              " FROM django_celery_beat_periodictask AS task" \
              " INNER JOIN django_celery_beat_crontabschedule AS cron" \
              " ON task.crontab_id=cron.id" \
              " WHERE task.task='tasks.snapshot';"
        cursor.execute(sql)
        items = cursor.fetchall()
    datas = list()
    group_num = 0
    group = list()
    for item in items:
        data = dict()
        data["name"] = item[0]
        data["description"] = item[1]
        args = json.loads(item[2])
        data["start_url"] = args[0]
        data["exist_time"] = int(int(args[1]) / 60)
        data["depth"] = args[2]
        data["max_num"] = args[3]
        data["expires"] = item[3]
        data["crontab"] = item[4] + " " + item[5] + " " + item[6] \
                          + " " + item[7] + " " + item[8]
        data["id"] = item[9]
        data["enabled"] = item[10]
        expires = item[11]
        if expires is None:
            data["expires_check"] = 1
        else:
            expires_time = time.mktime(expires.timetuple())
            now_time = int(time.time())
            data["expires_check"] = 0 if now_time-expires_time > 0 else 1
        group_num += 1
        group.append(data)
        if group_num == 3:
            datas.append(group)
            group_num = 0
            group = list()
    if group_num != 0:
        # 等于0的时候说明任务数是3的倍数，这个group已经加进去了
        datas.append(group)
    context = {
        "groups": datas,
    }

    return render(request, 'isadmin/task/tasks.html', context=context)


def edit_task(request):
    """编辑定时快照任务页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    task_id = request.GET.get("id")
    with connection.cursor() as cursor:
        sql = "SELECT task.name,task.description,task.args,task.expires,task.enabled,cron.minute,cron.hour," \
              "cron.day_of_week,cron.day_of_month,cron.month_of_year" \
              " FROM django_celery_beat_periodictask AS task" \
              " INNER JOIN django_celery_beat_crontabschedule AS cron" \
              " ON task.crontab_id=cron.id" \
              " WHERE task.task='tasks.snapshot'" \
              " AND task.id=%s"
        cursor.execute(sql, (task_id,))
        item = cursor.fetchone()
    args = json.loads(item[2])
    context = {
        "name": item[0],
        "start_url": args[0],
        "exist_time": args[1],
        "depth": args[2],
        "max_num": args[3],
        "expires": item[3] if item[3] is not None else "",
        "enabled": item[4],
        "description": item[1],
        "minute": item[5],
        "hour": item[6],
        "day_of_week": item[7],
        "day_of_month": item[8],
        "month_of_year": item[9]
    }
    return render(request, 'isadmin/task/edit_task.html', context=context)


def history_log(request):
    """历史日志查询页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/log/history_log.html')


def real_time_log(request):
    """实时日志查询页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/log/real_time_log.html')


@csrf_exempt
def pubsocs(request, id=None):
    """PUBSOC(PublicSafeOutChains)的CURD操作REST接口"""
    if request.method == 'POST':
        mydomain = request.POST.get("mydomain")
        remark = request.POST.get("remark")
        obj = PublicSafeOutChains.objects.create(mydomain=mydomain, remark=remark)
        if not obj:
            result = json_result("error", "添加公共正常外链主域名失败:-(")
        else:
            result = json_result("success", "添加公共正常外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'DELETE':
        obj = PublicSafeOutChains.objects.filter(id=id).delete()
        if not obj or obj[0] == 0:
            result = json_result("error", "删除公共正常外链主域名失败:-(")
        else:
            result = json_result("success", "删除公共正常外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'PUT':
        put = QueryDict(request.body)
        id = put.get("id")
        mydomain = put.get("mydomain")
        remark = put.get("remark")
        obj = PublicSafeOutChains.objects.filter(id=id).update(mydomain=mydomain, remark=remark)
        if obj == 0:
            result = json_result("error", "更新公共正常外链主域名失败:-(")
        else:
            result = json_result("success", "更新公共正常外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'GET':
        if id:
            obj = PublicSafeOutChains.objects.filter(id=id)
            if not isinstance(obj, QuerySet):
                result = json_result("error", "查询公共正常外链主域名失败:-(")
            else:
                data = list()
                data.append(to_json_dict(obj))
                result = json_result("success", "查询公共正常外链主域名成功:-)", data=data)
        else:
            rows = int(request.GET.get("rows")) if request.GET.get("rows") else 10
            page = int(request.GET.get("page")) if request.GET.get("page") else 1
            start = (page-1) * rows
            end = start + rows
            objs = PublicSafeOutChains.objects.all()[start: end]
            if not isinstance(objs, QuerySet):
                result = json_result("error", "查询公共正常外链主域名失败:-(")
            else:
                data = list()
                for obj in objs:
                    data.append(to_json_dict(obj))
                recoards = PublicSafeOutChains.objects.count()
                total_pages = math.floor(recoards / rows) + 1
                result = json_result("success", "查询公共正常外链主域名成功:-)", data=data, page=page,
                                     total=total_pages, records=recoards)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def pubsocs_jqgrid(request):
    """PUBSOC(PublicSafeOutChains)的CURD操作jqgrid接口"""
    if request.method == "POST":
        oper = request.POST.get("oper")
        if oper == "add":
            return pubsocs(request)
        elif oper == "del":
            id = request.POST.get("id")
            request.method = "DELETE"
            return pubsocs(request, id=id)
        elif oper == "edit":
            request.method = "PUT"
            return pubsocs(request)
    elif request.method == "GET":
        return pubsocs(request)
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def prisocs(request, id=None):
    """PRISOC(PrivateSafeOutChains)的CURD操作REST接口"""
    if request.method == 'POST':
        mydomain = request.POST.get("mydomain")
        owner = request.POST.get("owner")
        remark = request.POST.get("remark")
        obj = PrivateSafeOutChains.objects.create(mydomain=mydomain, owner=owner, remark=remark)
        if not obj:
            result = json_result("error", "添加私有正常外链主域名失败:-(")
        else:
            result = json_result("success", "添加私有正常外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'DELETE':
        obj = PrivateSafeOutChains.objects.filter(id=id).delete()
        if not obj or obj[0] == 0:
            result = json_result("error", "删除私有正常外链主域名失败:-(")
        else:
            result = json_result("success", "删除私有正常外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'PUT':
        put = QueryDict(request.body)
        id = put.get("id")
        mydomain = put.get("mydomain")
        owner = put.get("owner")
        remark = put.get("remark")
        obj = PrivateSafeOutChains.objects.filter(id=id).update(mydomain=mydomain, owner=owner, remark=remark)
        if obj == 0:
            result = json_result("error", "更新私有正常外链主域名失败:-(")
        else:
            result = json_result("success", "更新私有正常外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'GET':
        if id:
            obj = PrivateSafeOutChains.objects.filter(id=id)
            if not isinstance(obj, QuerySet):
                result = json_result("error", "查询私有正常外链主域名失败:-(")
            else:
                data = list()
                data.append(to_json_dict(obj))
                result = json_result("success", "查询私有正常外链主域名成功:-)", data=data)
        else:
            rows = int(request.GET.get("rows")) if request.GET.get("rows") else 10
            page = int(request.GET.get("page")) if request.GET.get("page") else 1
            start = (page-1) * rows
            end = start + rows
            objs = PrivateSafeOutChains.objects.all()[start: end]
            if not isinstance(objs, QuerySet):
                result = json_result("error", "查询私有正常外链主域名失败:-(")
            else:
                data = list()
                for obj in objs:
                    data.append(to_json_dict(obj))
                recoards = PrivateSafeOutChains.objects.count()
                total_pages = math.floor(recoards / rows) + 1
                result = json_result("success", "查询私有正常外链主域名成功:-)", data=data, page=page,
                                     total=total_pages, records=recoards)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def prisocs_jqgrid(request):
    """PRISOC(PrivateSafeOutChains)的CURD操作jqgrid接口"""
    if request.method == "POST":
        oper = request.POST.get("oper")
        if oper == "add":
            return prisocs(request)
        elif oper == "del":
            id = request.POST.get("id")
            request.method = "DELETE"
            return prisocs(request, id=id)
        elif oper == "edit":
            request.method = "PUT"
            return prisocs(request)
    elif request.method == "GET":
        return prisocs(request)
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def malicious_domains(request, id=None):
    """MaliciousDomains的CURD操作REST接口"""
    if request.method == 'POST':
        mydomain = request.POST.get("mydomain")
        remark = request.POST.get("remark")
        obj = MaliciousDomains.objects.create(mydomain=mydomain, remark=remark)
        if not obj:
            result = json_result("error", "添加恶意外链主域名失败:-(")
        else:
            result = json_result("success", "添加恶意外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'DELETE':
        obj = MaliciousDomains.objects.filter(id=id).delete()
        if not obj or obj[0] == 0:
            result = json_result("error", "删除恶意外链主域名失败:-(")
        else:
            result = json_result("success", "删除恶意外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'PUT':
        put = QueryDict(request.body)
        id = put.get("id")
        mydomain = put.get("mydomain")
        remark = put.get("remark")
        obj = MaliciousDomains.objects.filter(id=id).update(mydomain=mydomain, remark=remark)
        if obj == 0:
            result = json_result("error", "更新恶意外链主域名失败:-(")
        else:
            result = json_result("success", "更新恶意外链主域名成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'GET':
        if id:
            obj = MaliciousDomains.objects.filter(id=id)
            if not isinstance(obj, QuerySet):
                result = json_result("error", "查询恶意外链主域名失败:-(")
            else:
                data = list()
                data.append(to_json_dict(obj))
                result = json_result("success", "查询恶意外链主域名成功:-)", data=data)
        else:
            rows = int(request.GET.get("rows")) if request.GET.get("rows") else 10
            page = int(request.GET.get("page")) if request.GET.get("page") else 1
            start = (page-1) * rows
            end = start + rows
            objs = MaliciousDomains.objects.all()[start: end]
            if not isinstance(objs, QuerySet):
                result = json_result("error", "查询恶意主域名失败:-(")
            else:
                data = list()
                for obj in objs:
                    data.append(to_json_dict(obj))
                records = MaliciousDomains.objects.count()
                total_pages = math.floor(records / rows) + 1
                result = json_result("success", "查询恶意外链主域名成功:-)", data=data, page=page,
                                     total=total_pages, records=records)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def malicious_domians_jqgrid(request):
    """MaliciousDomains的CURD操作jqgrid接口"""
    if request.method == "POST":
        oper = request.POST.get("oper")
        if oper == "add":
            return malicious_domains(request)
        elif oper == "del":
            id = request.POST.get("id")
            request.method = "DELETE"
            return malicious_domains(request, id=id)
        elif oper == "edit":
            request.method = "PUT"
            return malicious_domains(request)
    elif request.method == "GET":
        return malicious_domains(request)
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def snapshots(request, id=None):
    """网页快照(Snapshot)的CURD操作REST接口"""
    if request.method == 'POST':
        return render(request, 'isadmin/error/error-404.html')
    elif request.method == 'DELETE':
        obj = Snapshot.objects.filter(id=id).delete()
        if not obj or obj[0] == 0:
            result = json_result("error", "删除网页快照失败:-(")
        else:
            result = json_result("success", "删除网页快照成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'PUT':
        put = QueryDict(request.body)
        id = put.get("id")
        screen_shot_path = put.get("screen_shot_path")
        obj = Snapshot.objects.filter(id=id).update(screen_shot_path=screen_shot_path)
        if obj == 0:
            result = json_result("error", "更新网页快照失败:-(")
        else:
            result = json_result("success", "更新网页快照成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'GET':
        if id:
            obj = Snapshot.objects.filter(id=id)
            if not isinstance(obj, QuerySet):
                result = json_result("error", "查询网页快照失败:-(")
            else:
                data = list()
                if obj.get_time:
                    obj.get_time = obj.get_time.strftime("%Y-%m-%d %H:%M:%S")
                data.append(to_json_dict(obj))
                result = json_result("success", "查询网页快照成功:-)", data=data)
        else:
            rows = int(request.GET.get("rows")) if request.GET.get("rows") else 10
            page = int(request.GET.get("page")) if request.GET.get("page") else 1
            start = (page - 1) * rows
            end = start + rows
            objs = Snapshot.objects.all()[start: end]
            if not isinstance(objs, QuerySet):
                result = json_result("error", "查询网页快照失败:-(")
            else:
                data = list()
                for obj in objs:
                    if obj.get_time:
                        obj.get_time = obj.get_time.strftime("%Y-%m-%d %H:%M:%S")
                    data.append(to_json_dict(obj))
                recoards = Snapshot.objects.count()
                total_pages = math.floor(recoards / rows) + 1
                result = json_result("success", "查询网页快照成功:-)", data=data, page=page,
                                     total=total_pages, records=recoards)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def snapshots_jqgrid(request):
    """网页快照(Snapshot)的CURD操作jqgrid接口"""
    if request.method == "POST":
        oper = request.POST.get("oper")
        if oper == "add":
            return snapshots(request)
        elif oper == "del":
            id = request.POST.get("id")
            request.method = "DELETE"
            return snapshots(request, id=id)
        elif oper == "edit":
            request.method = "PUT"
            return snapshots(request)
    elif request.method == "GET":
        return snapshots(request)
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def suspicious_records(request, id=None):
    """可疑外链(SuspiciousRecords)的CURD操作REST接口"""
    if request.method == 'POST':
        ss_id = request.POST.get("ss_id")
        unknown_domain = request.POST.get("unknown_domain")
        checked = request.POST.get("checked")
        result = request.POST.get("result")
        check_time = request.POST.get("check_time")
        obj = SuspiciousRecords.objects.create(ss_id=ss_id, unknown_domain=unknown_domain, checked=checked,
                                               result=result, check_time=check_time)
        if not obj:
            result = json_result("error", "添加可疑外链记录失败:-(")
        else:
            result = json_result("success", "添加可疑外链记录成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'DELETE':
        if isinstance(id, str) and id.find(',') != -1:
            ids = id.split(',')
            result_msg = ""
            for item in ids:
                obj = SuspiciousRecords.objects.filter(id=item).delete()
                if not obj or obj[0] == 0:
                    result_msg += "删除可疑外链记录id" + item + "失败:-("
                else:
                    result_msg += "删除可疑外链记录id" + item + "成功:-)"
            result = json_result("success", result_msg)
        else:
            obj = SuspiciousRecords.objects.filter(id=id).delete()
            if not obj or obj[0] == 0:
                result = json_result("error", "删除可疑外链记录失败:-(")
            else:
                result = json_result("success", "删除可疑外链记录成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'PUT':
        put = QueryDict(request.body)
        id = put.get("id")
        ss_id = put.get("ss_id")
        unknown_domain = put.get("unknown_domain")
        checked = put.get("checked")
        result = put.get("result")
        check_time = put.get("check_time")
        obj = SuspiciousRecords.objects.filter(id=id).\
            update(ss_id=ss_id, unknown_domain=unknown_domain,
                   checked=checked, result=result, check_time=check_time)
        if obj == 0:
            result = json_result("error", "更新可疑外链记录失败:-(")
        else:
            result = json_result("success", "删除可疑外链记录成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'GET':
        if id:
            obj = SuspiciousRecords.objects.filter(id=id)
            if not isinstance(obj, QuerySet):
                result = json_result("error", "查询可疑外链记录失败:-(")
            else:
                data = list()
                if obj.check_time:
                    obj.check_time = obj.check_time.strftime("%Y-%m-%d %H:%M:%S")
                data.append(to_json_dict(obj))
                result = json_result("success", "查询可疑外链记录成功:-)", data=data)
        else:
            rows = int(request.GET.get("rows")) if request.GET.get("rows") else 10
            page = int(request.GET.get("page")) if request.GET.get("page") else 1
            start = (page - 1) * rows
            end = start + rows
            filters = request.GET.get("filters")
            if filters:
                objs = SuspiciousRecords.objects
                filters = eval(filters)
                group_op = filters["groupOp"]
                rules = filters["rules"]
                if group_op == "OR":
                    pass
                elif group_op == "AND":
                    for rule in rules:
                        if rule["op"] == "eq":
                            if rule["field"] == "checked":
                                objs = objs.filter(checked=rule["data"])
                            elif rule["field"] == "result":
                                objs = objs.filter(result=rule["data"])
                    records = objs.count()
                    objs = objs[start: end]
                else:
                    return render(request, 'isadmin/error/error-404.html')
            else:
                objs = SuspiciousRecords.objects.all()[start: end]
                records = SuspiciousRecords.objects.count()
            if not isinstance(objs, QuerySet):
                result = json_result("error", "查询可疑外链记录失败:-(")
            else:
                data = list()
                for obj in objs:
                    if obj.check_time:
                        obj.check_time = obj.check_time.strftime("%Y-%m-%d %H:%M:%S")
                    data.append(to_json_dict(obj))

                total_pages = math.floor(records / rows) + 1
                result = json_result("success", "查询可疑外链记录成功:-)", data=data, page=page,
                                     total=total_pages, records=records)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def suspicious_records_jqgrid(request):
    """可疑外链(SuspiciousRecords)的CURD操作jqgrid接口"""
    if request.method == "POST":
        oper = request.POST.get("oper")
        if oper == "add":
            return suspicious_records(request)
        elif oper == "del":
            id = request.POST.get("id")
            request.method = "DELETE"
            return suspicious_records(request, id=id)
        elif oper == "edit":
            request.method = "PUT"
            return suspicious_records(request)
    elif request.method == "GET":
        return suspicious_records(request)
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def pocr_records(request, id=None):
    """比对结果(PrivateOutChainRecords)的CURD操作REST接口"""
    if request.method == 'POST':
        ss_id = request.POST.get("ss_id")
        out_chain = request.POST.get("out_chain")
        checked = request.POST.get("checked")
        result = request.POST.get("result")
        check_time = request.POST.get("check_time")
        obj = PrivateOutChainRecords.objects.create(ss_id=ss_id, out_chain=out_chain,
                                                    checked=checked, result=result,
                                                    check_time=check_time)
        if not obj:
            result = json_result("error", "添加比对结果记录失败:-(")
        else:
            result = json_result("success", "添加比对结果记录成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'DELETE':
        if isinstance(id, str) and id.find(',') != -1:
            ids = id.split(',')
            result_msg = ""
            for item in ids:
                obj = PrivateOutChainRecords.objects.filter(id=item).delete()
                if not obj or obj[0] == 0:
                    result_msg += "删除比对结果记录id" + item + "失败:-("
                else:
                    result_msg += "删除比对结果记录id" + item + "成功:-)"
            result = json_result("success", result_msg)
        else:
            obj = PrivateOutChainRecords.objects.filter(id=id).delete()
            if not obj or obj[0] == 0:
                result = json_result("error", "删除比对结果记录失败:-(")
            else:
                result = json_result("success", "删除比对结果记录成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'PUT':
        put = QueryDict(request.body)
        id = put.get("id")
        ss_id = put.get("ss_id")
        out_chain = put.get("out_chain")
        checked = put.get("checked")
        result = put.get("result")
        check_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        obj = PrivateOutChainRecords.objects.filter(id=id). \
            update(ss_id=ss_id, out_chain=out_chain,
                   checked=checked, result=result, check_time=check_time)
        if obj == 0:
            result = json_result("error", "更新比对结果记录失败:-(")
        else:
            result = json_result("success", "删除比对结果记录成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'GET':
        if id:
            obj = PrivateOutChainRecords.objects.filter(id=id)
            if not isinstance(obj, QuerySet):
                result = json_result("error", "查询比对结果记录失败:-(")
            else:
                data = list()
                if obj.check_time:
                    obj.check_time = obj.check_time.strftime("%Y-%m-%d %H:%M:%S")
                data.append(to_json_dict(obj))
                result = json_result("success", "查询比对结果记录成功:-)", data=data)
        else:
            rows = int(request.GET.get("rows")) if request.GET.get("rows") else 10
            page = int(request.GET.get("page")) if request.GET.get("page") else 1
            start = (page - 1) * rows
            end = start + rows
            filters = request.GET.get("filters")
            if filters:
                objs = PrivateOutChainRecords.objects
                filters = eval(filters)
                group_op = filters["groupOp"]
                rules = filters["rules"]
                if group_op == "OR":
                    pass
                elif group_op == "AND":
                    for rule in rules:
                        if rule["op"] == "eq":
                            if rule["field"] == "checked":
                                objs = objs.filter(checked=rule["data"])
                            elif rule["field"] == "result":
                                objs = objs.filter(result=rule["data"])
                    records = objs.count()
                    objs = objs[start: end]
                else:
                    return render(request, 'isadmin/error/error-404.html')
            else:
                objs = PrivateOutChainRecords.objects.all()[start: end]
                records = PrivateOutChainRecords.objects.count()
            if not isinstance(objs, QuerySet):
                result = json_result("error", "查询比对结果记录失败:-(")
            else:
                data = list()
                for obj in objs:
                    if obj.check_time:
                        obj.check_time = obj.check_time.strftime("%Y-%m-%d %H:%M:%S")
                    data.append(to_json_dict(obj))

                total_pages = math.floor(records / rows) + 1
                result = json_result("success", "查询比对结果记录成功:-)", data=data, page=page,
                                     total=total_pages, records=records)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def pocr_jqgrid(request):
    """比对结果(PrivateOutChainRecords)的CURD操作jqgrid接口"""
    if request.method == "POST":
        oper = request.POST.get("oper")
        if oper == "add":
            return pocr_records(request)
        elif oper == "del":
            id = request.POST.get("id")
            request.method = "DELETE"
            return pocr_records(request, id=id)
        elif oper == "edit":
            request.method = "PUT"
            return pocr_records(request)
    elif request.method == "GET":
        return pocr_records(request)
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def dcbps(request, id=None):
    """DCBP(DjangoCeleryBeatPeriodicTask)的CURD操作REST接口"""
    if request.method == 'POST':
        name = request.POST.get("name")
        args = request.POST.get("args")
        kwargs = request.POST.get("kwargs")
        queue = request.POST.get("queue")
        exchange = request.POST.get("exchange")
        routing_key = request.POST.get("routing_key")
        expires = request.POST.get("expires")
        enabled = request.POST.get("enabled")
        last_run_at = request.POST.get("last_run_at")
        total_run_count = request.POST.get("total_run_count")
        date_changed = request.POST.get("dete_changed")
        description = request.POST.get("description")
        crontab_id = request.POST.get("crontab_id")
        obj = PeriodicTask.objects.create(name=name, args=args, kwargs=kwargs, queue=queue, exchange=exchange,
                                          routing_key=routing_key, expires=expires, enabled=enabled,
                                          last_run_at=last_run_at, total_run_count=total_run_count,
                                          date_changed=date_changed, description=description, crontab_id=crontab_id)
        if not obj:
            result = json_result("error", "添加定时任务失败:-(")
        else:
            result = json_result("success", "添加定时任务成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'DELETE':
        obj = PeriodicTask.objects.filter(id=id).delete()
        if not obj or obj[0] == 0:
            result = json_result("error", "删除定时任务失败:-(")
        else:
            result = json_result("success", "删除定时任务成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'PUT':
        put = QueryDict(request.body)
        id = put.get("id")
        name = put.get("name")
        args = put.get("args")
        kwargs = put.get("kwargs")
        queue = put.get("queue")
        exchange = put.get("exchange")
        routing_key = put.get("routing_key")
        expires = put.get("expires")
        enabled = put.get("enabled")
        last_run_at = put.get("last_run_at")
        total_run_count = put.get("total_run_count")
        date_changed = put.get("dete_changed")
        description = put.get("description")
        crontab_id = put.get("crontab_id")
        obj = PeriodicTask.objects.filter(id=id).update(name=name, args=args, kwargs=kwargs, queue=queue, exchange=exchange,
                                                 routing_key=routing_key, expires=expires, enabled=enabled,
                                                 last_run_at=last_run_at, total_run_count=total_run_count,
                                                 date_changed=date_changed, description=description, crontab_id=crontab_id)
        if obj == 0:
            result = json_result("error", "更新定时任务失败:-(")
        else:
            result = json_result("success", "更新定时任务成功:-)")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif request.method == 'GET':
        if id:
            obj = PeriodicTask.objects.filter(id=id)
            if not isinstance(obj, QuerySet):
                result = json_result("error", "查询定时任务失败:-(")
            else:
                data = list()
                data.append(to_json_dict(obj))
                result = json_result("success", "查询定时任务成功:-)", data=data)
        else:
            rows = int(request.GET.get("rows")) if request.GET.get("rows") else 10
            page = int(request.GET.get("page")) if request.GET.get("page") else 1
            start = (page - 1) * rows
            end = start + rows
            objs = PeriodicTask.objects.all()[start: end]
            if not isinstance(objs, QuerySet):
                result = json_result("error", "查询定时任务失败:-(")
            else:
                data = list()
                for obj in objs:
                    data.append(to_json_dict(obj))
                recoards = PeriodicTask.objects.count()
                total_pages = math.floor(recoards / rows) + 1
                result = json_result("success", "查询定时任务成功:-)", data=data, page=page,
                                     total=total_pages, records=recoards)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def dcbps_jqgrid(request):
    """DCBP(DjangoCeleryBeatPeriodicTask)的CURD操作jqgrid接口"""
    if request.method == "POST":
        oper = request.POST.get("oper")
        if oper == "add":
            return dcbps(request)
        elif oper == "del":
            id = request.POST.get("id")
            request.method = "DELETE"
            return dcbps(request, id=id)
        elif oper == "edit":
            request.method = "PUT"
            return dcbps(request)
    elif request.method == "GET":
        return dcbps(request)
    else:
        return render(request, 'isadmin/error/error-404.html')


@csrf_exempt
def redirect_records_datas(request):
    draw = request.GET.get("draw")
    start = int(request.GET.get("start"))
    length = int(request.GET.get("length"))
    objs = Snapshot.objects.exclude(request_url=F("final_url")).\
        values("id", "request_url", "final_url", "task_id", "send_ip", "server_ip")
    redirect_objs = list()
    for obj in objs:
        if UrlUtil.get_top_domain(obj["request_url"]) != UrlUtil.get_top_domain(obj["final_url"]) \
                and obj["final_url"] != "Something error occurred, please check the error log.":
            redirect_objs.append(obj)
    data = redirect_objs[start: start+length]
    records_total = len(redirect_objs)
    # records_filtered = len(data)
    result = json_result("success", "查询成功:-)", draw=draw, data=data, recordsTotal=records_total,
                         recordsFiltered=records_total)
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def compare_unique_datas(request):
    draw = request.GET.get("draw")
    start = request.GET.get("start")
    length = request.GET.get("length")
    filter = request.GET.get("search[value]")
    sql = "SELECT snapshot.id, snapshot.request_url, private_out_chain_records.out_chain, " \
          "private_out_chain_records.checked, private_out_chain_records.result, " \
          "snapshot.send_ip, snapshot.server_ip, snapshot.get_time, private_out_chain_records.id " \
          "FROM snapshot INNER JOIN private_out_chain_records " \
          "ON snapshot.id = private_out_chain_records.ss_id "
    if filter == "未检查":
        sql += "WHERE private_out_chain_records.checked=0 "
    elif "恶意" in filter:
        sql += "WHERE private_out_chain_records.checked=1 AND private_out_chain_records.result=1 "
    sql += "LIMIT %s,%s;"
    with connection.cursor() as cursor:
        cursor.execute(sql, (int(start), int(length)))
        rows = cursor.fetchall()
    data = []
    for row in rows:
        item = {}
        item["ss_id"] = row[0]
        item["request_url"] = row[1]
        item["out_chain"] = row[2]
        item["checked"] = row[3]
        item["result"] = row[4]
        item["send_ip"] = row[5]
        item["server_ip"] = row[6]
        get_time = row[7].strftime("%Y-%m-%d %H:%M:%S")
        item["get_time"] = get_time
        item["id"] = row[8]
        data.append(item)
    sql = "SELECT COUNT(*) FROM snapshot INNER JOIN private_out_chain_records " \
          "ON snapshot.id = private_out_chain_records.ss_id "
    if filter == "未检查":
        sql += "WHERE private_out_chain_records.checked=0 "
    elif "恶意" in filter:
        sql += "WHERE private_out_chain_records.checked=1 AND private_out_chain_records.result=1 "
    sql += ";"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        re = cursor.fetchone()
    records_total = re[0]
    # records_filtered = len(data)
    result = json_result("success", "查询成功:-)", draw=draw, data=data, recordsTotal=records_total,
                         recordsFiltered=records_total)
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def filted_suspicious_datas(request):
    draw = request.GET.get("draw")
    start = request.GET.get("start")
    length = request.GET.get("length")
    filter = request.GET.get("search[value]")
    sql = "SELECT snapshot.id, snapshot.request_url, suspicious_records.unknown_domain, " \
          "suspicious_records.checked, suspicious_records.result, " \
          "snapshot.send_ip, snapshot.server_ip, snapshot.get_time, suspicious_records.id " \
          "FROM snapshot INNER JOIN suspicious_records " \
          "ON snapshot.id = suspicious_records.ss_id "
    if filter == "未检查":
        sql += "WHERE suspicious_records.checked=0 "
    elif "恶意" in filter:
        sql += "WHERE suspicious_records.checked=1 AND suspicious_records.result=1 "
    sql += "LIMIT %s,%s;"
    with connection.cursor() as cursor:
        cursor.execute(sql, (int(start), int(length)))
        rows = cursor.fetchall()
    data = []
    for row in rows:
        item = {}
        item["ss_id"] = row[0]
        item["request_url"] = row[1]
        item["unknown_domain"] = row[2]
        item["checked"] = row[3]
        item["result"] = row[4]
        item["send_ip"] = row[5]
        item["server_ip"] = row[6]
        get_time = row[7].strftime("%Y-%m-%d %H:%M:%S")
        item["get_time"] = get_time
        item["id"] = row[8]
        data.append(item)
    sql = "SELECT COUNT(*) FROM snapshot INNER JOIN suspicious_records " \
          "ON snapshot.id = suspicious_records.ss_id "
    if filter == "未检查":
        sql += "WHERE suspicious_records.checked=0 "
    elif "恶意" in filter:
        sql += "WHERE suspicious_records.checked=1 AND suspicious_records.result=1 "
    sql += ";"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        re = cursor.fetchone()
    records_total = re[0]
    records_filtered = len(data)  # 指有前端有过滤条件时的记录数
    result = json_result("success", "查询成功:-)", draw=draw, data=data, recordsTotal=records_total,
                         recordsFiltered=records_total)
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def beat_start(request):
    ip = "118.24.106.218"
    user = "root"
    password = "KONG64530322931."
    if platform.system() != "Linux":
        result = json_result("error", "WEB服务器操作系统不支持此操作！:-(")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    child = None
    try:
        child = get_ssh_connection(ip, user, password)
        child.expect("root@(.*?)~#", timeout=5)
        child.sendline("cd /home/internet-snapshot/mysite")
        child.expect("root@(.*?)/home/internet-snapshot/mysite#", timeout=5)
        child.sendline("ps -aux | grep django_celery_beat | grep -v grep | awk '{print $2}'")
        expect_result = child.expect(["\r\n\d+", "root@(.*?)/home/internet-snapshot/mysite#"], timeout=5)
        if expect_result == 0:
            pid = int(child.after[2:])
            result = json_result("error", "检测到beat正在运行，其进程id为%s。" % (pid,))
        else:
            child.sendline("bash ./celery-beat-start.sh")
            child.expect("root@(.*?)/home/internet-snapshot/mysite#", timeout=5)
            child.sendline("ps -aux | grep django_celery_beat | grep -v grep | awk '{print $2}'")
            child.expect("\r\n\d+", timeout=5)
            pid = int(child.after[2:])
            result = json_result("success", "beat启动成功，其进程号为%s。" % (pid,))
    except Exception as e:
        logging.error("When beat start, error %s occurred." % (e.__class__,))
        result = json_result("error", "后台链接失败，请重试:-(")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    finally:
        if child is not None:
            child.sendline("exit")
            child.close()
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def beat_stop(request):
    '''停止beat'''
    ip = "118.24.106.218"
    user = "root"
    password = "KONG64530322931."
    if platform.system() != "Linux":
        result = json_result("error", "WEB服务器操作系统不支持此操作！:-(")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    child = None
    try:
        child = get_ssh_connection(ip, user, password)
        child.expect("root@(.*?)~#", timeout=5)
        child.sendline("cd /home/internet-snapshot/mysite")
        child.expect("root@(.*?)/home/internet-snapshot/mysite#", timeout=5)
        child.sendline("ps -aux | grep django_celery_beat | grep -v grep | awk '{print $2}'")
        expect_result = child.expect(["\r\n\d+", "root@(.*?)/home/internet-snapshot/mysite#"], timeout=5)
        if expect_result == 1:
            result = json_result("error", "没有检测到beat正在运行。")
        else:
            pid = int(child.after[2:])
            child.sendline("bash ./celery-beat-stop.sh")
            child.expect("root@(.*?)/home/internet-snapshot/mysite#", timeout=5)
            child.sendline("ps -aux | grep django_celery_beat | grep -v grep | awk '{print $2}'")
            child.expect("\r\n", timeout=5)
            result = json_result("success", "beat停止成功，杀死进程号: %s。" % (pid,))
    except Exception as e:
        logging.error("When beat stop, error %s occurred." % (e.__class__,))
        result = json_result("error", "后台链接失败，请重试:-(")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    finally:
        if child is not None:
            child.sendline("exit")
            child.close()
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def beat_restart(request):
    '''重启django-celery-beat使定时任务修改生效'''
    ip = "118.24.106.218"
    user = "root"
    password = "KONG64530322931."
    if platform.system() != "Linux":
        result = json_result("error", "WEB服务器操作系统不支持此操作！:-(")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    child = None
    try:
        child = get_ssh_connection(ip, user, password)
        child.expect("root@(.*?)~#", timeout=5)
        child.sendline("cd /home/internet-snapshot/mysite")
        child.expect("root@(.*?)/home/internet-snapshot/mysite#", timeout=5)
        child.sendline("ps -aux | grep django_celery_beat | grep -v grep | awk '{print $2}'")
        expect_result = child.expect(["\r\n\d+", "root@(.*?)/home/internet-snapshot/mysite#"], timeout=5)
        if expect_result == 1:
            result = json_result("error", "没有检测到beat正在运行，请尝试点击启动beat按钮。")
        else:
            old_pid = int(child.after[2:])
            child.sendline("bash ./celery-beat-restart.sh")
            child.expect("root@(.*?)/home/internet-snapshot/mysite#", timeout=5)
            child.sendline("ps -aux | grep django_celery_beat | grep -v grep | awk '{print $2}'")
            child.expect("\r\n\d+", timeout=5)
            new_pid = int(child.after[2:])
            result = json_result("success", "beat重启成功,原进程号: %s, 新进程号: %s。" % (old_pid, new_pid))
    except Exception as e:
        logging.error("When beat restart, error %s occurred." % (e.__class__,))
        result = json_result("error", "后台链接失败，请重试:-(")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    finally:
        if child is not None:
            child.sendline("exit")
            child.close()
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def check_compare_unique(request):
    """判定比对出的独有外链是否异常"""
    # todo 事务控制
    result = request.GET.get("result")
    id = request.GET.get("id")
    request_url = request.GET.get("request_url")
    out_chain = request.GET.get("out_chain")
    out_chain_top_domain = UrlUtil.get_top_domain(out_chain)
    if result == "0":
        # 判定为恶意链接
        row = PrivateOutChainRecords.objects.filter(id=id).update(checked=1, result=1, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        row2 = MaliciousDomains.objects.create(mydomain=out_chain_top_domain)
        if row == 0 or row2 == 0:
            result = json_result("error", "添加恶意链接失败:-(")
        else:
            result = json_result("success", "添加恶意链接成功:-)")
        # 联动处理
        uncheked_records = PrivateOutChainRecords.objects.filter(checked=0)
        for uncheked_record in uncheked_records:
            if UrlUtil.get_top_domain(uncheked_record.out_chain) == UrlUtil.get_top_domain(out_chain):
                PrivateOutChainRecords.objects.filter(id=uncheked_record.id).update(checked=1, result=1, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    elif result == "1":
        # 加入公共白名单
        re = PrivateOutChainRecords.objects.filter(id=id).update(checked=1, result=0, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        re2 = PublicSafeOutChains.objects.create(mydomain=out_chain_top_domain)
        if re == 0 or re2 == 0:
            result = json_result("error", "加入公共白名单失败:-(")
        else:
            result = json_result("success", "加入公共白名单成功:-)")
        # 联动处理
        uncheked_records = PrivateOutChainRecords.objects.filter(checked=0)
        for uncheked_record in uncheked_records:
            if UrlUtil.get_top_domain(uncheked_record.out_chain) == UrlUtil.get_top_domain(out_chain):
                PrivateOutChainRecords.objects.filter(id=uncheked_record.id).update(checked=1, result=0,
                                                                                       check_time=time.strftime(
                                                                                           '%Y-%m-%d %H:%M:%S',
                                                                                           time.localtime(time.time())))
    elif result == "2":
        # 加入私有白名单
        re = PrivateOutChainRecords.objects.filter(id=id).update(checked=1, result=0, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        request_top_domain = UrlUtil.get_top_domain(request_url)
        re2 = PrivateSafeOutChains.objects.create(mydomain=out_chain_top_domain, owner=request_top_domain)
        if re == 0 or re2 == 0:
            result = json_result("error", "加入私有白名单失败:-(")
        else:
            result = json_result("success", "加入私有白名单成功:-)")
        # 联动处理
        uncheked_records = PrivateOutChainRecords.objects.filter(checked=0)
        for uncheked_record in uncheked_records:
            if UrlUtil.get_top_domain(uncheked_record,out_chain) == UrlUtil.get_top_domain(out_chain):
                PrivateOutChainRecords.objects.filter(id=uncheked_record.id).update(checked=1, result=0,
                                                                                           check_time=time.strftime(
                                                                                               '%Y-%m-%d %H:%M:%S',
                                                                                               time.localtime(
                                                                                                   time.time())))
    else:
        result = json_result("error", "参数错误:-(")
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def check_suspicious(request):
    """判定过滤出的可疑主域名是否异常"""
    # todo 事务控制、日志
    result = request.GET.get("result")
    id = request.GET.get("id")
    request_url = request.GET.get("request_url")
    unknown_domain = UrlUtil.get_domain(request.GET.get("unknown_domain"))
    request_top_domain = UrlUtil.get_top_domain(request_url)
    if result == "0":
        # 判定为恶意链接
        row = SuspiciousRecords.objects.filter(id=id).\
            update(checked=1, result=1, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        row2 = MaliciousDomains.objects.create(mydomain=unknown_domain)
        if row == 0 or row2 == 0:
            result = json_result("error", "添加恶意链接失败:-(")
        else:
            result = json_result("success", "添加恶意链接成功:-)")
        # 联动处理
        SuspiciousRecords.objects.filter(checked=0, unknown_domain=unknown_domain).\
            update(checked=1, result=1, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    elif result == "1":
        # 加入公共白名单
        re = SuspiciousRecords.objects.filter(id=id).\
            update(checked=1, result=0, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        re2 = PublicSafeOutChains.objects.create(mydomain=unknown_domain)
        if re == 0 or re2 == 0:
            result = json_result("error", "加入公共白名单失败:-(")
        else:
            result = json_result("success", "加入公共白名单成功:-)")
        # 联动处理
        SuspiciousRecords.objects.filter(checked=0, unknown_domain=unknown_domain).\
            update(checked=1, result=0, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    elif result == "2":
        # 加入私有白名单
        re = SuspiciousRecords.objects.filter(id=id).\
            update(checked=1, result=0, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        re2 = PrivateSafeOutChains.objects.create(mydomain=unknown_domain, owner=request_top_domain)
        if re == 0 or re2 == 0:
            result = json_result("error", "加入私有白名单失败:-(")
        else:
            result = json_result("success", "加入私有白名单成功:-)")
        # 联动处理
        SuspiciousRecords.objects.filter(checked=0, unknown_domain=unknown_domain).\
            update(checked=1, result=0, check_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    else:
        result = json_result("error", "参数错误:-(")
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def tasks(request):
    """与任务相关的CURD操作"""
    # todo 事务处理
    oper = request.GET.get("oper")
    if oper == "add":
        try:
            task_name = request.GET.get("task_name")
            start_url = request.GET.get("start_url")
            exist_time = request.GET.get("exist_time")
            depth = request.GET.get("depth")
            max_num = request.GET.get("max_num")
            expires = request.GET.get("expires")
            enabled = int(request.GET.get("enabled"))
            description = request.GET.get("description")
            minute = request.GET.get("minute")
            hour = request.GET.get("hour")
            day_of_week = request.GET.get("day_of_week")
            day_of_month = request.GET.get("day_of_month")
            month_of_year = request.GET.get("month_of_year")
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            # 对任务名查重
            with connection.cursor() as cursor:
                sql = "SELECT * FROM django_celery_beat_periodictask WHERE name=%s;"
                rows = cursor.execute(sql, (task_name,))
                if rows > 0:
                    result = json_result("error", "任务名重复，请更改。")
                    return HttpResponse(result, content_type="application/json;charset=utf-8")
            with connection.cursor() as cursor:
                sql = "INSERT INTO django_celery_beat_crontabschedule(minute,hour,day_of_week,day_of_month,month_of_year)" \
                  " VALUE (%s,%s,%s,%s,%s);"
                cursor.execute(sql, (minute, hour, day_of_week, day_of_month, month_of_year))
            with connection.cursor() as cursor:
                sql = "SELECT LAST_INSERT_ID() as id;"
                cursor.execute(sql)
                result = cursor.fetchone()
                cron_id = result[0]
            task_args = json.dumps([start_url, exist_time, depth, max_num])
            with connection.cursor() as cursor:
                sql = "INSERT INTO django_celery_beat_periodictask(name,task,args,kwargs,queue,exchange,routing_key,expires,enabled," \
                    "total_run_count,date_changed,description,crontab_id) VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
                cursor.execute(sql, (task_name, "tasks.snapshot", task_args, "{}", "default_queue", "default_exchange", "default_key",
                                     expires, enabled, 0, now, description, cron_id))
            result = json_result("success", "任务插入成功")
        except Exception as e:
            raise e
            logging.error("Error %s occurred" % (e.__class__,))
            result = json_result("error", "任务插入失败")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif oper == "get":
        with connection.cursor() as cursor:
            sql = "SELECT task.name,task.description,task.args,task.expires,cron.minute,cron.hour," \
                  "cron.day_of_week,cron.day_of_month,cron.month_of_year,task.id,task.enabled" \
                  " FROM django_celery_beat_periodictask AS task" \
                  " INNER JOIN django_celery_beat_crontabschedule AS cron" \
                  " ON task.crontab_id=cron.id" \
                  " WHERE task.task='tasks.snapshot'"
            cursor.execute(sql)
            items = cursor.fetchall()
        datas = list()
        for item in items:
            data = dict()
            data["name"] = item[0]
            data["description"] = item[1]
            args = json.loads(item[2])
            data["start_url"] = args[0]
            data["exist_time"] = args[1]
            data["depth"] = args[2]
            data["max_num"] = args[3]
            data["expires"] = item[3]
            data["crontab"] = item[4] + " " + item[5] + " " + item[6] \
                                + " " + item[7] + " " + item[8]
            data["id"] = item[9]
            data["enabled"] = item[10]
            datas.append(data)
        result = json_result("success", "查询成功", data=datas)
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    elif oper == "edit":
        try:
            task_id = request.GET.get("task_id")
            task_name = request.GET.get("task_name")
            start_url = request.GET.get("start_url")
            exist_time = request.GET.get("exist_time")
            depth = request.GET.get("depth")
            max_num = request.GET.get("max_num")
            expires = request.GET.get("expires") if request.GET.get("expires") is not "" else None
            enabled = int(request.GET.get("enabled"))
            description = request.GET.get("description")
            minute = request.GET.get("minute")
            hour = request.GET.get("hour")
            day_of_week = request.GET.get("day_of_week")
            day_of_month = request.GET.get("day_of_month")
            month_of_year = request.GET.get("month_of_year")
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            with connection.cursor() as cursor:
                sql = "INSERT INTO django_celery_beat_crontabschedule(minute,hour,day_of_week,day_of_month,month_of_year)" \
                  " VALUE (%s,%s,%s,%s,%s);"
                cursor.execute(sql, (minute, hour, day_of_week, day_of_month, month_of_year))
            with connection.cursor() as cursor:
                sql = "SELECT LAST_INSERT_ID() as id;"
                cursor.execute(sql)
                result = cursor.fetchone()
                cron_id = result[0]
            task_args = json.dumps([start_url, exist_time, depth, max_num])
            with connection.cursor() as cursor:
                sql = "UPDATE django_celery_beat_periodictask SET name=%s,args=%s,expires=%s,enabled=%s," \
                      "date_changed=%s,description=%s,crontab_id=%s WHERE id=%s;"
                cursor.execute(sql, (task_name, task_args, expires, enabled, now, description, cron_id, task_id))
            result = json_result("success", "任务更新成功")
        except Exception as e:
            raise e
            logging.error("Error %s occurred" % (e.__class__,))
            result = json_result("error", "任务更新失败")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        return render(request, 'isadmin/error/error-404.html')


def leveled_json_result(status, message, data=None):
    """将返回对象序列化成层次化的json串"""
    return json.dumps({
        "status": status,
        "message": message,
        "data": data,
    }, ensure_ascii=False)


def json_result(status, message, **kwargs):
    """将返回对象序列化成json串"""
    result = dict()
    result["status"] = status
    result["message"] = message
    for key in kwargs.keys():
        result[key] = kwargs[key]
    return json.dumps(result, ensure_ascii=False)


def float_to_percent(num):
    """小数转化成百分数"""
    return int(num * 100)


def byte_to_gb(num):
    """把比特数转化成GB, 保留两位"""
    return "%.2f" %(num / (1024 * 1024 * 1024))

