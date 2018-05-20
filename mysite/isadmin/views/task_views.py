import json

import time
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from isadmin.decorators import check_session, check_session_json
from isadmin.tools.tools import json_result


@check_session
def add_task(request):
    """增加定时快照任务页面"""
    if request.method != "GET":
        return render(request, 'isadmin/error/error-403.html')
    return render(request, 'isadmin/task/add_task.html')


@check_session
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


@check_session
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


@check_session_json
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