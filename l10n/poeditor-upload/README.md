# `zetkin-poeditor-upload` localization message converter utility

This utility script converts the tree of YAML files used in the Zetkin front-end
apps to lists of Terms for the Poeditor.com translation service.

## Pre-requisites
The following steps need to be taken once before running the script for the
first time.

### 1. Install Docker
If you haven't already, you first need to install Docker and Docker Compose.
You can download them for your system from [docker.com](https://docker.com).

### 2. Configure environment
Before running the script, you need to configure some environment variables,
preferrably using a `.env` file. Copy `.env-sample` to create an `.env` file
in the same directory:

```
cp .env-sample .env
```

Edit the `.env` file to contain the POEditor API key, project IDs and the
correct paths to where you have cloned the Zetkin app repositories. For example:

```
# This is the API key from POEditor.com, which you can find
# in the POEditor dashboard (or by contacting info@zetkin.org)
POEDITOR_API_KEY=abc123def456

# Per-app settings
CALL_ZETK_IN_PROJECT_ID=123456
CALL_ZETK_IN_LOCALE_PATH=~/src/zetkin/call.zetk.in/locale

ORGANIZE_ZETK_IN_PROJECT_ID=123457
ORGANIZE_ZETK_IN_LOCALE_PATH=~/src/zetkin/organize.zetk.in/locale

WWW_ZETK_IN_PROJECT_ID=123458
WWW_ZETK_IN_LOCALE_PATH=~/src/zetkin/www.zetk.in/locale

# Enable more verbose output
VERBOSE=1
...
```

## Running the script
Once everything is set up, you can run (and re-run) the script using Docker
Compose.

### All translations for all apps
To upload translations for all apps at once, run:
```
docker-compose up
```

The above will start one Docker container per app, mounting the input folders
as volumes, and run the script for all the apps simultaneously.

### Select apps
To upload terms/translations for just one of the apps, run:
```
docker-compose run www_zetk_in
```

Or for two named apps:
```
docker-compose run www_zetk_in call_zetk_in
```

### Select languages
To upload terms/translations for a select subset of languages only, run:
```
TARGET_LANGUAGE=sv docker-compose run www_zetk_in
```

You can specify several languages as a comma-separated list, and use variations
of the `docker-compose` command to run one or several apps, e.g:
```
TARGET_LANGUAGE=sv,en docker-compose run www_zetk_in call_zetk_in
```
