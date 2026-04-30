import json


config = dict()

with open('../config.json', 'r') as file:
    config:dict = json.load(file)

