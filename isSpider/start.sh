#!/bin/bash

echo "Please select(or input) queue's name that this worker will subscribe:"
echo -e "1. default_queue\t2. parse_queue"
echo -e "3. beijing_queue\t4. beijing_download_queue"
echo -e "5. shenzhen_queue\t6. shenzhen_download_queue"
echo -e "7. chengdu_queue\t8. chengdu_download_queue"
read select_num
case $select_num in
    1) queue_name="default_queue";;
    2) queue_name="parse_queue";;
    3) queue_name="beijing_queue";;
    4) queue_name="beijing_download_queue";;
    5) queue_name="shenzhen_queue";;
	6) queue_name="shenzhen_download_queue";;
	7) queue_name="chengdu_queue";;
	8) queue_name="chengdu_download_queue";;
    *) queue_name=${select_num};;
esac
echo "Please enter hostname of this worker(ex. jdcloud):"
read hostname
log_file_name="./"${queue_name}".log"
pid_file_name="./"${queue_name}".pid"
celery worker -A tasks -Q ${queue_name} -D -c 1 -l info -n ${hostname} -f ${log_file_name} --heartbeat-interval=60 --pidfile=${pid_file_name}
