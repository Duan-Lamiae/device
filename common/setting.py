from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout,
    QLabel, QPushButton, QHBoxLayout, 
    QMessageBox, QGroupBox, QCheckBox, QSpinBox, QLineEdit, QDoubleSpinBox,
    QTextEdit
)
from common.config import Config


class SettingsDialog(QDialog):
    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f'设备 {self.device} 设置')
        self.setGeometry(100, 100, 1200, 800)

        layout = QVBoxLayout()

        # 创建标签页
        tab_widget = QTabWidget()

        # 养号设置
        nurture_settings = self.create_nurture_tab()
        tab_widget.addTab(nurture_settings, "养号设置")

        layout.addWidget(tab_widget)
        self.setLayout(layout)


    def create_nurture_tab(self):
        """创建养号设置标签页"""
        # 从配置管理器获取配置
        config = Config(self.device)
        nurture_config = config.read_nurture_config()

        nurture_tab = QWidget()
        layout = QVBoxLayout()

        # 基础设置组
        basic_group = QGroupBox("基础设置")
        basic_layout = QVBoxLayout()

        # 自动打开抖音
        self.auto_open_cb = QCheckBox("自动打开抖音")
        self.auto_open_cb.setChecked(nurture_config.get('auto_open_douyin', True))

        # 最大运行时间
        max_time_layout = QHBoxLayout()
        max_time_layout.addWidget(QLabel("最大运行时间(小时):"))
        self.max_time_spin = QSpinBox()
        self.max_time_spin.setSpecialValueText("不限制")
        self.max_time_spin.setValue(nurture_config.get('max_run_time', 0))
        max_time_layout.addWidget(self.max_time_spin)
        max_time_layout.addStretch()

        # 运行时间段
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(QLabel("运行时间段:"))
        self.start_time = QSpinBox()
        self.end_time = QSpinBox()
        self.start_time.setRange(0, 23)
        self.end_time.setRange(0, 23)
        time_range = nurture_config.get('run_time_range', [9, 22])
        self.start_time.setValue(time_range[0])
        self.end_time.setValue(time_range[1])
        time_range_layout.addWidget(self.start_time)
        time_range_layout.addWidget(QLabel("-"))
        time_range_layout.addWidget(self.end_time)
        time_range_layout.addStretch()

        # 游戏直播设置
        game_live_layout = QHBoxLayout()
        game_live_layout.addWidget(QLabel("游戏直播搜索关键词:"))
        self.game_live_keyword = QLineEdit()
        self.game_live_keyword.setText(nurture_config.get('game_live_keyword', '弹幕游戏直播'))
        game_live_layout.addWidget(self.game_live_keyword)

        basic_layout.addWidget(self.auto_open_cb)
        basic_layout.addLayout(max_time_layout)
        basic_layout.addLayout(time_range_layout)
        basic_layout.addLayout(game_live_layout)
        basic_group.setLayout(basic_layout)

        # 互动设置组
        interaction_group = QGroupBox("互动设置")
        interaction_layout = QVBoxLayout()

        # 各种互动概率设置
        self.like_prob = self.create_probability_setting("点赞概率:",
                                                         nurture_config.get('like_probability', 60))
        self.comment_prob = self.create_probability_setting("评论概率:",
                                                            nurture_config.get('comment_probability', 30))
        self.follow_prob = self.create_probability_setting("关注概率:",
                                                           nurture_config.get('follow_probability', 20))
        self.share_prob = self.create_probability_setting("分享概率:",
                                                          nurture_config.get('share_probability', 10))

        # 互动时间间隔设置
        self.watch_interval = self.create_time_range_setting("观看时间(秒):",
                                                             nurture_config.get('watch_interval', [10, 15]))
        self.follow_interval = self.create_time_range_setting("关注间隔(秒):",
                                                              nurture_config.get('follow_interval', [5, 8]))
        self.like_interval = self.create_time_range_setting("点赞间隔(秒):",
                                                            nurture_config.get('like_interval', [0.1, 0.2]))
        self.comment_interval = self.create_time_range_setting("评论间隔(秒):",
                                                               nurture_config.get('comment_interval', [5, 8]))

        interaction_layout.addLayout(self.like_prob)
        interaction_layout.addLayout(self.comment_prob)
        interaction_layout.addLayout(self.follow_prob)
        interaction_layout.addLayout(self.share_prob)
        interaction_layout.addLayout(self.watch_interval)
        interaction_layout.addLayout(self.follow_interval)
        interaction_layout.addLayout(self.like_interval)
        interaction_layout.addLayout(self.comment_interval)
        interaction_group.setLayout(interaction_layout)

        # 评论设置组
        comment_group = QGroupBox("评论设置")
        comment_layout = QVBoxLayout()

        # 评论内容列表
        comment_layout.addWidget(QLabel("评论内容列表(每行一条):"))
        self.comment_text = QTextEdit()
        self.comment_text.setPlainText("\n".join(
            nurture_config.get('comment_texts', ["真不错👍", "支持一下", "厉害了", "学到了", "666"])))
        comment_layout.addWidget(self.comment_text)
        comment_group.setLayout(comment_layout)

        # 滑动设置组
        swipe_group = QGroupBox("滑动设置")
        swipe_layout = QVBoxLayout()

        self.swipe_interval = self.create_time_range_setting("滑动间隔(秒):",
                                                             nurture_config.get('swipe_interval', [2, 3]))
        self.page_load_interval = self.create_time_range_setting("页面加载等待(秒):",
                                                                 nurture_config.get('page_load_interval', [3, 5]))

        swipe_layout.addLayout(self.swipe_interval)
        swipe_layout.addLayout(self.page_load_interval)
        swipe_group.setLayout(swipe_layout)

        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_nurture_settings)

        # 添加所有组件到主布局
        layout.addWidget(basic_group)
        layout.addWidget(interaction_group)
        layout.addWidget(comment_group)
        layout.addWidget(swipe_group)
        layout.addWidget(save_btn)
        layout.addStretch()

        nurture_tab.setLayout(layout)
        return nurture_tab

    def create_probability_setting(self, label, default_value):
        """创建概率设置布局"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setSuffix("%")
        spin.setValue(default_value)
        layout.addWidget(spin)
        layout.addStretch()
        return layout

    def create_time_range_setting(self, label, default_range):
        """创建时间范围设置布局"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))

        min_spin = QDoubleSpinBox()
        max_spin = QDoubleSpinBox()
        min_spin.setRange(0, 3600)
        max_spin.setRange(0, 3600)
        min_spin.setValue(default_range[0])
        max_spin.setValue(default_range[1])

        layout.addWidget(min_spin)
        layout.addWidget(QLabel("-"))
        layout.addWidget(max_spin)
        layout.addStretch()
        return layout

    def save_nurture_settings(self):
        """保存养号设置"""
        try:
            config = {
                'auto_open_douyin': self.auto_open_cb.isChecked(),
                'max_run_time': self.max_time_spin.value(),
                'run_time_range': [
                    self.start_time.value(),
                    self.end_time.value()
                ],
                'game_live_keyword': self.game_live_keyword.text(),
                'like_probability': self.like_prob.itemAt(1).widget().value(),
                'comment_probability': self.comment_prob.itemAt(1).widget().value(),
                'follow_probability': self.follow_prob.itemAt(1).widget().value(),
                'share_probability': self.share_prob.itemAt(1).widget().value(),
                'watch_interval': [
                    self.watch_interval.itemAt(1).widget().value(),
                    self.watch_interval.itemAt(3).widget().value()
                ],
                'follow_interval': [
                    self.follow_interval.itemAt(1).widget().value(),
                    self.follow_interval.itemAt(3).widget().value()
                ],
                'like_interval': [
                    self.like_interval.itemAt(1).widget().value(),
                    self.like_interval.itemAt(3).widget().value()
                ],
                'comment_interval': [
                    self.comment_interval.itemAt(1).widget().value(),
                    self.comment_interval.itemAt(3).widget().value()
                ],
                'comment_texts': self.comment_text.toPlainText().split('\n'),
                'swipe_interval': [
                    self.swipe_interval.itemAt(1).widget().value(),
                    self.swipe_interval.itemAt(3).widget().value()
                ],
                'page_load_interval': [
                    self.page_load_interval.itemAt(1).widget().value(),
                    self.page_load_interval.itemAt(3).widget().value()
                ]
            }

            # ���存配置到设���专属的nurture_config.json
            config_instance = Config(self.device)
            if config_instance.save_nurture_config(config):
                QMessageBox.information(self, "成功", "养号设置已保存！")
            else:
                QMessageBox.warning(self, "错误", "保存设置失败！")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置时出错: {str(e)}")
