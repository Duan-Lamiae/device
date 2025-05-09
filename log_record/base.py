# !/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import configparser

configs = configparser.ConfigParser()
configs.optionxform = str
config_path = os.path.join(os.path.dirname(__file__), 'database_dev.ini')
configs.read(config_path)
