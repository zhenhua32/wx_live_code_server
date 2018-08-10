import os
import json


dir_path = os.path.dirname(__file__)
config_path = os.path.join(dir_path, '../livecode/config.json')
config_path = os.path.normpath(config_path)
config = json.load(open(config_path, 'r', encoding='utf-8'), encoding='utf-8')
