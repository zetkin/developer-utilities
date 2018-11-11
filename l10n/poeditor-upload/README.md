# `zetkin-poeditor-upload` localization message converter utility

This utility script converts the tree of YAML files used in the Zetkin front-end
apps to lists of Terms for the Poeditor.com translation service.

## Usage

Pre-requisites:

- Install [`jq`](https://stedolan.github.io/jq/download/)
- Install `curl`
- Prepare your `../.env` file with API key
- `npm install`

Now, you can use the scripts described below.

## Update Terms (base language Terms)

Find all the `en`-language Terms, to prepare the Terms for our main language.

```
POEDITOR_PROJECT_ID=12345 APP_LOCALE_PATH="~/opensource/www.zetk.in/locale" ./add-and-update-project-terms.sh
```

## Update language translations

Update all translations:

```
POEDITOR_PROJECT_ID=12345 ./update-all-languages.sh
```

Update Danish strings:

```
POEDITOR_PROJECT_ID=12345 TARGET_LANGUAGE=da ./update-language.sh
```
