class NurtureConfigManager:
    """养号配置管理器"""

    @staticmethod
    def get_default_config():
        """获取默认的养号配置"""
        return {'auto_open_douyin': True,
            'max_run_time': 0,
            'run_time_range': [9, 22],
            'game_live_keyword': '弹幕游戏直播',
            'like_probability': 60,
            'comment_probability': 30,
            'follow_probability': 20,
            'share_probability': 10,
            'watch_interval': [10, 15],
            'follow_interval': [5, 8],
            'like_interval': [0.1, 0.2],
            'comment_interval': [5, 8],
            'comment_texts': [
                "真不错👍",
                "支持一下",
                "厉害了",
                "学到了",
                "666"
            ],
            'swipe_interval': [2, 3],
            'page_load_interval': [3, 5]
                 }



