#!/bin/bash

echo "Please enter queue's name that this worker will subscribe(ex. beijing_queue):"
read queue_name
echo "Please enter hostname of this worker(ex. jdcloud):"
read hostname
$log_file_name=${queue_name}".log"
celery -A tasks -Q $queue_name -D worker -c 1 -l info -n $hostname --heartbeat-interval 60 -f $log_file_name