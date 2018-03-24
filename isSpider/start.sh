#!/bin/bash

echo "Please enter queue's name that this worker will subscribe(ex. beijing_queue):"
read queue_name
echo "Please enter hostname of this worker(ex. jdcloud):"
read hostname
log_file_name="./"${queue_name}".log"
pid_file_name="./"${queue_name}".pid"
celery worker -A tasks -Q ${queue_name} -D -c 1 -l info -n ${hostname} -f ${log_file_name} --heartbeat-interval=60 --pidfile=${pid_file_name}
