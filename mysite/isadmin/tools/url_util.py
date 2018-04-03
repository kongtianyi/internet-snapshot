# -*- coding: utf-8 -*-

from urllib import parse
from publicsuffix import fetch
from publicsuffix import PublicSuffixList
import codecs
import os


class UrlUtil:
    """封装一些关于url的操作"""
    # psl_file = fetch()  # 加载https://publicsuffix.org/list/public_suffix_list.dat

    psl_file = codecs.open(os.path.abspath(os.path.dirname(__file__)) + os.path.sep + 'public_suffix_list.dat', encoding='utf8')
    psl = PublicSuffixList(psl_file)

    @classmethod
    def get_protocol(cls, url):
        """抽取url的协议"""
        parse_result = parse.urlparse(url=url)
        return parse_result[0]

    @classmethod
    def get_domain(cls, url):
        """抽取url的域名"""
        parse_result = parse.urlparse(url=url)
        return parse_result[1]

    @classmethod
    def get_top_domain(cls, url):
        """抽取url的一级域名"""
        domain = UrlUtil.get_domain(url)
        domain = domain.split(':')[0]
        return cls.psl.get_public_suffix(domain)

    @classmethod
    def get_path(cls, url):
        """抽取url对应文件的路径（去掉文件本身）"""
        splites = url.split('/')
        if len(splites) == 3:
            return url
        elif len(splites) == 4 and splites[-1] == "":
            return url[:-1]
        return "/".join(url.split('/')[:-1])
