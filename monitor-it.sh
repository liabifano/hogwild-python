#!/usr/bin/env bash

while [ $(kubectl get pods | grep coordinator | awk '{print $5}' = "3m") ]
do
    sleep 5
done

kill -9 $(ps -a | grep run-in-cluster |  awk '{print $1}' | head -n 1)