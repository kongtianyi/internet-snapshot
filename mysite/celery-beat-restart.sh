#!/bin/bash

ID=`ps -ef | grep django_celery_beat | grep -v "grep" | awk '{print $2}'`
echo "django_celery_beat has ids: $ID"
for id in $ID
do
	echo "killed $id"
	kill -9 $id
done
rm ./*.pid
celery -A mysite beat -l info -S django_celery_beat.schedulers:DatabaseScheduler --detach -f ./celery-beat-log.log
