'use strict';

// ENV variables are read from the ../.env file
const path = require('path');
require('dotenv').config({ path: path.resolve(process.cwd(), '../.env') });
const util = require('util');

const flatten = require('flat').flatten;
const yaml = require('node-yaml');
const recurse = require('recursive-readdir');

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
            yaml.read(files[i], {
                encoding: "utf8",
                schema: yaml.schema.defaultSafe
            }, (err, data) => {
                if (err) {
                    cb(err, null);
                }
                else {
                    if (!data) {
                        console.error("File empty: " + files[i]);
                        console.error("Blank content replaced by the empty object.");
                        data = data || {};
                    }
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

function languagesFrom(messages) {
    let langs = [];
    Object.keys(messages).forEach(msg => {
        Object.keys(messages[msg].translations).forEach(lang => {
            if (langs.indexOf(lang) < 0) {
                langs.push(lang);
            }
        });
    });
    return langs;
}

loadMessages(process.env.APP_LOCALE_PATH, (err, messages) => {
    if (err) {
        console.log('Load error', err);
    }

    let langs = languagesFrom(messages);
    // Collect all terms in all languages
    let allTerms = {};
    Object.keys(messages)
        .sort()
        .forEach(msg => {
            let message = messages[msg];
            let term = message.filePath + ":" + message.yamlPath;
            langs.forEach(lang => {
                allTerms[lang] = allTerms[lang] || [];
                let content = message.translations[lang] || '';
                allTerms[lang].push({
                    term,
                    translation: {
                        content,
                        fuzzy: 0
                    }
                });
            });
        });

    // Output all terms in all languages as JSON
    process.stdout.write(JSON.stringify({allTerms}) + '\n');
});
