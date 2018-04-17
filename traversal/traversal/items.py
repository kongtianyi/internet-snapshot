# -*- coding: utf-8 -*-

from scrapy import Item
from scrapy import Field


class TraversalItem(Item):
    url = Field()  # url
    status = Field()  # 状态码
    refer = Field()  # 上级页面
    depth = Field()  # 广度优先的深度
    get_time = Field()  # 获取的时间
    inner_chains_num = Field()  # 内链数量

    def save_tuple(self):
        return self["url"], self["status"], self["refer"], self["depth"], self["get_time"], self["inner_chains_num"]
