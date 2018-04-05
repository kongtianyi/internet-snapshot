# -*- encoding: utf-8 -*-

import pexpect


def get_ssh_connection(ip, user, password):
    """获取ssh链接"""
    child = pexpect.spawn("ssh %s@%s" % (user, ip))
    result = child.expect(["(yes/no)", "(.*?)password:"])
    if result == 0:
        child.sendline("yes")
        child.expect("(.*?)password:")
        child.sendline(password)
    elif result == 1:
        child.sendline(password)
    return child
