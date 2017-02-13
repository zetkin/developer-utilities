'use strict';

const fs = require('fs');
const mkdirp = require('mkdirp');
const objectPath = require('object-path');
const parse = require('csv-parse');
const path = require('path');
const request = require('request');
const yaml = require('node-yaml');


let loadUrl = (url, cb) => {
    request(url, (err, res, body) => {
        if (err) {
            console.log('Request error', err);
        }
        else if (res.statusCode !== 200) {
            console.log('Request status error', res.statusCode);
        }
        else {
            cb(body);
        }
    });
};

let loadFile = (path, cb) => {
    fs.readFile(path, (err, buf) => {
        if (err) {
            console.log('File read error', err);
        }
        else {
            cb(buf.toString('utf8'));
        }
    });
};

let loadData = (path, cb) => {
    let parseData = data => {
        parse(data, (err, rows) => {
            if (err) {
                console.log('Parse error', err);
                return;
            }

            cb(rows);
        });
    };

    if (path.substr(0, 4) == 'http') {
        loadUrl(path, parseData);
    }
    else {
        loadFile(path, parseData);
    }
};

if (process.argv.length < 4) {
    console.log('Usage: npm start /path/to/file.csv /path/to/app/locale');
    console.log('');
    process.exit(0);
}

loadData(process.argv[2], rows => {
    if (rows.length <= 1) {
        console.log('File is empty');
        return;
    }

    let header = rows[0];
    let directories = {};

    rows.slice(1).forEach(row => {
        let filePath = row[0];
        let yamlPath = row[1];

        if (!directories.hasOwnProperty(filePath)) {
            directories[filePath] = {
                path: filePath.replace('.', '/'),
                translations: {},
            };
        }

        row.slice(2).forEach((val, index) => {
            let lang = header[2 + index];

            if (val.length) {
                if (!directories[filePath].translations.hasOwnProperty(lang)) {
                    directories[filePath].translations[lang] = {};
                }

                let obj = directories[filePath].translations[lang];
                objectPath.set(obj, yamlPath, val);
            }
        });
    });

    let keys = Object.keys(directories);
    let keyIdx = 0;
    let numFilesWritten = 0;

    let createNextDir = () => {
        if (keyIdx < keys.length) {
            let key = keys[keyIdx];
            let dir = directories[key];
            let dirPath = path.join(process.argv[3], dir.path);

            let langs = Object.keys(dir.translations);
            let langIdx = 0;

            let writeNextLang = cb => {
                if (langIdx < langs.length) {
                    let lang = langs[langIdx];
                    let langPath = path.join(dirPath, lang + '.yaml');
                    let options = {
                        indent: 4,
                    };

                    yaml.write(langPath, dir.translations[lang], options, err => {
                        if (err) {
                            console.log('Error writing YAML file', err);
                        }

                        langIdx++;
                        numFilesWritten++;
                        writeNextLang(cb);
                    });
                }
                else {
                    cb();
                }
            };

            mkdirp(dirPath, err => {
                if (err) {
                    console.log('Error creating dir:', err);
                    return;
                }

                writeNextLang(() => {
                    keyIdx++;
                    createNextDir();
                });
            });
        }
        else {
            console.log('Done! Files written: ' + numFilesWritten);
        }
    };

    createNextDir();
});
