#!/bin/bash

PROCESS_NAME=$1
echo $PROCESS_NAME
ID=`ps -ef | grep "$PROCESS_NAME" | grep -v "grep" | awk '{print $2}'`
echo "$PROCESS_NAME has ids: $ID"
echo "---------------"
for id in $ID
do
	echo "killed $id"
	kill -9 $id
done
echo "---------------"