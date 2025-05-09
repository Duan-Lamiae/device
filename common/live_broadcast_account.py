# -*- coding: utf-8 -*-
import sys
import random
import time
import base64
import threading
from PIL import Image
import uiautomator2 as u2
from datetime import datetime
from log_record.log_sql_lite import LogRecordSQLite
from log_record.log_utils import yunying_logger

try:
    from .config import Config
    from .nurture_config_manager import NurtureConfigManager
except Exception as ex:
    print(ex)
    exit(1)


class LiveBroadcastAccount:
    def __init__(self, serial):
        self.serial = serial
        self.device = u2.connect_usb(serial)
        self.size = self.device.window_size()
        self.center = (self.size[0] / 2, self.size[1] / 2)
        self.stop_event = threading.Event()  # 添加 Event 对象
        self.stop_running = False
        # self.logger = LogRecord()
        self.logger = LogRecordSQLite()
        self.current_account_id = "000000"
        # 加载养号配置
        config = Config(serial)
        self.nurture_config = config.read_nurture_config()
        if not self.nurture_config:
            self.nurture_config = NurtureConfigManager.get_default_config()
            config.save_nurture_config(self.nurture_config)

        self.start_time = datetime.now()
        # self.adb = AutoAdb()

    def app_running(self, package='com.taobao.qianniu'):
        """检查应用是否在运行，如果不在运行则启动它"""
        try:
            # 检查应用是否安装
            current_app = self.device.app_current()
            if current_app['package'] == package:
                yunying_logger.info(
                    self.serial,
                    f'应用{package}已打开'
                )
                return True
            else:
                try:
                    self.device.app_start(package)
                    yunying_logger.info(
                        self.serial,
                        f'应用{package}成功打开'
                    )
                    return True
                except Exception as e:
                    yunying_logger.error(
                        self.serial,
                        f"无法打开{package}: {e}"
                    )
                    return False
        except Exception as e:
            yunying_logger.error(
                self.serial,
                f"无法获取当前应用信息: {e}"
            )
            return False
        
    
    def left_next_page(self):
        """
        向左翻页
        :return:
        """
        try:
            duration = random.uniform(0.02, 0.08)  # 减少滑动时间
            swipe_element = self.device(description="Left Swipe")
            if swipe_element.exists:
                swipe_element.click()
            else:
                self.device.swipe_ext("left", scale=0.8, duration=duration)
            time.sleep(random.uniform(0.3, 0.5))  # 减少等待时间并随机化
        except Exception as e:
            yunying_logger.error(
                self.serial,
                f'向左翻页失败: {e}'
            )
    
    def right_next_page(self):
        """
        向右翻页
        """
        try:
            duration = random.uniform(0.02, 0.08)  # 减少滑动时间
            swipe_element = self.device(description="Right Swipe")
            if swipe_element.exists:
                swipe_element.click()
            else:
                self.device.swipe_ext("right", scale=0.8, duration=duration)
            time.sleep(random.uniform(0.3, 0.5))  # 减少等待时间并随机化
        except Exception as e:
            yunying_logger.error(
                self.serial,
                f'向右翻页失败: {e}'
            )


  
    def swipe_next_live(self):
        """上滑到下一个视频:param duration: 滑动持续时间，默认0.05秒"""
        try:
            duration=random.uniform(0.02,0.08)
            # 获取屏幕尺寸
            width, height = self.size
            # 计算滑动起点和终点
            start_y = int(height * 0.6)
            end_y = int(height * 0.2)
            x = width // 2
            # 执行滑动
            self.device.swipe(x, start_y, x, end_y, duration)
            yunying_logger.info(
                self.serial,
                "翻到下一页"
            )
            end=False
            end_page_show=self.device.xpath('//*[@text="暂时没有更多了"]')
            if end_page_show.exists:
                end=True
            time.sleep(random.uniform(0.3, 0.5))
            return end
        except Exception as e:
            yunying_logger.error(
                self.serial,
                f"翻页失败: {str(e)}"
            )
        

    def stop(self):
        """停止运行"""
        try:
            self.stop_running = True  # 设置停止标志
            self.stop_event.set()  # 设置停止事件
            
            # 确保关闭最后一个直播间的记录
            if hasattr(self, 'current_account_id') and self.current_account_id:
                self.logger.close_live_room_record(self.serial, self.current_account_id)
                self.current_account_id = None

            # 返回首页并关闭应用
            package = 'com.taobao.qianniu'
            try:
                self.device.app_stop(package)
                yunying_logger.info(
                    self.serial,
                    f"关闭应用{package}"
                )
            except Exception as e:
                yunying_logger.error(
                    self.serial,
                    f"关闭应用失败: {str(e)}"
                )
                # 尝试强制停止
                try:
                    self.device.shell(f'am force-stop {package}')
                except Exception as force_stop_error:
                    yunying_logger.error(
                        self.serial,
                        f"强制停止应用失败: {str(force_stop_error)}"
                    )
        except Exception as e:
            yunying_logger.error(
                self.serial,
                f"停止养号时出错: {str(e)}"
            )
   
    def _check_app_status(self, package='com.taobao.qianniu'):
        """检查应用状态"""
        if package not in self.device.app_list():
            print(f"{package} 未安装")
            return False
        
        return self.app_running(package)

    def send_comment_message(self):
        """评论视频"""
        try:
            is_commented = False
            comments = ["你好", "亲，在的"]
            comment_text = random.choice(comments)
            time.sleep(2)
            # 点击评论
            comment_btn = self.device.xpath('//android.widget.EditText')
            if comment_btn.exists:
                comment_btn.click()
                time.sleep(1)  # 添加短暂延迟确保UI响应
            else:
                yunying_logger.error(
                    self.serial,
                    "未找到评论按钮"
                )
                return False

            # 点击评论输入框
            comment_input = self.device.xpath('//android.widget.EditText')
            if comment_input.exists:
                comment_input.click()
            else:
                yunying_logger.error(
                    self.serial,
                    "未找到评论输入框"
                )
                return False
            
            time.sleep(1)

            # 切换到 ADBKeyboard
            self.device.set_fastinput_ime(True)
            time.sleep(1)

            # 清空输入框
            self.device.clear_text()
            time.sleep(0.5)

            # 输入评论
            self.device.send_keys(comment_text, clear=True)
            time.sleep(1)

            # 发送评论
            send_btn = self.device.xpath('//android.widget.TextView[@text="发送"]')
            if send_btn.exists:
                send_btn.click()
                is_commented = True
                yunying_logger.info(
                    self.serial,
                    f"评论了{comment_text}"
                )
                time.sleep(random.uniform(0.5, 3))
            else:
                yunying_logger.error(
                    self.serial,
                    "未找到发送按钮"
                )
                is_commented = False
            return is_commented
        except Exception as e:
            yunying_logger.error(
                self.serial,
                f"评论失败: {str(e)}"
            )
            return False

    
 
    def run_qainniu_account(self):
        """千牛收发消息"""
        try:
            while not self.stop_event.is_set():
                if self.stop_event.wait(timeout=5):
                    break
                
                # 打开千牛
                self.app_running()
                time.sleep(random.uniform(1, 2))
                
                # 点击进消息界面
                self.device.xpath('//*[@content-desc="消息"]').click()
                time.sleep(random.uniform(1, 2))
                
                # 获取消息列表中的所有联系人
                contact_items = self.device.xpath('//androidx.recyclerview.widget.RecyclerView').all()
                
                if contact_items:
                    # 随机选择一个联系人
                    random_contact = random.choice(contact_items)
                    random_contact.click()
                    yunying_logger.info(
                        self.serial,
                        "成功选择一个联系人"
                    )
                    # 发送消息
                    self.send_comment_message()
                    time.sleep(random.uniform(1, 2))
                else:
                    yunying_logger.error(
                        self.serial,
                        "未找到任何联系人"
                    )
                    continue
                                
        except Exception as e:
            yunying_logger.error(
                self.serial,
                f"千牛收发消息失败: {str(e)}"
            )
                
                
 