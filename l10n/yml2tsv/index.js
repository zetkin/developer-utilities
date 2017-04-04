'use strict';

const flatten = require('flat').flatten;
const yaml = require('node-yaml');
const recurse = require('recursive-readdir');
const stringify = require('csv-stringify');


let loadMessages = (path, cb) => {
    let messages = {};
    let numCompleted = 0;
    let ignore = (file, stats) =>
        !stats.isDirectory() && !file.endsWith('.yaml');

    recurse(path, [ ignore ], (err, files) => {
        if (err) {
            console.log('readdir() error', err);
            return;
        }

        for (let i = 0; i < files.length; i++) {
            yaml.read(files[i], null, (err, data) => {
                if (err) {
                    cb(err, null);
                }
                else {
                    let relPath = files[i].replace(path, '')

                    let pathElems = relPath
                        .substring(0, relPath.length - 5)
                        .split('/');

                    let filePath = pathElems
                        .slice(0, pathElems.length -1)
                        .join('.');

                    let fileMessages = flatten(data);
                    let flatData = flatten(data);
                    Object.keys(flatData).forEach(msg => {
                        let lang = pathElems[pathElems.length-1];
                        let fullPath = filePath + '.' + msg;

                        if (!messages.hasOwnProperty(fullPath)) {
                            messages[fullPath] = {
                                filePath: filePath,
                                yamlPath: msg,
                                translations: {},
                            };
                        }

                        messages[fullPath].translations[lang] = flatData[msg];
                    });
                }

                numCompleted++;
                if (numCompleted === files.length) {
                    cb(null, messages);
                }
            });
        }
    });
};

loadMessages(process.argv[2], (err, messages) => {
    if (err) {
        console.log('Load error', err);
    }

    let langs = [];
    Object.keys(messages).forEach(msg => {
        Object.keys(messages[msg].translations).forEach(lang => {
            if (langs.indexOf(lang) < 0) {
                langs.push(lang);
            }
        });
    });

    let rows = [];

    // First row is header
    rows.push([ 'File path', 'YAML path' ].concat(langs));

    Object.keys(messages)
        .sort()
        .forEach(msg => {
            let message = messages[msg];
            let translations = langs.map(lang => message.translations[lang] || '');
            let row = [ message.filePath, message.yamlPath ].concat(translations);

            rows.push(row);
        });

    stringify(rows, { delimiter: '\t', quoted: true, }, (err, csv) => {
        console.log(csv);
    });
});
