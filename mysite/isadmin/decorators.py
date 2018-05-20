# -*- encoding: utf-8 -*-

from django.http import HttpResponseRedirect, HttpResponse
from isadmin.tools.tools import json_result


def check_session(func):
    '''检查是否有登陆状态'''
    def _check_session(request, *args, **kwargs):
        if request.session.get("nickname", None):
            response = func(request, *args, **kwargs)
        else:
            response = HttpResponseRedirect('/isadmin/login')
        return response
    return _check_session


def check_session_json(func):
    """检查是否有登陆态，返回json数据，适用于返回json数据的后端接口"""
    def _check_session_json(request, *args, **kwargs):
        if request.session.get("nickname", None):
            response = func(request, *args, **kwargs)
        else:
            result = json_result("error", "未检查到登陆态:-(")
            response = HttpResponse(result, content_type="application/json;charset=utf-8")
        return response
    return _check_session_json

