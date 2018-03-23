# -*- encoding: utf-8 -*-


class MainItem():
    """各模块间传递的描述一个页面信息的对象"""
    def __init__(self, request_url, final_url=None, load_time=None, html=None, refer=None,
                 get_time=None, task_id=None, send_ip=None, server_ip=None):
        self.request_url = request_url  # 请求的url
        self.final_url = final_url  # 最终下载的url(可能存在重定向)
        # self.screen_shot = str()  # 页面首屏快照,base64, 太大了，不能存库
        self.load_time = load_time  # 页面首屏加载时间
        self.html = html  # 下载到的页面内容
        self.refer = refer  # 上级链接
        self.get_time = get_time  # 页面获取时间
        self.task_id = task_id  # 标识它所属的任务
        self.send_ip = send_ip  # 请求发送ip
        self.server_ip = server_ip  # 接受处理请求的ip(暂无来源)

    def save_tuple(self):
        """处理一下数据， 往mysql里插"""
        return (self.request_url, self.final_url, self.load_time,
                self.refer, self.get_time, self.task_id,
                self.send_ip, self.server_ip)


def main_item_to_json(obj):
    return {
        "request_url": obj.request_url,
        "final_url": obj.final_url,
        "load_time": obj.load_time,
        "html": obj.html,
        "refer": obj.refer,
        "get_time": obj.get_time,
        "task_id": obj.task_id,
        "send_ip": obj.send_ip,
        "server_ip": obj.server_ip
    }


def json_to_main_item(main_item_dict):
    return MainItem(main_item_dict["request_url"], main_item_dict["final_url"], main_item_dict["load_time"],
                    main_item_dict["html"], main_item_dict["refer"], main_item_dict["get_time"],
                    main_item_dict["task_id"], main_item_dict["send_ip"], main_item_dict["server_ip"])


class SsHtmlItem:
    """页面内容对象"""
    def __init__(self, ss_id, html):
        self.ss_id = ss_id
        self.html = html

    def save_tuple(self):
        html = self.html.replace("''", "'")
        return self.ss_id, html


class SuspiciousItem:
    """可疑记录对象"""
    def __init__(self, ss_id, unknown_domain, checked, result, check_time):
        self.ss_id = ss_id  # shapshot表中的id
        self.unknown_domain = unknown_domain  # 可疑外链主域名
        self.checked = checked  # 是否已人工检查，1已检查，0未检查
        self.result = result  # 检查结果, 1恶意信息，0误判, -1未检查
        self.check_time = check_time  # 人工检查时间

    def save_tuple(self):
        return (self.ss_id, self.unknown_domain, self.checked,
                self.result, self.check_time)


class PrivateOutChainRecordItem:
    """同url页面比对后产生的地区独有外链记录对象"""
    def __init__(self, ss_id, out_chain, checked, result, check_time):
        self.ss_id = ss_id  # shapshot表中的id
        self.out_chain = out_chain  # 可疑外链主域名
        self.checked = checked  # 是否已人工检查，1已检查，0未检查
        self.result = result  # 检查结果, 1恶意信息，0误判, -1未检查
        self.check_time = check_time  # 人工检查时间

    def save_tuple(self):
        return (self.ss_id, self.out_chain, self.checked,
                self.result, self.check_time)
