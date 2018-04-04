#!/bin/bash

echo "Please select(or input) the process's name that you want to kill:"
echo -e "1. celery\t2. geckodriver"
echo -e "3. firefox\t4. all of the above"
read select_num
if [ $select_num != "4" ]
then
	case $select_num in
		1) PROCESS_NAME="celery";;
		2) PROCESS_NAME="geckodriver";;
		3) PROCESS_NAME="firefox";;
	esac
	ID=`ps -ef | grep "$PROCESS_NAME" | grep -v "grep" | awk '{print $2}'`
	echo "$PROCESS_NAME has ids: $ID"
	echo "---------------"
	for id in $ID
	do
		echo "killed $id"
		kill -9 $id
	done
	echo "---------------"
else
	ID=`ps -ef | grep celery | grep -v "grep" | awk '{print $2}'`
	echo "celery has ids: $ID"
	echo "---------------"
	for id in $ID
	do
		echo "killed $id"
		kill -9 $id
	done
	echo "---------------"
	ID=`ps -ef | grep geckodriver | grep -v "grep" | awk '{print $2}'`
	echo "geckodriver has ids: $ID"
	echo "---------------"
	for id in $ID
	do
		echo "killed $id"
		kill -9 $id
	done
	echo "---------------"
	ID=`ps -ef | grep firefox | grep -v "grep" | awk '{print $2}'`
	echo "firefox has ids: $ID"
	echo "---------------"
	for id in $ID
	do
		echo "killed $id"
		kill -9 $id
	done
	echo "---------------"
fi