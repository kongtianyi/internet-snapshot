# -*- coding: utf-8 -*-

from BloomFilter import GeneralHashFunctions


class BloomFilter:
    hash_list = ["rs_hash", "js_hash", "pjw_hash", "elf_hash", "bkdr_hash",
                 "sdbm_hash", "djb_hash", "dek_hash"]

    def __init__(self, size, hash_list=hash_list):
        self.size = size
        # 哈希函数列表
        self.hash_list = hash_list
        # 位数组
        self.bitmap = [0 for i in range(0, self.size)]

    def random_generator(self, hash_value):
        '''
        将hash函数得出的函数值映射到[0, size]区间内
        '''
        return hash_value % self.size

    def do_filter(self, item):
        '''
        检查是否是新的条目，是新条目则更新并返回True，是重复条目则返回False
        '''
        flag = False
        for hash_func_str in self.hash_list:
            # 获得到hash函数对象
            hash_func = getattr(GeneralHashFunctions, hash_func_str)
            # 计算hash值
            hash_value = hash_func(item)
            # 将hash值映射到[0, size]区间
            real_value = self.random_generator(hash_value)
            # bitmap中对应位是0，则置为1，并说明此条目为新的条目
            if self.bitmap[real_value] == 0:
                self.bitmap[real_value] = 1
                flag = True
        # 当所有hash值在bitmap中对应位都是1，说明此条目重复，返回False
        return flag


if __name__ == "__main__":
    bloomFilter = BloomFilter(1 << 27)
    bloomFilter.do_filter("one item to check")