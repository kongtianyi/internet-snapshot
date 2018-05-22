#!/usr/bin/python
# -*- encoding: utf-8 -*-

from sys import stdin
from sys import stdout
import time
import re


def tail(file, taillines=500, return_str=True, avg_line_length=None):
    """avg_line_length:每行字符平均数,
    return_str:返回类型，默认为字符串，False为列表。
    offset:每次循环相对文件末尾指针偏移数"""
    with open(file, errors='ignore') as f:
        if not avg_line_length:
            f.seek(0, 2)
            f.seek(f.tell() - 3000)
            avg_line_length = int(3000 / len(f.readlines())) + 10
        f.seek(0, 2)
        end_pointer = f.tell()
        offset = taillines * avg_line_length
        if offset > end_pointer:
            f.seek(0, 0)
            lines = f.readlines()[-taillines:]
            return "".join(lines) if return_str else lines
        offset_init = offset
        i = 1
        while len(f.readlines()) < taillines:
            location = f.tell() - offset
            f.seek(location)
            i += 1
            offset = i * offset_init
            if f.tell() - offset < 0:
                f.seek(0, 0)
                break
        else:
            f.seek(end_pointer - offset)
        lines = f.readlines()
        if len(lines) >= taillines:
            lines = lines[-taillines:]

        return "".join(lines) if return_str else lines

file_path = "/home/internet-snapshot/"
file_name = stdin.readline()[:-1]
while True:
    front_sent = stdin.readline()[:-1]  # 前端传来的时间或终止信号
    if front_sent == "stop":
        break
    file_tail = tail(file_path + file_name, taillines=200)
    date_pattern = "^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
    if not re.match(date_pattern, front_sent):
        stdout.write("Date format error.")
        stdout.flush()
        break
    now = time.mktime(time.strptime(front_sent, '%Y-%m-%d %H:%M:%S'))
    last_second = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now-5))  # 前端传过来那一时刻的上五秒
    first_index = file_tail.find(last_second)-1  # 这一秒的第一条记录起点
    if first_index == -2:
        continue
    last_index = file_tail.rfind(last_second)  # 这一秒的最后一条记录起点
    end_index = file_tail.find("\n", last_index)  # 这一秒的最后一条记录终点
    if end_index == -1:
        end_index = len(file_tail)
    stdout.write(file_tail[first_index: end_index+1])
    stdout.flush()
