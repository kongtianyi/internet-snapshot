from django.db.models import QuerySet
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from isadmin.models import Snapshot, SsHtml, SysUser
from isadmin.tools.html_util import HtmlUtil
from isadmin.tools.url_util import UrlUtil
from isadmin.tools.tools import get_ssh_connection, json_result
from isadmin.decorators import check_session, check_session_json
import platform
import logging


@check_session
def index(request):
    """首页-VPS监控"""
    if request.method != 'GET':
        return Http404
    nickname = request.session["nickname"]
    user = SysUser.objects.filter(nickname=nickname)[0]
    context = {
        "nickname": user.nickname
    }
    return render(request, 'isadmin/index.html', context=context)


@check_session
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


@check_session
def one_button(request):
    """一键功能页"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/one_button.html')


@check_session_json
@csrf_exempt
def beat_start(request):
    ip = settings.CELERY_BEAT_IP
    user = settings.CELERY_BEAT_USER
    password = settings.CELERY_BEAT_PW
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


@check_session_json
@csrf_exempt
def beat_stop(request):
    '''停止beat'''
    ip = settings.CELERY_BEAT_IP
    user = settings.CELERY_BEAT_USER
    password = settings.CELERY_BEAT_PW
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


@check_session_json
@csrf_exempt
def beat_restart(request):
    '''重启django-celery-beat使定时任务修改生效'''
    ip = settings.CELERY_BEAT_IP
    user = settings.CELERY_BEAT_USER
    password = settings.CELERY_BEAT_PW
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
