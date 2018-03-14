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
    url(r'^add_pubsoc$', views.add_pubsoc, name='add_pubsoc'),
    url(r'^add_prisoc$', views.add_prisoc, name='add_prisoc'),
    url(r'^show_snapshot$', views.show_snapshot, name='show_snapshot'),
    url(r'^show_snapshot/(?P<id>[0-9]+)$', views.show_snapshot, name='show_snapshot'),
    url(r'^dashboard$', views.dashboard, name='dashboard'),

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
}