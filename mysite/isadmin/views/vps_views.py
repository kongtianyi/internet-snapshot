import json

import time
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render

from isadmin.decorators import check_session
from isadmin.models import Vps, VpsStatus
from isadmin.tools.tools import byte_to_gb, float_to_percent, json_result


@check_session
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


@check_session
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


@check_session
def vps_detail(request):
    if request.method != "GET":
        return render(request, "isadmin/error/error-403.html")
    vps_id = request.GET.get("vps_id")
    context = {
        "vps_id": vps_id,
    }
    return render(request, "isadmin/monitor/vps_detail.html", context=context)


@check_session
def cpu_chart(request):
    """cpu利用率走势"""
    vps_id = request.GET.get("vps_id")
    try:
        vps_status_count = VpsStatus.objects.filter(vps_id=vps_id).count()
        start_index = vps_status_count-288 if vps_status_count > 288 else 0
        vps_statuses = VpsStatus.objects.filter(vps_id=vps_id)[start_index:]
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


@check_session
def memory_chart(request):
    """内存利用率走势"""
    vps_id = request.GET.get("vps_id")
    try:
        vps = Vps.objects.filter(id=vps_id)
        vps_status_count = VpsStatus.objects.filter(vps_id=vps_id).count()
        start_index = vps_status_count-288 if vps_status_count>288 else 0
        vps_statuses = VpsStatus.objects.filter(vps_id=vps_id)[start_index:]
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


@check_session
def disks_chart(request):
    """磁盘剩余量走势"""
    vps_id = request.GET.get("vps_id")
    try:
        vps = Vps.objects.filter(id=vps_id)
        vps_status_count = VpsStatus.objects.filter(vps_id=vps_id).count()
        start_index = vps_status_count-288 if vps_status_count>288 else 0
        vps_statuses = VpsStatus.objects.filter(vps_id=vps_id)[start_index:]
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
