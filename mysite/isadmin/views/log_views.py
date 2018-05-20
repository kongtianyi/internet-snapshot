from django.shortcuts import render

from isadmin.decorators import check_session


@check_session
def history_log(request):
    """历史日志查询页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/log/history_log.html')


@check_session
def real_time_log(request):
    """实时日志查询页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/log/real_time_log.html')