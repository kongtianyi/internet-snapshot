import hashlib
import time
import logging
import pyDes
import base64
import urllib.parse
from django.db.models import F
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings

from isadmin.models import SysUser, Invite
from isadmin.tools.tools import random_string, json_result


def login(request):
    """用户-登陆"""
    if request.method != 'GET':
        return Http404()
    if request.session.get("nickname", None):
        return HttpResponseRedirect('/isadmin/index')
    return render(request, 'isadmin/user/login.html')


def register(request):
    """用户-注册"""
    if request.method != 'GET':
        return Http404
    return render(request, 'isadmin/user/register.html')


def retrieve(request):
    """用户-重置密码"""
    if request.method != 'GET':
        return Http404()
    token = request.GET.get("token", None)
    context = {
        "token": token
    }
    if token is None:
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/user/retrieve.html', context=context)


@csrf_exempt
def login_action(request):
    """处理登陆请求"""
    if request.method != "POST":
        return render(request, 'isadmin/error/error-403.html')
    nickname = request.POST.get("nickname")
    password = request.POST.get("password")
    remain = request.POST.get("remain")
    user = SysUser.objects.filter(nickname=nickname)
    if user is None or len(user) == 0:
        result = json_result("error", "用户不存在")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    salt = user[0].salt
    real_password = user[0].pw
    # 创建md5对象
    hl = hashlib.md5()
    hl.update((password+salt).encode(encoding='utf-8'))
    if real_password == hl.hexdigest():
        half_hour = 60 * 30
        seven_days = 60 * 60 * 24 * 7
        if int(remain) == 0:
            request.session.set_expiry(half_hour)
        else:
            request.session.set_expiry(seven_days)
        request.session["id"] = user[0].id
        request.session["nickname"] = nickname
        result = json_result("success", "登陆成功。")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    else:
        result = json_result("error", "密码错误，请重试。")
        return HttpResponse(result, content_type='application/json;charset=utf-8')


@csrf_exempt
def logout(request):
    request.session.clear()
    return render(request, 'isadmin/user/login.html')


