import json
import os


class LiveConfigManager:
    """直播配置管理类"""

    DEFAULT_CONFIG = {
        "is_auto_open_douyin": True,        # 是否自动打开抖音
        "max_run_time": 0,                  # 最大运行时间 0不限制
        # 观看视频配置
        "watch_video": {
            "watch": True,
            "watch_interval": [10, 30],
        },
        # 观看垂类直播配置
        "vertical_live": {
            "watch": True,                  # 是否观看垂类直播
            "vertical_type": "弹幕",         # 垂类类型
            "watch_count": 0,               # 观看次数 0不限制
            "watch_time": 0.1,              # 观看时长小时
        },
        # 观看目标直播间配置
        "target_room": {
            "watch": True,                  # 是否观看直播
            "room_name": "@Sawubona",       # 目标直播间名称
            "watch_time": 1,                # 观看时长小时
        }
    }

    def __init__(self, config_path="config/live_config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # 如果配置文件不存在，返回默认配置
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, config):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            self.config = config
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get_config(self):
        """获取当前配置"""
        return self.config

    def get_watch_video_config(self):
        """获取视频观看配置"""
        return self.config.get("watch_video", self.DEFAULT_CONFIG["watch_video"])

    def get_vertical_live_config(self):
        """获取垂类直播配置"""
        return self.config.get("vertical_live", self.DEFAULT_CONFIG["vertical_live"])

    def get_target_room_config(self):
        """获取目标直播间配置"""
        return self.config.get("target_room", self.DEFAULT_CONFIG["target_room"])
