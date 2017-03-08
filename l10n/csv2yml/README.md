# `csv2yml` localization message converter utility
This utility scripts converts CSV (comma-separated value) files similar to those
produced by the `yml2tsv` utility, to the YAML file structure used for localized
messages by the Zetkin front-end apps.

## Usage
```bash
$ npm install
$ npm start /path/to/file.csv /path/to/www.zetk.in/locale
```

This will convert the content of the CSV file to one or several YAML files that
are written into the _locale_ directory. Files may be overwritten by this
operation, so make sure you have the possibility to `git reset --hard` if you
need to.

The CSV file can also be a URL retrievable over HTTP/HTTPS:

```bash
$ npm start https://example.com/path/to/file.csv /path/to/www.zetk.in/locale
```

This makes it possible to retrieve directly from a public Google spreadsheet,
e.g. http://docs.google.com/spreadsheets/d/<sheet-id>/export?format=csv.
