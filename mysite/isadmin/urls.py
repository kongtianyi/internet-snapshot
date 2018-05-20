from django.conf.urls import url
from django.views.generic.base import RedirectView
from .views import user_views, db_views, report_views, vps_views, task_views, log_views, views


urlpatterns = {
    #  ====================================================================================
    # 前端界面
    url(r'^index$', views.index, name='index'),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/isadmin/images/favicon.ico')),
    # 用户相关
    url(r'^$', user_views.login, name='login'),
    url(r'^login$', user_views.login, name='login'),
    url(r'^register$', user_views.register, name='register'),
    url(r'^retrieve$', user_views.retrieve, name='retrieve'),
    # db管理
    url(r'^pubsoc_list$', db_views.pubsoc_list, name='pubsoc_list'),
    url(r'^prisoc_list$', db_views.prisoc_list, name='prisoc_list'),
    url(r'^malicious_domains_list$', db_views.malicious_domains_list, name='malicious_domains_list'),
    url(r'^snapshot_list$', db_views.snapshot_list, name='snapshot_list'),
    url(r'^suspicious_records_list$', db_views.suspicious_records_list, name='suspicious_record_list'),
    url(r'^pocr_list$', db_views.pocr_list, name='pocr_list'),
    url(r'^dcbp_list$', db_views.dcbp_list, name='dcbp_list'),
    # 快照展示
    url(r'^show_snapshot$', views.show_snapshot, name='show_snapshot'),
    url(r'^show_snapshot/(?P<id>[0-9]+)$', views.show_snapshot, name='show_snapshot'),
    # vps监控
    url(r'^vps_monitor$', vps_views.vps_monitor, name='vps_monitor'),
    url(r'^vps_monitor_reload$', vps_views.vps_monitor_reload, name='vps_monitor_reload'),
    url(r'^vps_detail$', vps_views.vps_detail, name='vps_detail'),
    url(r'^cpu_chart$', vps_views.cpu_chart, name='cpu_chart'),
    url(r'^memory_chart$', vps_views.memory_chart, name='memory_chart'),
    url(r'^disks_chart$', vps_views.disks_chart, name='disks_chart'),
    # 数据报表
    url(r'^report/redirect_records$', report_views.redirect_records, name='redirect_records'),
    url(r'^report/compare_unique$', report_views.compare_unique, name='compare_unique'),
    url(r'^report/filted_suspicious$', report_views.filted_suspicious, name='filted_suspicious'),
    # 一键功能
    url(r'^one_button$', views.one_button, name='one_button'),
    # 快照任务
    url(r'^add_task$', task_views.add_task, name='add_task'),
    url(r'^get_tasks$', task_views.get_tasks, name='get_tasks'),
    url(r'^edit_task$', task_views.edit_task, name='edit_task'),
    # 日志模块
    url(r'^history_log$', log_views.history_log, name='history_log'),
    url(r'^real_time_log$', log_views.real_time_log, name='real_time_log'),

    # ======================================================================================
    # 后端接口
    # 用户相关
    url('^login_action$', user_views.login_action, name='login_action'),
    url('^logout$', user_views.logout, name='logout'),
    url('^register_action$', user_views.register_action, name='register_action'),
    url('^invite_code_action$', user_views.invite_code_action, name='invite_code_action'),
    url('^retrieve_email_action$', user_views.retrieve_email_action, name='retrieve_email_action'),
    url('^retrieve_action$', user_views.retrieve_action, name='retrieve_action'),
    # CURD
    url(r'^pubsocs$', db_views.pubsocs, name='pubsocs'),
    url(r'^pubsocs/(?P<id>[0-9]+)$', db_views.pubsocs, name='pubsocs'),
    url(r'^pubsocs_jqgrid$', db_views.pubsocs_jqgrid, name='pubsocs_jqgrid'),
    url(r'^prisocs$', db_views.prisocs, name='prisocs'),
    url(r'^prisocs/(?P<id>[0-9]+)$', db_views.pubsocs, name='prisocs'),
    url(r'^prisocs_jqgrid$', db_views.prisocs_jqgrid, name='prisocs_jqgrid'),
    url(r'^malicious_domains/(?P<id>[0-9]+)$', db_views.malicious_domains, name='malicious_domains'),
    url(r'^malicious_domains_jqgrid$', db_views.malicious_domians_jqgrid, name='malicious_domains_jqgrid'),
    url(r'^snapshots$', db_views.snapshots, name='snapshots'),
    url(r'^snapshots/(?P<id>[0-9]+)$', db_views.snapshots, name='snapshots'),
    url(r'^snapshots_jqgrid$', db_views.snapshots_jqgrid, name='snapshots_jqgrid'),
    url(r'^suspicious_records$', db_views.suspicious_records, name='suspicious_records'),
    url(r'^suspicious_records/(?P<id>[0-9]+)$', db_views.suspicious_records, name='suspicious_records'),
    url(r'^suspicious_records_jqgrid$', db_views.suspicious_records_jqgrid, name='suspicious_records_jqgrid'),
    url(r'^pocr_records$', db_views.pocr_records, name='pocr_records'),
    url(r'^pocr_records/(?P<id>[0-9]+)$', db_views.pocr_records, name='pocr_records'),
    url(r'^pocr_jqgrid$', db_views.pocr_jqgrid, name='pocr_jqgrid'),
    url(r'^dcbps/(?P<id>[0-9]+)$', db_views.dcbps, name='dcbps'),
    url(r'^dcbps_jqgrid$', db_views.dcbps_jqgrid, name='dcbps_jqgrid'),
    # 数据报表
    url('^redirect_records_datas$', report_views.redirect_records_datas, name="redirect_records_datas"),
    url('^compare_unique_datas$', report_views.compare_unique_datas, name="compare_unique_datas"),
    url('^filted_suspicious_datas$', report_views.filted_suspicious_datas, name="filted_suspicious_datas"),
    # 人工后处理
    url(r'^check_compare_unique$', report_views.check_compare_unique, name="check_compare_unique"),
    url(r'^check_suspicious$', report_views.check_suspicious, name="check_suspicious"),
    # ssh
    url('^beat_start$', views.beat_start, name="beat_start"),
    url('^beat_stop$', views.beat_stop, name="beat_stop"),
    url('^beat_restart$', views.beat_restart, name="beat_restart"),
    # 快照任务
    url(r'^tasks$', task_views.tasks, name="tasks")
}
