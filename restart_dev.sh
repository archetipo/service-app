#!/bin/bash
source ${PWD}/.env
if [ -z "${MONGO_PORT}" ]; then
   export MONGO_PORT=27018
fi
if [ -z "${SERVER_PORT}" ]; then
   export SERVER_PORT=8225
fi
if [ -z "${CLIENT_PORT}" ]; then
   export CLIENT_PORT=8526
fi
if [ -z "${STACK}" ]; then
   export STACK="service-app"
fi
docker-compose -f docker-compose.yml -p ${STACK} stop
docker-compose -f docker-compose.yml -p ${STACK} start