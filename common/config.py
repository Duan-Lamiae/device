# -*- coding: utf-8 -*-
"""
调取配置文件和屏幕分辨率的代码
"""
import os
import sys
import json
import re
from pathlib import Path

from common.nurture_config_manager import NurtureConfigManager

from common.auto_adb import AutoAdb

adb = AutoAdb()

class Config:
    def __init__(self, serialno):
        self.serialno = serialno
        self.config_dir = Path(f"config/{serialno}")
        self.config_file = self.config_dir / "config.json"
        self.nurture_config_file = self.config_dir / "nurture_config.json"
        self.ensure_config_dir()


    def ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)


    def save_nurture_config(self, config_data):
        """保存配置到JSON文件"""
        try:
            with open(self.nurture_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {str(e)}")
            return False

    def read_nurture_config(self):
        """读取配置文件"""
        try:
            if self.nurture_config_file.exists():
                with open(self.nurture_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # 如果文件不存在，返回默认配置
            default_config = NurtureConfigManager.get_default_config()
            self.save_nurture_config(default_config)
            return default_config
        except Exception as e:
            print(f"读取配置失败: {str(e)}")
            # 发生错误时也返回默认配置
            return NurtureConfigManager.get_default_config()

 
    # 读取配置文件
    def read_config(self):
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)



    def open_accordant_config(self):
        """
        调用配置文件
        """
        serialno=self.serialno
        config_file = "{path}/config/{serialno}/config.json".format(
            path=sys.path[0],
            serialno=serialno
        )

        # 优先获取执行文件目录的配置文件
        here = sys.path[0]
        for file in os.listdir(here):
            if re.match(r'(.+)\.json', file):
                file_name = os.path.join(here, file)
                with open(file_name, 'r') as f:
                    print("Load config file from {}".format(file_name))
                    return json.load(f)

        # 根据手机序列号查找配置文件
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                print("正在从 {} 加载配置文件".format(config_file))
                return json.load(f)
        else:
            with open('{}/config/default.json'.format(sys.path[0]), 'r') as f:
                print("Load default config")
                return json.load(f)


