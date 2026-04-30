import json
from pathlib import Path


config_path = Path(__file__).parent.parent / 'config.json'
config = dict()

with open(config_path, 'r') as file:
    config:dict = json.load(file)

