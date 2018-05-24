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
        _id = ' id="aim_point"'
        left_index = html.find(aim)
        right_index = html.rfind(aim)
        if left_index == -1:  # 说明页面内没有传入外链
            return html
        # 边界判断
        sub_start = left_index-100 if left_index > 100 else 0
        sub_end = right_index+100 if right_index+100 < len(html) else len(html)-1
        # 分割
        left_html = html[:sub_start]
        sub_html = html[sub_start: sub_end]
        right_html = html[sub_end:]
        # 只对包含目标的区域正则替换，不然太耗时
        sub_html = re.sub('(?P<prefix><a(.*?)href=["\'](.*?)'+aim+'(.*?)["\'])',
               lambda m: m.group("prefix") + light + _id,
               sub_html, flags=re.M)
        return left_html + sub_html + right_html
