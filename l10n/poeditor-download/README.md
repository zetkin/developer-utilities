# `zetkin-poeditor-download` localization message converter utility

This utility script updates the YAML files used in the Zetkin front-end apps with the translations from the Poeditor.com translations service.

## Usage

Pre-requisites:

- Install PyYAML
- Prepare your ../.env file with API key

To update all language files in `$APP_LOCALE_PATH`, run the script as specified below:

```
env POEDITOR_PROJECT_ID=12345 APP_LOCALE_PATH="~/dev/www.zetkin.in/locale" `cat ../.env` ./update-all-languages.py
```

Update English and Swedish translations:

```
env POEDITOR_PROJECT_ID=12345 APP_LOCALE_PATH="~/dev/www.zetkin.in/locale" `cat ../.env` TARGET_LANGUAGE=en,sv ./update-all-languages.py
```
