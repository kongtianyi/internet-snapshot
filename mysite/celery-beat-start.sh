#!/bin/bash

celery -A mysite beat -l info -S django_celery_beat.schedulers:DatabaseScheduler --detach -f ./celery-beat-log.log