#!/bin/bash

nohup websocketd --port 8080 python websocket.py >> websocketd.log 2>&1 &