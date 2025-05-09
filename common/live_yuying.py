import uiautomator2 as u2
import subprocess
import time
import random
from .live_config_manager import LiveConfigManager
from datetime import datetime, timedelta


class LiveYuying:
    def __init__(self, serial):
        self.serial = serial
        self.device = u2.connect_usb(serial)
        self.size = self.device.window_size()
        self.center = (self.size[0] / 2, self.size[1] / 2)
        self.live_config = LiveConfigManager()
        self.is_room = False
        self.stop_running = False  # 添加停止标志
        # 初始化开始时间
        self.start_time = datetime.now()
        # 上次观看视频的时间
        self.last_video_time = None
        # 添加停止标志
        self.stop_running = False

    def stop(self):
        """停止运行"""
        self.stop_running = True
        
    def check_max_run_time(self):
        """检查是否超过最大运行时间"""
        max_run_time = self.live_config.get_config().get('max_run_time', 0)
        if max_run_time > 0:
            run_time = datetime.now() - self.start_time
            if run_time > timedelta(hours=max_run_time):
                print(f"已达到最大运行时间 {max_run_time} 小时")
                return False
        return True

    def should_watch_video(self):
        """检查是否应该观看视频"""
        video_config = self.live_config.get_config()['watch_video']
        if not video_config['watch']:
            return False

        if self.last_video_time is None:
            self.last_video_time = datetime.now()
            return True

        interval = random.randint(
            video_config['watch_interval'][0],
            video_config['watch_interval'][1]
        )
        time_since_last = (
            datetime.now() - self.last_video_time).total_seconds()
        return time_since_last >= interval

    def watch_vertical_live(self, room_name, room_intro):
        """观看垂类直播"""
        vertical_config = self.live_config.get_config()['vertical_live']
        if not vertical_config['watch']:
            return False

        vertical_type = vertical_config['vertical_type']
        if vertical_type in room_intro or vertical_type in room_name:
            print(f'当前直播间: {room_name}, 是{vertical_type}直播间！')
            watch_time = vertical_config['watch_time']
            # 观看指定时长
            if watch_time > 0:
                watch_seconds = int(watch_time * 3600)  # 转换为秒
                print(f"将观看 {watch_time} 小时")
                time.sleep(watch_seconds)
            return True
        return False

    def watch_target_room(self, room_name):
        """观看目标直播间"""
        target_config = self.live_config.get_config()['target_room']
        if not target_config['watch']:
            return False

        if room_name == target_config['room_name']:
            print(f"进入目标直播间: {room_name}")
            watch_time = target_config['watch_time']
            if watch_time > 0:
                watch_seconds = int(watch_time * 3600)  # 转换为秒
                print(f"将观看 {watch_time} 小时")
                time.sleep(watch_seconds)
            return True
        return False

    def yunying_live(self):
        package = 'com.ss.android.ugc.aweme'
        if package not in self.device.app_list():
            print(f"{package} 未安装")
            return False

        config = self.live_config.get_config()
        if not config.get('is_auto_open_douyin', True):
            print("自动打开抖音功能已禁用")
            return False

        if self.app_running(package):
            # 修改主循环条件，加入停止检查
            while self.check_max_run_time() and not self.stop_running:
                if self.is_live_room():
                    print(f"{self.serial} 在{self.is_live_room()}直播间")
                    self.like()
                    time.sleep(10)
                else:
                    if self.is_live_room_page():
                        room_name, room_intro = self.is_live_room_page_exist()
                        if room_name:
                            # 优先检查是否是目标直播间
                            if self.watch_target_room(room_name):
                                continue
                            # 然后检查是否是垂类直播间
                            if self.watch_vertical_live(room_name, room_intro):
                                continue
                            # 都不是，检查是否应该观看视频
                            if self.should_watch_video():
                                self.last_video_time = datetime.now()
                                print("观看普通视频")
                                continue

                            print(f'当前直播间: {room_name}, 不是目标直播间')
                            self.not_like_room()

                    self.next_page()

                # 检查是否需要停止
                if self.stop_running:
                    print(f"{self.serial} 直播运营停止")
                    break

                random_sleep = random.uniform(2, 10)
                print(f'随机休眠: {random_sleep}')
                time.sleep(random_sleep)
        else:
            print(f"{self.serial} 抖音打开失败")

    # 是否在直播间，如果是返回直播间名称
    def is_live_room(self):
        # 检查元素是否存在
        user_name_element = self.device(
            resourceId="com.ss.android.ugc.aweme:id/user_name")
        if user_name_element.exists:
            # 获取元素的文本
            self.is_room = True
            return user_name_element.get_text()
        else:
            print(f'当前不是直播间')
            self.is_room = False
            return False

    # 是否在直播间页面
    def is_live_room_page(self):
        if self.device(text="点击进入直播间").exists:
            self.is_room = True
            return True
        else:
            self.is_room = False
            return False

    # 检查直播间名称是否存在

    def is_live_room_page_exist(self):
        room_name_element = self.device(
            resourceId="com.ss.android.ugc.aweme:id/1tz")
        if room_name_element.exists:
            # 获取直播间名称
            room_name = room_name_element.get_text()
            print(f'直播间名称: {room_name}')
            # //*[@resource-id="com.ss.android.ugc.aweme:id/xr7"]
            # 直播间介绍
            room_intro_element = self.device(
                resourceId="com.ss.android.ugc.aweme:id/xr7")
            if room_intro_element.exists:
                room_intro = room_intro_element.get_text()
                print(f'直播间介绍: {room_intro}')
            return room_name, room_intro
        else:
            return False, False

    # 点击 //android.widget.TextView[@text="点击进入直播间"]
    def click_live_room(self):
        try:
            self.device(text="点击进入直播间").click()
            print(f'点击进入直播间')
        except Exception as e:
            print(f'点击进入直播间失败: {e}')

    # 不是喜欢的直播间
    def not_like_room(self):
        # 长按屏幕
        self.device.long_click(
            x=0.5, y=0.5, duration=random.uniform(0.5, 1))
        print(f'长按屏幕')
        # //android.widget.TextView[@text="不感兴趣"]
        if self.device(text="不感兴趣").exists:
            self.device(text="不感兴趣").click()
            print(f'点击不感兴趣')
            # //android.widget.TextView[@text="减少此类型"]
            time.sleep(random.uniform(0.5, 1))
            if self.device(text="减少此类型").exists:
                self.device(text="减少此类型").click()
                print(f'点击减少此类型')
                return True

    # 翻到下一页
    def next_page(self):
        try:
            # 假设有一个向下滑动的按钮，可以通过描述或文本定位
            swipe_element = self.device(description="Next Page")
            if swipe_element.exists:
                swipe_element.click()
            else:
                scale = random.uniform(0.2, 0.4)
                self.device.swipe_ext("up", scale=scale, steps=10)
                print(f'翻到下一页')
                time.sleep(1)
        except Exception as e:
            print(f'翻到下一页失败: {e}')

    # 点赞
    def like(self):
        # 点赞次数
        like_count = random.randint(20, 40)
        while like_count > 0:
            # 偏左 x,y加上随机偏移量
            x = self.center[0] + random.uniform(100, 200)
            y = self.center[1] + random.uniform(300, 400)
            self.device.click(x, y)
            print(f'点赞')
            time.sleep(random.uniform(0.1, 0.2))
            like_count -= 1

    # 文字输入

    def input_text(self, text):
        self.device.send_keys(text)

    # 检查应用是否在运行，如果不在运行则打开应用
    def app_running(self, package):
        try:
            # 检查应用是否安装
            current_app = self.device.app_current()
            if current_app['package'] == package:
                print(f'应用{package}已打开')
                return True
            else:
                try:
                    self.device.app_start(package)
                    print(f'应用{package}成功打开')
                    return True
                except Exception as e:
                    print(f"无法打开{package}: {e}")
                    return False
        except Exception as e:
            print(f"无法获取当前应用信息: {e}")
            return False


# 获取设备列表
def get_devices():
    cmd = ['adb', 'devices']
    output = subprocess.check_output(cmd).decode('utf-8')
    devices = []
    for line in output.split('\n')[1:]:
        if line.strip():
            serial = line.split()[0]
            devices.append(serial)
    return devices


if __name__ == '__main__':
    # 使用示例
    devices = get_devices()
    for device in devices:
        device = LiveYuying(device)
        device.yunying_live()
