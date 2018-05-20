# -*- encoding: utf-8 -*-
import json
import random

import pexpect


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


def random_string(length=16):
    chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g',
             'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
             'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
             'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '@', '#', '$', '%', '^',
             '&', '*', '(', ')']
    result = ""
    for i in range(0, length):
        result += chars[random.randint(0, len(chars)-1)]
    return result


def get_ssh_connection(ip, user, password):
    """获取ssh链接"""
    child = pexpect.spawn("ssh %s@%s" % (user, ip), timeout=10)
    result = child.expect(["(yes/no)", "(.*?)password:"], timeout=5)
    if result == 0:
        child.sendline("yes")
        child.expect("(.*?)password:", timeout=5)
        child.sendline(password)
    elif result == 1:
        child.sendline(password)
    return child
