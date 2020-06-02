# Zetkin developer utils

docker build -t zdu .
docker run --rm -v $PWD/src:/var/app/src --env-file .env -v $PWD/../../product/www.zetk.in/locale:/var/app/locale -ti zdu loadtranslations sv

## Localization

### Upload terms

* Read local English message IDs
* Retrieve list of POEditor project terms
* Create any terms which do not already exist in POEditor, log to stdout
* Compare translations, warn about any mismatches
* Find online terms which have been removed locally
  * Log missing terms to stdout
  * Delete after asking user

### Download translations

* Read local English messages and IDs
* Retrieve all translations from POEditor
* Cull translations to only include terms existing locally
* For each translated term:
    * Check English syntax, and verify translated syntax, warn if invalid
    * Write to YAML
