import math

import time
from django.db.models import QuerySet
from django.http import HttpResponse
from django.http import QueryDict
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django_celery_beat.models import PeriodicTask

from isadmin.decorators import check_session, check_session_json
from isadmin.models import SuspiciousRecords, to_json_dict, PublicSafeOutChains, PrivateSafeOutChains, MaliciousDomains, \
    Snapshot, PrivateOutChainRecords
from isadmin.tools.tools import json_result


@check_session
def pubsoc_list(request):
    """公共正常外链列表页面"""
    if request.method != 'GET':
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/pubsoc_list.html')


@check_session
def prisoc_list(request):
    """私有正常外链列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/prisoc_list.html')


@check_session
def malicious_domains_list(request):
    """恶意外链列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/malicious_domains_list.html')


@check_session
def snapshot_list(request):
    """网页快照列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/snapshot_list.html')


@check_session
def suspicious_records_list(request):
    """可疑外链列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/suspicious_records_list.html')


@check_session
def pocr_list(request):
    """比对结果列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/pocr_list.html')


@check_session
def dcbp_list(request):
    """定时任务列表页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-404.html')
    return render(request, 'isadmin/db/dcbp_list.html')


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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


@check_session_json
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