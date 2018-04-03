from django.conf.urls import url
from . import views

urlpatterns = {
    # 前端界面
    url(r'^$', views.index, name='index'),
    url(r'^index$', views.index, name='index'),
    url(r'^pubsoc_list$', views.pubsoc_list, name='pubsoc_list'),
    url(r'^prisoc_list$', views.prisoc_list, name='prisoc_list'),
    url(r'^snapshot_list', views.snapshot_list, name='snapshot_list'),
    url(r'^suspicious_records_list', views.suspicious_records_list, name='suspicious_record_list'),
    # 快照展示
    url(r'^show_snapshot$', views.show_snapshot, name='show_snapshot'),
    url(r'^show_snapshot/(?P<id>[0-9]+)$', views.show_snapshot, name='show_snapshot'),
    # vps监控
    url(r'^vps_monitor$', views.vps_monitor, name='vps_monitor'),
    url(r'^vps_monitor_reload$', views.vps_monitor_reload, name='vps_monitor_reload'),
    url(r'^vps_detail$', views.vps_detail, name='vps_detail'),
    url(r'cpu_chart$', views.cpu_chart, name='cpu_chart'),
    url(r'memory_chart', views.memory_chart, name='memory_chart'),
    url(r'disks_chart', views.disks_chart, name='disks_chart'),
    # 数据报表
    url(r'^report/redirect_records$', views.redirect_records, name='redirect_records'),
    url(r'^report/compare_unique$', views.compare_unique, name='compare_unique'),
    url(r'^report/filted_suspicious$', views.filted_suspicious, name='filted_suspicious'),


    # CURD
    url(r'^pubsocs$', views.pubsocs, name='pubsocs'),
    url(r'^pubsocs/(?P<id>[0-9]+)$', views.pubsocs, name='pubsocs'),
    url(r'^pubsocs_jqgrid$', views.pubsocs_jqgrid, name='pubsocs_jqgrid'),
    url(r'^prisocs$', views.prisocs, name='prisocs'),
    url(r'^prisocs/(?P<id>[0-9]+)$', views.pubsocs, name='prisocs'),
    url(r'^prisocs_jqgrid$', views.prisocs_jqgrid, name='prisocs_jqgrid'),
    url(r'^snapshots$', views.snapshots, name='snapshots'),
    url(r'^snapshots/(?P<id>[0-9]+)$', views.snapshots, name='snapshots'),
    url(r'^snapshots_jqgrid$', views.snapshots_jqgrid, name='snapshots_jqgrid'),
    url(r'^suspicious_records$', views.suspicious_records, name='suspicious_records'),
    url(r'^suspicious_records/(?P<id>[0-9]+)$', views.suspicious_records, name='suspicious_records'),
    url(r'^suspicious_records_jqgrid$', views.suspicious_records_jqgrid, name='suspicious_records_jqgrid'),
    # 数据报表
    url('^redirect_records_datas$', views.redirect_records_datas, name="redirect_records_datas"),
    url('^compare_unique_datas$', views.compare_unique_datas, name="compare_unique_datas"),
    url('^filted_suspicious_datas$', views.filted_suspicious_datas, name="filted_suspicious_datas"),
}

if __name__ == "__main__":
    import psutil
    psutil.net_io_counters()