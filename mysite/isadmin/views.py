from django.db.models import F
from django.db.models import QuerySet
from django.http import QueryDict
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from isadmin.models import PublicSafeOutChains, PrivateSafeOutChains, Snapshot, SsHtml, \
    SuspiciousRecords, Vps, VpsStatus, to_json_dict
from isadmin.tools.html_util import HtmlUtil
from isadmin.tools.url_util import UrlUtil
from django.db import connection
import json
import math
import time


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
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/report/filted_suspicious.html')


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
            result = json_result("success", "删除公共正常外链主域名成功:-)")
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
            result = json_result("success", "删除私有正常外链主域名成功:-)")
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
    sql = "SELECT snapshot.id, snapshot.request_url, " \
          "private_out_chain_records.out_chain, snapshot.task_id, " \
          "snapshot.send_ip, snapshot.server_ip, snapshot.get_time  " \
          "FROM snapshot INNER JOIN private_out_chain_records " \
          "ON snapshot.id = private_out_chain_records.ss_id " \
          "LIMIT %s,%s;"
    with connection.cursor() as cursor:
        cursor.execute(sql, (int(start), int(length)))
        rows = cursor.fetchall()
    data = []
    for row in rows:
        item = {}
        item["id"] = row[0]
        item["request_url"] = row[1]
        item["out_chain"] = row[2]
        item["task_id"] = row[3]
        item["send_ip"] = row[4]
        item["server_ip"] = row[5]
        timestamp = time.localtime(int(row[6]))
        # 转换成新的时间格式(2016-05-05 20:28:54)
        get_time = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
        item["get_time"] = get_time
        data.append(item)
    sql = "SELECT COUNT(*) FROM snapshot INNER JOIN private_out_chain_records " \
          "ON snapshot.id = private_out_chain_records.ss_id;"
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
    sql = "SELECT snapshot.id, snapshot.request_url, " \
          "suspicious_records.unknown_domain, snapshot.task_id, " \
          "snapshot.send_ip, snapshot.server_ip, snapshot.get_time  " \
          "FROM snapshot INNER JOIN suspicious_records " \
          "ON snapshot.id = suspicious_records.ss_id " \
          "LIMIT %s,%s;"
    with connection.cursor() as cursor:
        cursor.execute(sql, (int(start), int(length)))
        rows = cursor.fetchall()
    data = []
    for row in rows:
        item = {}
        item["id"] = row[0]
        item["request_url"] = row[1]
        item["unknown_domain"] = row[2]
        item["task_id"] = row[3]
        item["send_ip"] = row[4]
        item["server_ip"] = row[5]
        timestamp = time.localtime(int(row[6]))
        # 转换成新的时间格式(2016-05-05 20:28:54)
        get_time = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
        item["get_time"] = get_time
        data.append(item)
    sql = "SELECT COUNT(*) FROM snapshot INNER JOIN suspicious_records " \
          "ON snapshot.id = suspicious_records.ss_id;"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        re = cursor.fetchone()
    records_total = re[0]
    records_filtered = len(data)  # 指有前端有过滤条件时的记录数
    result = json_result("success", "查询成功:-)", draw=draw, data=data, recordsTotal=records_total,
                         recordsFiltered=records_total)
    return HttpResponse(result, content_type="application/json;charset=utf-8")


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

