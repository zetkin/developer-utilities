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
        lang_list_data = get_poeditor_langs()
        langs = parse_poeditor_lang_list(lang_list_data)
    return langs


def get_poeditor_langs():
    get_langs_url = 'https://api.poeditor.com/v2/languages/list'
    post_dict = {'api_token': os.environ['POEDITOR_API_KEY'],
            'id': os.environ['POEDITOR_PROJECT_ID']}

    lang_list_data = poeditor_http_request(get_langs_url, post_dict)
    return lang_list_data

def parse_poeditor_lang_list(lang_list_data):
    lang_list = [lang['code'] for lang in lang_list_data['result']['languages']]
    return lang_list

def get_lang_data(lang):
    lang_data_url = 'https://api.poeditor.com/v2/terms/list'
    post_dict = {'api_token': os.environ['POEDITOR_API_KEY'],
            'id': os.environ['POEDITOR_PROJECT_ID'],
            'language': lang}

    lang_data = poeditor_http_request(lang_data_url, post_dict)
    return lang_data

def parse_lang_data(lang_data):
    term_dict = {}
    locale_dir = os.environ['APP_LOCALE_DIR']
    for term_data in lang_data['result']['terms']:
        folders = term_data['term'].split(':')[0].split('.')
        path = os.path.join(locale_dir, *folders,'')
        properties = term_data['term'].split(':')[1].split('.')
        translation_content = term_data['translation']['content']
        c_dict = term_dict.setdefault(path,{})
        for prop in properties[:-1]:
            c_dict = c_dict.setdefault(prop,{})
        c_dict[properties[-1]] = translation_content
    return term_dict

def get_all_terms_all_langs(langs = ['en']):
    langs_data = {}
    langs_terms = {}
    for lang in langs:
        langs_data[lang] = get_lang_data(lang)
        langs_terms[lang] = parse_lang_data(langs_data[lang])
    return langs_terms

def str_representer(dumper, data):
    if len(data.splitlines()) == 1:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style ='|')

def dump_all_terms_all_langs(langs_terms, langs=['en']):
    yaml.add_representer(str, str_representer)
    for lang in langs:
        term_dict = langs_terms[lang]
        for directory in term_dict.keys():
            dir_path = os.path.dirname(directory)
            os.makedirs(dir_path, exist_ok=True)
            yaml_file = os.path.join(dir_path, lang+'.yaml')
            with open(yaml_file, 'w') as f:
                yaml.dump(term_dict[directory], f,
                        default_flow_style = False,
                        indent = 4,
                        allow_unicode = True)

def main():
    langs = get_langs()
    langs_terms = get_all_terms_all_langs(langs)
    dump_all_terms_all_langs(langs_terms, langs)
    return langs_terms

if __name__=='__main__':
    main()

