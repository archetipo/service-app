#!/bin/bash
source .env
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
if [ -z "${COOKPIT_PORT}" ]; then
   export COOKPIT_PORT=9090
fi
if [ -z "${STACK}" ]; then
   export STACK="service-app"
fi
echo "setup mongo"
if [ -z "${MONGO_DB}" ]; then
   echo "MONGO_DB env var not set and required!"
   exit 0
fi
if [ -z "${MONGO_USER}" ]; then
   echo "MONGO_USER env var not set and required!"
   exit 0
fi
if [ -z "${MONGO_PASS}" ]; then
   echo "MONGO_PASS env var not set and required!"
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
     sh setup_db.sh
fi
echo "setup basic user data"
if [ ! -e "$PWD/backend/ozon/base/data/user.json" ]; then
     sh setup_user.sh
fi
if [ ! -e "$PWD/automations/modules/.env" ]; then
  if [ -z "${API_USER_KEY}" ]; then
     echo "---------NOTICE------"
     echo "Automations .env is required"
     echo "In project .env file fill API_USER_KEY var with:"
     echo "'token' value in file backend/ozon/base/data/user.json"
     echo "KEY='token value' "
     exit 0
  fi
  touch "$PWD/automations/modules/.env"
  echo "KEY=${API_USER_KEY}" > "$PWD/automations/modules/.env"
fi
echo "Compose eand Run"
docker-compose -f docker-compose.yml -p ${STACK} stop
docker-compose -f docker-compose.yml --env-file .env -p ${STACK} up --force-recreate  --always-recreate-deps --remove-orphans --build