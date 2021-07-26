#!/bin/bash

source ${PWD}/.env
echo "setup ports"
if [ -z "${MONGO_PORT}" ]; then
   export MONGO_PORT=27018
fi
if [ -z "${SERVER_PORT}" ]; then
   export SERVER_PORT=8225
fi
if [ -z "${CLIENT_PORT}" ]; then
   export CLIENT_PORT=8526
fi
echo "setup mongo"
if [ -z "${MONGO_INITDB_DATABASE}" ]; then
   echo "MONGO_INITDB_DATABASE env var not set and required!"
   exit 0
fi
if [ -z "${MONGO_INITDB_ROOT_USERNAME}" ]; then
   echo "MONGO_INITDB_ROOT_USERNAME env var not set and required!"
   exit 0
fi
if [ -z "${MONGO_INITDB_ROOT_PASSWORD}" ]; then
   echo "MONGO_INITDB_ROOT_PASSWORD env var not set and required!"
   exit 0
fi
if [ -z "${ADMIN_USERNAME}" ]; then
   echo "ADMIN_USERNAME env var not set and required!"
   exit 0
fi
if [ -z "${ADMIN_PASSWORD}" ]; then
   echo "ADMIN_PASSWORD env var not set and required!"
   exit 0
fi
if [ ! -e "$PWD/scripts/init_db.js" ]; then
     mkdir scripts
     ./setup_db.sh
fi
echo "setup basic user data"
if [ ! -e "$PWD/backend/ozon/base/data/user.json" ]; then
     ./setup_user.sh
fi
echo "Compose eand Run"
docker-compose -f docker-compose.yml -p service-app stop
docker-compose -f docker-compose.yml -p service-app up --force-recreate  --always-recreate-deps --detach --remove-orphans --build