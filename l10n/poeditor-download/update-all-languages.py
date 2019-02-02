import os
import sys
import urllib.parse
import urllib.request
import yaml
import json
import pyseeyou
from parsimonious.exceptions import IncompleteParseError
import distutils.util


def poeditor_http_request(url, post_dict):
    data = urllib.parse.urlencode(post_dict)
    data = data.encode('ascii')

    with urllib.request.urlopen(url, data) as f:
        response = f.read().decode('utf-8')

    clean_response = json.loads(response)

    try:
        assert clean_response['response']['code'] == '200'
    except AssertionError:
        print('Bad response from poeditor.com, code {}'.format(clean_response['response']['code']))
        raise

    return clean_response


def get_langs():
    lang_spec = os.environ.get('TARGET_LANGUAGE')
    if len(lang_spec) > 0:
        return lang_spec.split(',')
    else:
        lang_list_data = get_poeditor_langs()
        return parse_poeditor_lang_list(lang_list_data)


def get_poeditor_langs():
    get_langs_url = 'https://api.poeditor.com/v2/languages/list'
    post_dict = {
        'api_token': os.environ['POEDITOR_API_KEY'],
        'id': os.environ['POEDITOR_PROJECT_ID']
    }

    lang_list_data = poeditor_http_request(get_langs_url, post_dict)
    return lang_list_data


def parse_poeditor_lang_list(lang_list_data):
    lang_list = [lang['code'] for lang in lang_list_data['result']['languages']]
    return lang_list


def get_lang_data(lang):
    lang_data_url = 'https://api.poeditor.com/v2/terms/list'
    post_dict = {
        'api_token': os.environ.get('POEDITOR_API_KEY'),
        'id': os.environ.get('POEDITOR_PROJECT_ID'),
        'language': lang
    }

    lang_data = poeditor_http_request(lang_data_url, post_dict)
    return lang_data


def parse_lang_data(lang_data):
    term_dict = {}
    locale_dir = os.environ['APP_LOCALE_DIR']
    for term_data in lang_data['result']['terms']:
        folders = term_data['term'].split(':')[0].split('.')
        path = os.path.join(locale_dir, *folders, '')
        properties = term_data['term'].split(':')[1].split('.')
        translation_content = term_data['translation']['content']
        c_dict = term_dict.setdefault(path, {})
        for prop in properties[:-1]:
            c_dict = c_dict.setdefault(prop, {})
        c_dict[properties[-1]] = translation_content
    return term_dict


def get_all_terms_all_langs(langs=['en']):
    langs_data = {}
    langs_terms = {}
    for lang in langs:
        langs_data[lang] = get_lang_data(lang)
        langs_terms[lang] = parse_lang_data(langs_data[lang])
    return langs_terms, langs_data


def str_representer(dumper, data):
    if len(data.splitlines()) == 1:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')


def dump_all_terms_all_langs(langs_terms, langs=['en']):
    yaml.add_representer(str, str_representer)
    for lang in langs:
        term_dict = langs_terms[lang]
        for directory in term_dict.keys():
            dir_path = os.path.dirname(directory)
            os.makedirs(dir_path, exist_ok=True)
            yaml_file = os.path.join(dir_path, lang + '.yaml')
            with open(yaml_file, 'w') as f:
                yaml.dump(term_dict[directory], f,
                        default_flow_style=False,
                        indent=4,
                        allow_unicode=True)


def check_ICU(langs_data, langs=['en']):
    ICU_terms = []
    bad_ICU = []
    for term_entry in langs_data['en']['result']['terms']:
        term = term_entry['term']
        translation = term_entry['translation']['content']
        if '{' in translation or '}' in translation:
            try:
                pyseeyou.ICUMessageFormat.parse(translation)
                ICU_terms.append(term)
            except IncompleteParseError:
                print('en: Incorrect ICU in term {}'.format(term))
                bad_ICU.append(term)
    ICU_terms = set(ICU_terms)
    for lang in langs:
        if lang == 'en':
            continue
        for term_entry in langs_data[lang]['result']['terms']:
            term = term_entry['term']
            translation = term_entry['translation']['content']
            if '{' in translation or '}' in translation or term in ICU_terms:
                if term not in ICU_terms:
                    print('{}: Term {} ICU formatted, but English translation is not'.format(lang, term))
                    bad_ICU.append(term)
                try:
                    pyseeyou.ICUMessageFormat.parse(translation)
                except IncompleteParseError:
                    bad_ICU.append(term)
                    print('{}: Incorrect ICU in term {}'.format(lang, term))
    if len(bad_ICU) > 0:
        message = 'Bad or mismatching ICUs detected. Continuing will overwrite current translations with possibly bad ICUs. Continue? [Y/n] '
        check_continue(message)


def check_continue(message):
    while True:
        input_response = input(message)
        try:
            if len(input_response) == 0 or distutils.util.strtobool(input_response):
                return
            else:
                sys.exit(0)
        except ValueError:
            print('Please enter "yes" or "no"')


def get_verbosity():
    verbose_env = os.environ.get('VERBOSE', '0')
    if len(verbose_env) > 0:
        return bool(int(verbose_env))
    return False


def summarize_result(langs_terms, langs):
    if get_verbosity():
        for lang in langs:
            num_terms = count_terms(langs_terms[lang])
            print('{}: {} translated terms fetched'.format(lang, num_terms))


def count_terms(term_dict):
    count = 0
    for key, item in term_dict.items():
        if type(item) == dict:
            count += count_terms(item)
        elif item != '':
            count += 1
    return count


def main():
    langs = get_langs()
    langs_terms, langs_data = get_all_terms_all_langs(langs)
    check_ICU(langs_data, langs)
    dump_all_terms_all_langs(langs_terms, langs)
    summarize_result(langs_terms, langs)


if __name__ == '__main__':
    main()
