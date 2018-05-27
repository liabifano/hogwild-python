#!/usr/bin/env bash

APP_NAME=hogwild
REPO=liabifano
KUBER_LOGIN=cs449g9

DATA_PATH=/data/datasets

while getopts ":n:r:f:w:" opt; do
  case $opt in
    n) N_WORKERS="$OPTARG";; # number workers
    r) RUNNING_MODE="$OPTARG";; # synchronous or asynchronous
    f) FILE_LOG="$OPTARG";; # file where the output of the job will be stored
    w) WHERE="$OPTARG";;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

if [[ $WHERE = "local" ]];
then
    bash run-local.sh
    exit 0
fi;


function shutdown_infra {
    if ! [[ -z $(kubectl get services | grep coordinator-service-lia) ]];
    then
        kubectl delete -f Kubernetes/coordinator.yaml --cascade=true
    fi;

    if ! [[ -z $(kubectl get services | grep workers-service-lia) ]];
    then
        kubectl delete -f Kubernetes/workers.yaml --cascade=true
    fi;

    if ! [[ -z $(kubectl get configmap | grep hogwild-config-lia) ]];
    then
        kubectl delete configmap hogwild-config-lia
    fi;
}

echo
echo "----- Logging in Docker Hub -----"
docker login --username=$DOCKER_USER --password=$DOCKER_PASS 2> /dev/null

echo
echo "----- Deleting remaining infra -----"
shutdown_infra

echo
echo "----- Starting workers -----"
kubectl create configmap hogwild-config-lia --from-literal=replicas=${N_WORKERS} \
                                            --from-literal=running_mode=${RUNNING_MODE} \
                                            --from-literal=data_path=${DATA_PATH} \
                                            --from-literal=running_where=${WHERE}
sed "s/\(replicas:\)\(.*\)/\1 ${N_WORKERS}/" Kubernetes/workers_template.yaml > Kubernetes/workers.yaml
kubectl create -f Kubernetes/workers.yaml

while [ $(kubectl get pods | grep worker | grep Running | wc -l) != ${N_WORKERS} ]
do
    sleep 1
done

echo
echo
echo "----- Workers are up and running, starting coordinator -----"
kubectl create -f Kubernetes/coordinator.yaml


while [ $(kubectl get pods | grep coordinator | grep Running | wc -l) == 0 ]
do
    sleep 1
done

echo
echo "----- Running Job -----"


MY_TIME="`date +%Y%m%d%H%M%S`" && kubectl cp coordinator-0:log.json logs/log_${MY_TIME}.json 2> /dev/null
while [ $? -ne 0 ];
do
    sleep 0.1
    MY_TIME="`date +%Y%m%d%H%M%S`" && kubectl cp coordinator-0:log.json logs/log_${MY_TIME}.json 2> /dev/null
done


echo
echo "----- Job Completed, writing log -----"


if [[ -z $(ls logs | grep ${FILE_LOG}) ]];
then
    touch logs/${FILE_LOG}
fi;

echo $(jq -s add logs/${FILE_LOG} logs/log_${MY_TIME}.json) > logs/${FILE_LOG}
rm logs/log_${MY_TIME}.json

echo
echo "----- Logs available in ${FILE_LOG} -----"

echo
#echo "----- Shutting down monitoring -----"
#kill -9 $(ps -a | grep monitor-it |  awk '{print $1}' | head -n 1)

echo
echo "----- Shutting down infra -----"
shutdown_infra

# useful commands
#kubectl delete po,svc --all
#docker build -f `pwd`/Docker/coordinator/Dockerfile `pwd` -t ${REPO}/${APP_NAME}_coordinator
#docker push ${REPO}/hogwild_coordinator
## Create `pod` in the cluster
#kubectl create -f ./Kubernetes/hog-pod.yaml
#kubectl describe pod/${APP_NAME} -n ${KUBER_LOGIN}
# kubectl logs $APP_NAME -p --container="coordinator"
#kubectl -n my-ns delete po,svc --all
#kubectl delete -f Kubernetes/workers_template.yaml --cascade=true
#kubectl exec -it coordinator-0 -- /bin/bash


# ➝  kubectl scale --replicas=3 service/workers-service
#error: Scaling the resource failed with: could not fetch the scale for services workers-service: services "workers-service" is forbidden: User "cs449g9" cannot get services/scale in the namespace "cs449g9"
