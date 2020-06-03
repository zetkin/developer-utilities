const axios = require('axios');
const MessageFormat = require('messageformat');
const qs = require('querystring');
const recurse = require('recursive-readdir');
const util = require('util');
const yaml = require('node-yaml');


const API_TOKEN = process.env.POEDITOR_API_TOKEN;
const PROJECT_ID = process.env.POEDITOR_PROJECT_ID;
const LOCALE_PATH = '/var/app/locale';

const poeRequest = (path, data) => axios
    .post(`https://api.poeditor.com/v2${path}`, qs.stringify({
        api_token: API_TOKEN,
        ...data,
    }))
    .then(res => res.data);


const cmdLoadTranslations = (lang) => {
    let localTerms;
    let oldLangTerms;

    const stats = {
        ignored: [],
        invalid: [],
        unchanged: [],
        updated: [],
    };

    loadMessages(LOCALE_PATH, '')
        .then(messages => {
            localTerms = messages;
            oldLangTerms = localTerms[lang] || {};
            localTerms[lang] = {};
            return poeRequest('/terms/list', { id: PROJECT_ID, language: lang });
        })
        .then(data => {
            const mf = new MessageFormat(lang);
            const argExp = /\{\s*[a-zA-Z0-9]*\s*\}/g;
            const parseArgs = s => (s.match(argExp) || []).map(a => a.slice(1, -1).trim());

            data.result.terms.forEach(term => {
                if (localTerms.en.hasOwnProperty(term.term)) {
                    const translation = term.translation.content
                    if (oldLangTerms[term.term] != translation) {
                        stats.updated.push(term.term);
                    }
                    else {
                        stats.unchanged.push(term.term);
                    }

                    // Check if ICU message format, and validate syntax
                    if (translation.indexOf('{') >= 0) {
                        // Validate basic syntax
                        try {
                            const msg = mf.compile(translation);
                        }
                        catch (err) {
                            stats.invalid.push(term.term);
                        }

                        // Get list of args (placeholders) and compare
                        const enArgs = parseArgs(localTerms.en[term.term]);
                        const transArgs = parseArgs(translation);
                        for (const arg of transArgs) {
                            if (!enArgs.includes(arg)) {
                                stats.invalid.push(term.term);
                                break;
                            }
                        }
                    }

                    localTerms[lang][term.term] = translation;
                }
                else {
                    stats.ignored.push(term.term);
                }
            });

            if (stats.invalid.length) {
                console.warn('Found invalid terms');
                stats.invalid.forEach(term => console.log('- ', term));
                throw new Error('Invalid MessageFormat syntax');
            }

            let dataByFile = {};
            Object.keys(localTerms.en).forEach(term => {
                // Only write those which have actually been translated
                if (localTerms[lang][term]) {
                    const fileDotPath = term.split(':')[0];
                    if (!dataByFile[fileDotPath]) {
                        dataByFile[fileDotPath] = {};
                    }

                    const yamlDotPath = term.split(':')[1];
                    const yamlPathElems = yamlDotPath.split('.');
                    let obj = dataByFile[fileDotPath];
                    yamlPathElems.forEach((elem, idx) => {
                        if (idx == yamlPathElems.length-1) {
                            // Last element in path is the actual value
                            obj[elem] = localTerms[lang][term];
                        }
                        else {
                            if (!obj.hasOwnProperty(elem)) {
                                obj[elem] = {};
                            }

                            obj = obj[elem];
                        }
                    });
                }
            });

            const yamlWrite = util.promisify(yaml.write);

            const promises = Object.keys(dataByFile)
                .filter(fileDotPath => stats.updated.find(path => path.startsWith(fileDotPath)))
                .map(fileDotPath => {
                    const path = LOCALE_PATH + '/' + fileDotPath.split('.').join('/');
                    const yamlPath = path + '/' + lang + '.yaml';
                    return yamlWrite(yamlPath, dataByFile[fileDotPath], { indent: 4 });
                });

            return Promise.all(promises);
        })
        .then(() => {
            console.log('Done!');
            console.log('Ignored: ' + stats.ignored.length);
            console.log('Unchanged: ' + stats.unchanged.length);
            console.log('Updated: ' + stats.updated.length);
        })
        .catch(err => {
            console.log('Bailed due to an error');
            console.error(err);
        });
}

if (process.argv.length > 2) {
    const cmd = process.argv[2];

    if (cmd == 'loadtranslations') {
        cmdLoadTranslations(process.argv[3]);
    }
}
else {
    console.log('Give command');
}


function loadMessages(path, lang='') {
    let messages = {};

    const ignore = (file, stats) =>
        !stats.isDirectory() && !file.endsWith(`${lang}.yaml`);

    const traverse = (basePath, obj, output) => {
        Object.keys(obj).forEach(key => {
            const val = obj[key];
            if (typeof val == 'string') {
                output[basePath + key] = val;
            }
            else if (val && typeof val == 'object') {
                traverse(basePath + key + '.', val, output);
            }
        });
    };

    return new Promise((resolve, reject) => {
        recurse(path, [ ignore ], (err, files) => {
            if (err) {
                return console.log('readdir() error', err);
            }

            let numCompleted = 0;
            for (let i = 0; i < files.length; i++) {
                yaml.read(files[i], null, (err, data) => {
                    if (err) {
                        reject(err);
                    }
                    else if (data) {
                        let relPath = files[i].replace(path, '')

                        let pathElems = relPath
                            .substring(1, relPath.length - 5)
                            .split('/');

                        const fileDotPath = pathElems.slice(0, -1).join('.');

                        // Locale dot path is language first, then the path of the
                        // file (which denotes the "scope").
                        const lang = pathElems[pathElems.length - 1];
                        if (!messages[lang]) {
                            messages[lang] = {};
                        }

                        traverse(fileDotPath + ':', data, messages[lang]);
                    }

                    numCompleted++;
                    if (numCompleted === files.length) {
                        resolve(messages);
                    }
                });
            }
        });
    });
}
