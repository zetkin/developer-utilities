#!/bin/bash

set -eu
export LANG=C.UTF-8

source ../.env

export APP_LOCALE_PATH=${APP_LOCALE_PATH:-~/opensource/www.zetk.in/locale}

for TARGET_LANGUAGE in $(npm run --silent showLanguages)
do
  TERMS=$(npm run --silent start | jq "[.allTerms.${TARGET_LANGUAGE}[]]")

  echo "Add Translations to language ${TARGET_LANGUAGE} in project ${POEDITOR_PROJECT_ID}"

  curl -X POST https://api.poeditor.com/v2/languages/update \
       -H "Content-Type: application/x-www-form-urlencoded; charset=utf-8" \
       -d api_token="${POEDITOR_API_KEY}" \
       -d id="${POEDITOR_PROJECT_ID}" \
       -d data="${TERMS}" \
       -d language="${TARGET_LANGUAGE}" \
       -d fuzzy_trigger="1" | jq .
done

