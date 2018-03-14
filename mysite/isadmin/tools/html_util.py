# -*- coding: utf-8 -*-

import re


class HtmlUtil:
    @classmethod
    def parse_protocol(cls, html, protocol):
        """处理“//xx.xx.xx”类型的链接（协议随页面）"""
        return re.sub('(?P<prefix>(=\s?["\'])|(url\(["\']?))'
                             '(?P<url>//(\w+(-\w+)*)(\.(\w+(-\w+)*))*(/\S+)*(\?\S*)?)'
                             '(?P<suffix>(["\'])|(["\']?\)))',
                             lambda m: m.group("prefix") + protocol
                                       + ':' + m.group("url") + m.group("suffix"),
                             html, flags=re.M)

    @classmethod
    def parse_dmain(cls, html, protocol, domain):
        """处理“/xx.xx”类型的链接（站点路径）"""
        return re.sub('(?P<prefix>(=\s?["\'])|(url\(["\']?))'
                             '(?P<url>/(\w+(-\w+)*)(\.(\w+(-\w+)*))*(/\S+)*(\?\S*)?)'
                             '(?P<suffix>(["\'])|(["\']?\)))',
                             lambda m: m.group("prefix") + protocol + "://"
                                       + domain + m.group("url")
                                       + m.group("suffix"),
                             html, flags=re.M)

    # todo this
    # html = re.sub('(?P<prefix>(=\s?["\'])|(url\(["\']?))'
    #               '(?P<url>(\w+(-\w+)*)(\.(\w+(-\w+)*))*(\?\S*)?)'
    #               '(?P<suffix>(["\'])|(["\']?\)))',
    #               lambda m: m.group("prefix") + get_path(self.downloader_item.final_url)
    #                         + '/' + m.group("url") + m.group("suffix"),
    #               html, flags=re.M)  # 处理“xx.xx”类型的链接（当前目录文件）


    @classmethod
    def parse_aim(cls, html, aim):
        """将目标域名下的外链高亮显示"""
        light = ' style="background: cyan"'  # 高亮的样式
        return re.sub('(?P<prefix><a(.*?)href=["\'](.*?)'+aim+'(.*?)["\'])',
               lambda m: m.group("prefix") + light,
               html, flags=re.M)
