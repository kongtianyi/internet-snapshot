import time

from django.db import connection
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from isadmin.decorators import check_session, check_session_json
from isadmin.models import Snapshot, SuspiciousRecords, MaliciousDomains, PublicSafeOutChains, PrivateSafeOutChains, \
    PrivateOutChainRecords
from isadmin.tools.tools import json_result
from isadmin.tools.url_util import UrlUtil


@check_session
def redirect_records(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/report/redirect_records.html')


@check_session
def compare_unique(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/report/compare_unique.html')


@check_session
def filted_suspicious(request):
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/report/filted_suspicious.html')


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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