@csrf_exempt
def register_action(request):
    """处理注册请求"""
    if request.method != "POST":
        return render(request, 'isadmin/error/error-403.html')
    nickname = request.POST.get("nickname")
    email = request.POST.get("email")
    invite_code = request.POST.get("invite_code")
    password = request.POST.get("password")
    repeat_password = request.POST.get("repeat_password")

    if password != repeat_password:
        result = json_result("error", "两次输入密码不一致")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    user = SysUser.objects.filter(nickname=nickname)
    if user is not None and len(user) > 0:
        result = json_result("error", "用户名已存在")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    user = SysUser.objects.filter(email=email)
    if user is not None and len(user) > 0:
        result = json_result("error", "Email已与其它账户关联")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    invite = Invite.objects.filter(invite_code=invite_code)[0]
    if invite is None or invite.left_time < 1:
        result = json_result("error", "邀请码已失效")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    Invite.objects.filter(invite_code=invite_code).update(left_time=F("left_time")-1)
    salt = random_string()
    # 创建md5对象
    hl = hashlib.md5()
    hl.update((password + salt).encode(encoding='utf-8'))
    real_password = hl.hexdigest()

    item = SysUser.objects.create(nickname=nickname, pw=real_password, salt=salt, icon="/default.png", email=email)
    if item is None:
        result = json_result("error", "服务器错误，请重试")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    result = json_result("success", "注册成功")
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def invite_code_action(request):
    inviter_id = request.POST.get("inviter_id", None)
    left_time = request.POST.get("left_time", 1)
    invite_code = random_string()
    try:
        Invite.objects.create(inviter_id=inviter_id, invite_code=invite_code, left_time=left_time)
    except Exception as e:
        logging.error("When create invite entity, %s occurred." % (e.__class__,))
        result = json_result("error", "数据库错误")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    result = json_result("success", "生成邀请码成功", invite_code=invite_code)
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def retrieve_email_action(request):
    """处理发送重置密码邮件请求"""
    if request.method != "POST":
        return render(request, 'isadmin/error/error-403.html')
    email = request.POST.get("email")
    user = SysUser.objects.filter(email=email)
    if user is None or len(user) == 0:
        result = json_result("error", "该邮箱没有注册过本系统。")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    now = str(int(time.time()))
    triple_des = pyDes.triple_des(settings.DES_KEY, padmode=pyDes.PAD_PKCS5)
    encrypt = triple_des.encrypt(email + '+' + now)  # 3DES加密
    token = base64.b64encode(encrypt).decode()  # base64加密解码成字符串
    token = urllib.parse.quote(token)  # 避免特殊字符如+丢失
    msg = '''
    <table cellpadding="0" cellspacing="0" width="100%" style="max-width:744px; border: 1px solid #dedede;border-radius: 3px">
      <tbody><tr>
      <td style="padding: 10px 20px 10px 20px;">
      <table border="0" cellpadding="0" cellspacing="0" width="100%">
      <tbody><tr>
        <td align="left" style="font-size: 17px; padding:20px 0 10px 0;">
          <b>亲爱的''' + user[0].nickname + '''：</b>
        </td>
      </tr>
      <tr>
        <td align="left" style="font-size:15px; padding: 10px 0px 10px 0px;">
          你的密码重设要求已经得到验证。请点击以下按钮设置新的密码：
        </td>
      </tr>
      <tr>
        <td align="center" style="padding: 10px 0px 10px 0px;">
          <table border="0" cellpadding="0" cellspacing="0">
            <tbody><tr>
              <td>
                <div style="font-size:20px;font-weight:700;padding:5px 10px 5px 10px;text-align:center;background-color:#3aa252;border-radius: 3px;">
                  <a href="''' + settings.RETRIEVE_ADDRESS + '''?token=''' + token + ''''" class="button" style="text-decoration: none;color:white;" target="_blank">重设密码</a>
                </div>
              </td>
            </tr>
          </tbody></table>
        </td>
      </tr>
      <tr>
        <td align="left" style="font-size:15px; padding: 10px 0px 10px 0px;">
          感谢你对互联网站点劫持检测系统的支持，希望你在互联网站点劫持检测系统的体验有益且愉快。
        </td>
      </tr>
      <tr>
        <td align="left" style="font-size:15px; padding: 10px 0px 10px 0px;">
          互联网站点劫持检测系统 <a href="http://''' + settings.SITE_DOMAIN + '''/isadmin" target="_blank">https://''' + settings.SITE_DOMAIN + '''/isadmin</a>
        </td>
      </tr>
      <tr>
        <td align="left" style="font-size:15px; padding: 10px 0px 10px 0px;">
            (这是一封自动产生的email，请勿回复。)
        </td>
      </tr>
    </tbody></table>
        </td>
      </tr>
    </tbody></table>
    '''
    try:
        send_mail('密码重置链接', '', settings.EMAIL_FROM, [email, ], html_message=msg)
    except Exception as e:
        result = json_result("error", "邮件发送失败")
        logging.error("When sent retrieve email, error %s occurred." % (e.__class__, ))
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    result = json_result("success", "邮件发送成功")
    return HttpResponse(result, content_type="application/json;charset=utf-8")


@csrf_exempt
def retrieve_action(request):
    """处理重置密码请求"""
    if request.method != "POST":
        return render(request, 'isadmin/error/error-403.html')
    token = request.POST.get("token")
    password = request.POST.get("password")
    repeat_password = request.POST.get("repeat_password")
    token = urllib.parse.unquote(token)
    encrypt = base64.b64decode(token)  # base64解密
    triple_des = pyDes.triple_des(settings.DES_KEY, padmode=pyDes.PAD_PKCS5)
    decrypt = triple_des.decrypt(encrypt).decode("utf-8")  # 3DES解密
    try:
        email = decrypt.split('+')[0]
        token_time = int(decrypt.split('+')[1])
        user = SysUser.objects.filter(email=email)
        if user is None:
            raise Exception()
    except:
        result = json_result("error", "重置密码链接有误，请勿更改邮件内链接。")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    if int(time.time()) - token_time > 3600:
        # 邮件已发出一小时，token失效
        result = json_result("error", "token已超时，请重新申请重置密码邮件。")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    if password != repeat_password:
        result = json_result("error", "两次输入的密码不一致。")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    salt = random_string()
    # 创建md5对象
    hl = hashlib.md5()
    hl.update((password + salt).encode(encoding='utf-8'))
    real_password = hl.hexdigest()
    try:
        row = user.update(pw=real_password, salt=salt)
        if row == 0:
            raise Exception()
    except:
        result = json_result("error", "重置密码失败。")
        return HttpResponse(result, content_type="application/json;charset=utf-8")
    result = json_result("success", "重置密码成功。")
    return HttpResponse(result, content_type="application/json;charset=utf-8")




