#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os


# Custom constructor to read yaml with utf-8 encoding
def custom_str_constructor(loader, node):
    return loader.construct_scalar(node).encode('utf-8')


yaml.add_constructor(u'tag:yaml.org,2002:str', custom_str_constructor)


# Read yaml file into string
def get_yml(file):
    result = {}
    with open(os.path.join(os.path.dirname(__file__), file), 'rb') as ymlfile:
        values = yaml.load(ymlfile)
        for k, v in values.items():
            result[k.decode('utf-8')] = dict_byte_to_str(v)
    return result


# decode bytes dictionary
def dict_byte_to_str(v):
    result = {}
    if hasattr(v, 'items'):
        for key, value in v.items():
            if isinstance(value, bytes):
                value = value.decode('utf-8')
                value = str.replace(value, "\\n", "\n")
            result[key.decode('utf-8')] = value
    else:
        result = v.decode('utf-8')
        result = str.replace(result, "\\n", "\n")
    return result
