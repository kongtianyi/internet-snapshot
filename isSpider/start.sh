#!/bin/bash

IP_PATTERN="^[0-9]{0,3}\.[0-9]{0,3}\.[0-9]{0,3}\.[0-9]{0,3}$"
echo "You are starting a downloader worker."
echo "Please enter this VPS's ip address(ex.114.67.225.0):"
read ip
while [[ ! $ip =~ $IP_PATTERN ]];do
	echo "Input string not match an ip address!"
	echo "Please enter this VPS's ip address(ex.114.67.225.0):"
	read ip
done
echo "Please enter this VPS's geography address(ex. 北京):"
read address
echo -e "{\n\t\"local_ip\": \"$ip\",\n\t\"local_address\": \"$address\"\n}" > ext_conf.json
echo "Please enter queue's name that this worker will subscribe(ex. beijing_queue):"
read queue_name
echo "Please enter hostname of this worker(ex. jdcloud):"
read hostname
nohup celery -A tasks -Q $queue_name worker -c 1 --loglevel=info --hostname=$hostname --without-heartbeat >> worker.log 2>&1 &