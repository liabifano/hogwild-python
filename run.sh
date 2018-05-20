#!/usr/bin/env bash

set -eo pipefail

APP_NAME=hogwild
REPO=liabifano
KUBER_LOGIN=cs449g9
N_WORKERS=5
DATA_PATH=data/datasets
RUNNING_MODE=synchronous

# Don't forget to run login first with `docker login`
docker login --username=$DOCKER_USER --password=$DOCKER_PASS

# Delete services if exists
if ! [[ -z $(kubectl get services | grep workers-service) ]];
then
    kubectl delete -f Kubernetes/workers.yaml --cascade=true
fi;

if ! [[ -z $(kubectl get services | grep coordinator-service) ]];
then
    kubectl delete -f Kubernetes/coordinator.yaml --cascade=true
fi;

if ! [[ -z $(kubectl get configmap | grep hogwild-config) ]];
then
    kubectl delete configmap hogwild-config
fi;

# build docker images
docker build -f `pwd`/Docker/Dockerfile `pwd` -t ${REPO}/${APP_NAME}
docker push ${REPO}/${APP_NAME}

# generate configmap
kubectl create configmap hogwild-config --from-literal=replicas=${N_WORKERS} \
                                        --from-literal=running_mode=${RUNNING_MODE} \
                                        --from-literal=data_path==${DATA_PATH}


# create workers service
kubectl create -f Kubernetes/workers.yaml
kubectl scale statefulset/worker --replicas=$N_WORKERS -n cs449g9
# TODO: put a check until all the nodes are ready
#kubectl create -f Kubernetes/coordinator.yaml # it will crash

# useful commands
#kubectl delete po,svc --all
#docker build -f `pwd`/Docker/coordinator/Dockerfile `pwd` -t ${REPO}/${APP_NAME}_coordinator
#docker push ${REPO}/hogwild_coordinator
## Create `pod` in the cluster
#kubectl create -f ./Kubernetes/hog-pod.yaml
#kubectl describe pod/${APP_NAME} -n ${KUBER_LOGIN}
# kubectl logs $APP_NAME -p --container="coordinator"
#kubectl -n my-ns delete po,svc --all
#kubectl delete -f Kubernetes/workers.yaml --cascade=true


