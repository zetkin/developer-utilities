import os
import urllib.parse
import urllib.request
import yaml
import json

def poeditor_http_request(url, post_dict):
    data = urllib.parse.urlencode(post_dict)
    data = data.encode('ascii')
    
    with urllib.request.urlopen(url,data) as f:
        response = f.read().decode('utf-8')

    clean_response = json.loads(response)

    try:
        assert clean_response['response']['code'] == '200'
    except AssertionError as err:
        print('Bad response from poeditor.com, code {}'.format(clean_response['response']['code']))
        raise

    return clean_response

def get_langs():
    try:
        langs = os.environ['TARGET_LANGUAGE'].split(',')
    except KeyError:
        langs = get_local_langs()
    return langs

def get_local_langs():
    locale_dir = os.environ['APP_LOCALE_DIR']
    file_names = set()
    for dirname, subdirs, files in os.walk(locale_dir):
        file_names |= set(files)
    langs = [file_name[:-5] for file_name in file_names if file_name[-5:] == '.yaml']
    return langs

def get_poeditor_lang_data(lang):
    url = 'https://api.poeditor.com/v2/terms/list'
    post_dict = {'api_token': os.environ['POEDITOR_API_KEY'],
            'id': os.environ['POEDITOR_PROJECT_ID'],
            'language': lang}

    response = poeditor_http_request(url, post_dict)
    return response

def parse_poeditor_lang_data(lang_data):
    term_dict = {}
    for term_data in lang_data['result']['terms']:
        term = term_data['term']
        term_dict[term] = term_data['translation']['content']
    return term_dict

def get_all_poeditor_terms_all_langs(langs = ['en']):
    langs_data = {}
    langs_terms = {}
    for lang in langs:
        langs_data[lang] = get_poeditor_lang_data(lang)
        langs_terms[lang] = parse_poeditor_lang_data(langs_data[lang])
    return langs_terms

def poeditor_add_terms(data):
    url = 'https://api.poeditor.com/v2/terms/add'
    post_dict = {'api_token': os.environ['POEDITOR_API_KEY'],
            'id': os.environ['POEDITOR_PROJECT_ID'],
            'data': data,
            'fuzzy': '1'}

    response = poeditor_http_request(url, post_dict)
    return response

def poeditor_update_translations(lang, data):
    url = 'https://api.poeditor.com/v2/languages/update'
    post_dict = {'api_token': os.environ['POEDITOR_API_KEY'],
            'id': os.environ['POEDITOR_PROJECT_ID'],
            'language': lang,
            'data': data,
            'fuzzy':'1'}

    response = poeditor_http_request(url, post_dict)
    return response

def flatten_yaml_dict(yaml_dict, parent_key = []):
    flat_dict = {}
    if yaml_dict is None:
        return flat_dict
    for key, val in yaml_dict.items():
        full_key_list = parent_key + [key]
        if type(val) == dict:
            flat_dict = {**flat_dict, **flatten_yaml_dict(val, full_key_list)}
        else:
            full_key = '.'.join(full_key_list)
            flat_dict[full_key] = val
    return flat_dict

def get_local_lang_data(langs = ['en']):
    locale_dir = os.environ['APP_LOCALE_DIR']
    term_dict = {lang:{} for lang in langs}
    for dirname, subdirs, files in os.walk(locale_dir):
        if len(files) == 0:
            continue
        for lang in langs:
            try:
                with open(os.path.join(dirname, lang + '.yaml'), 'r') as f:
                    lang_data = yaml.safe_load(f)
            except FileNotFoundError:
                continue
            else:
                dir_part_key = os.path.relpath(dirname, locale_dir).replace('/','.')
                flat_lang_data = flatten_yaml_dict(lang_data)
                for yaml_part_key, val in flat_lang_data.items():
                    full_key = dir_part_key + ':' + yaml_part_key
                    term_dict[lang][full_key] = val
    return term_dict

def identify_terms_to_update(local_langs_data, poeditor_langs_data, langs=['en']):
    local_terms = set(local_langs_data['en'].keys())
    poeditor_terms = set(poeditor_langs_data['en'].keys())

    local_langs_data_with_translation = {lang: {term:local_langs_data[lang][term] for term in local_langs_data[lang].keys() if local_langs_data[lang][term] != ''} for lang in langs}
    local_terms_with_translation = {lang: local_terms & set(local_langs_data_with_translation[lang].keys()) for lang in langs}
    
    new_terms = local_terms - poeditor_terms
    new_terms_with_translation = {lang: new_terms & set(local_langs_data_with_translation[lang].keys()) for lang in langs}

    poeditor_orphan_terms = poeditor_terms - local_terms
    intersecting_terms = local_terms & poeditor_terms

    poeditor_terms_lacking_translation = {lang: set([term for term in intersecting_terms if poeditor_langs_data[lang][term] == '']) for lang in langs}
    locally_translated_terms = {lang: local_terms_with_translation[lang] & poeditor_terms_lacking_translation[lang] for lang in langs}

    terms_to_update = {lang: new_terms_with_translation[lang] | locally_translated_terms[lang] for lang in langs}
    
    return new_terms, terms_to_update

def get_local_translations(local_langs_data, terms_to_update, langs = ['en']):
    translated_terms = {lang: {term: local_langs_data[lang][term] for term in terms_to_update[lang]} for lang in langs}
    return translated_terms

def build_term_add_json(new_terms):
    term_dict_list = [{'term': term} for term in new_terms]
    data_string = json.dumps(term_dict_list)
    return data_string

def build_update_translation_jsons(translated_terms, langs = ['en']):
    update_translation_dicts = {lang: [{'term':term, 'translation': {'content':translation, 'fuzzy':'1'}} for term, translation in translated_terms[lang].items()] for lang in langs}
    update_translation_jsons = {lang: json.dumps(update_translation_dicts[lang]) for lang in langs}
    return update_translation_jsons

def main():
    langs = get_langs()
    poeditor_langs_data = get_all_poeditor_terms_all_langs(langs)
    local_langs_data = get_local_lang_data(langs)
    new_terms, terms_to_update = identify_terms_to_update(local_langs_data, poeditor_langs_data, langs)
    translated_terms = get_local_translations(local_langs_data, terms_to_update, langs)

    if len(new_terms) > 0:
        term_add_json = build_term_add_json(new_terms)
        poeditor_add_terms(term_add_json)

    langs_to_update = [lang for lang in langs if len(translated_terms[lang]) > 0]
    update_translation_jsons = build_update_translation_jsons(translated_terms, langs_to_update)
    for lang in langs_to_update:
        poeditor_update_translations(lang, update_translation_jsons[lang])

if __name__=='__main__':
    main()

