#!/bin/bash

set -eu
export LANG=C.UTF-8

source ../.env

export APP_LOCALE_PATH=${APP_LOCALE_PATH:-~/opensource/www.zetk.in/locale}

TERMS=$(npm run --silent showEnglishTerms)

echo "Add Terms to project ${POEDITOR_PROJECT_ID}"

curl -X POST https://api.poeditor.com/v2/terms/add \
     -H "Content-Type: application/x-www-form-urlencoded; charset=utf-8" \
     -d api_token="${POEDITOR_API_KEY}" \
     -d id="${POEDITOR_PROJECT_ID}" \
     -d data="${TERMS}" | jq .

echo "Updating project ${POEDITOR_PROJECT_ID}"

curl -X POST https://api.poeditor.com/v2/terms/update \
     -H "Content-Type: application/x-www-form-urlencoded; charset=utf-8" \
     -d api_token="${POEDITOR_API_KEY}" \
     -d id="${POEDITOR_PROJECT_ID}" \
     -d data="${TERMS}" \
     -d fuzzy_trigger="1" | jq .

# echo "Delete terms from project ${POEDITOR_PROJECT_ID}"
#
# curl -X POST https://api.poeditor.com/v2/terms/delete \
#      -H "Content-Type: application/x-www-form-urlencoded; charset=utf-8" \
#      -d api_token="${POEDITOR_API_KEY}" \
#      -d id="${POEDITOR_PROJECT_ID}" \
#      -d data="${TERMS}" | jq .
