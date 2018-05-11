#!/usr/bin/env bash

set -eo pipefail

APP_NAME=hogwild
REPO=liabifano
KUBER_LOGIN=cs449g9

if ! [[ -z $(kubectl get pods | grep ${APP_NAME}) ]];
then
    kubectl delete pods,services -l name=${APP_NAME}
    echo "Shutting down last pod - ${APP_NAME} ..."
    sleep 1m
fi;


# build docker images
# TODO: put a check if they already exists and to another to overwrite
#cd Docker && docker-compose up
docker build -f `pwd`/Docker/node/Dockerfile `pwd` -t ${REPO}/${APP_NAME}_node
docker push ${REPO}/${APP_NAME}_node

docker build -f `pwd`/Docker/coordinator/Dockerfile `pwd` -t ${REPO}/${APP_NAME}_coordinator
docker push ${REPO}/hogwild_coordinator

# TODO: Do it dynamically and also hog-pod.yaml
# Create `pod` in the cluster
kubectl create -f ./Kubernetes/hog-pod.yaml
kubectl describe pod/${APP_NAME} -n ${KUBER_LOGIN}
# kubectl logs $APP_NAME -p --container="coordinator"

#[QUESTION: I have to push all the images to a remote repository? I can do it from local images without use minikube?]
#[QUESTION: Do we need a new image for each node? Or it is just change the port while it container is spin? How can we do it?]
#[QUESTION: The data should be located in the volume provided and all cluster will have access to it, equals in the paper. Coordinator job is not distribute data anymore]



