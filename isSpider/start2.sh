#!/bin/bash

echo "You are starting a worker who handled default_queue's tasks."
nohup celery -A tasks -Q default_queue worker --loglevel=info --hostname=default --without-heartbeat >> default_queue.log 2>&1 &