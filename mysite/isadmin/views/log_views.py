from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from isadmin.decorators import check_session, check_session_json
from isadmin.models import Vps, LogFiles
from isadmin.tools.tools import json_result


@check_session
def real_time_log(request):
    """实时日志查询页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    vpss = Vps.objects.all()
    vps_ips = list()
    for vps in vpss:
        vps_ips.append(vps.ip)
    context = {
        "vps_ips": vps_ips
    }
    return render(request, 'isadmin/log/real_time_log.html', context=context)


@csrf_exempt
@check_session_json
def get_log_files(request):
    ip = request.POST.get("ip")
    vps = Vps.objects.filter(ip=ip)
    if vps is None or len(vps) == 0:
        result = json_result("error", "该服务器ip不存在。")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    log_files = LogFiles.objects.filter(vps_id=vps[0].id)
    data = [log_file.path+log_file.filename for log_file in log_files]
    result = json_result("success", "查询成功", data=data)
    return HttpResponse(result, content_type="application/json;charset=utf-8")

