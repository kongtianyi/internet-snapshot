/**
 * Created by kongwei on 2018/5/21.
 */
function isEmail(str){
    // todo 搞明白这个'.'为什么不能放在最后边
    // 加上这个'.'是因为gmail确实有这种帐号
    var reg = /^([a-zA-Z0-9_.-])+@([a-zA-Z0-9_-])+(\.[a-zA-Z0-9_-])+/;
    return reg.test(str);
}