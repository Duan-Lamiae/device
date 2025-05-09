import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel, QMessageBox
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import QTimer, Qt

from common.auto_adb import AutoAdb
from common.video_capture import PreviewWindow
from common.get_app import AppManager
from common.setting import SettingsDialog

from common.live_broadcast_account import LiveBroadcastAccount
from common.nurture_config_manager import NurtureConfigManager
from common.workers import DeviceInfoWorker, AppInstallWorker
from common.config import Config
import threading

class DeviceManager(QWidget):
    def __init__(self):
        super().__init__()
        self.preview_window = PreviewWindow()
        self.init_ui()
        self.auto_adb = AutoAdb()
        
        # 初始化工作线程
        self.device_info_worker = DeviceInfoWorker()
        self.device_info_worker.deviceInfoReady.connect(self.update_device_info)
        self.device_info_worker.batteryInfoReady.connect(self.update_battery_info)
        self.device_info_worker.appStatusReady.connect(self.update_app_status)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_devices_and_battery)
        self.update_timer.start(5000)
        self.sop_instances = {}
        self.get_devices()
        
    def update_device_info(self, device, info):
        """更新设备信息到UI"""
        for row in range(self.table.rowCount()):
            serial_item = self.table.item(row, 0)
            if serial_item and serial_item.text() == device:
                # 品牌/型号
                brand_model = f"{info['brand']}/{info['model']}"
                brand_item = QTableWidgetItem(brand_model)
                brand_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, brand_item)
                
                # 屏幕分辨率
                resolution_item = QTableWidgetItem(info['resolution'])
                resolution_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, resolution_item)
                
                # 系统版本
                android_item = QTableWidgetItem(info['android_ver'])
                android_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, android_item)
                break
                
    def update_battery_info(self, device, level, is_charging):
        """更新电池信息到UI"""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == device:
                battery_widget = self.create_battery_widget(level, is_charging)
                self.table.setCellWidget(row, 4, battery_widget)
                break

    def update_app_status(self, device, app_status):
        """更新应用安装状态到UI"""
        for row in range(self.table.rowCount()):
            serial_item = self.table.item(row, 0)
            if serial_item and serial_item.text() == device:
                # ADBKeyBoard 状态
                if app_status['adb_keyboard']:
                    adb_item = QTableWidgetItem('已安装')
                    adb_item.setTextAlignment(Qt.AlignCenter)
                    adb_item.setForeground(QColor('green'))
                    self.table.setItem(row, 5, adb_item)
                else:
                    install_btn = QPushButton('安装')
                    install_btn.clicked.connect(lambda checked, d=device: self.install_adb_keyboard(d))
                    self.table.setCellWidget(row, 5, install_btn)

                # 抖音安装状态
                douyin_item = QTableWidgetItem('已安装' if app_status['douyin'] else '未安装')
                douyin_item.setTextAlignment(Qt.AlignCenter)
                douyin_item.setForeground(QColor('green') if app_status['douyin'] else QColor('red'))
                self.table.setItem(row, 6, douyin_item)
                break

    def init_ui(self):
        self.setWindowTitle('设备管理器')
        self.showMaximized()
        self.table = QTableWidget()
        # 设置列数为10（移除直播运营开关）
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            '序列号', '品牌/型号', '屏幕分辨率',
            '系统版本', '电池电量', 'ADBKeyBoard',
            '抖音', '设置', '千牛开关', 
            '预览'
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)

        # 设置列宽
        self.table.setColumnWidth(0, 150)  # 序列号
        self.table.setColumnWidth(1, 200)  # 品牌/型号
        self.table.setColumnWidth(2, 120)  # 屏幕分辨率

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def get_device_info(self, device):
        """获取设备详细信息"""
        try:
            # 使用 AutoAdb 类中的方法获取信息
            brand = self.auto_adb.get_brand(device)
            model = self.auto_adb.get_model(device)
            serial = self.auto_adb.get_serialno(device)
            android_ver = self.auto_adb.test_device_os()
            resolution = self.auto_adb.get_screen(device).replace("Physical size: ", "")

            return {
                'brand': brand,
                'model': model,
                'serial': serial,
                'android_ver': android_ver,
                'resolution': resolution
            }
        except Exception as e:
            print(f"获取设备信息失败: {str(e)}")
            return {
                'brand': '未知',
                'model': '未知',
                'serial': '未知',
                'android_ver': '未知',
                'resolution': '未知'
            }


    def get_devices(self):
        devices = self.auto_adb.get_devices()
        self.table.setRowCount(len(devices))
        
        for i, device in enumerate(devices):
            # 初始化设备配置
            self.init_device_config(device)
            
            # 创建基本UI元素
            serial_item = QTableWidgetItem(device)
            serial_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, serial_item)
            
            # 启动工作线程获取设备信息
            self.device_info_worker.set_device(device)
            self.device_info_worker.start()
            
            # 添加其他控制按钮
            self.add_control_buttons(i, device)

    def add_control_buttons(self, row, device):
        """为每个设备添加控制按钮"""
        # 设置按钮
        settings_btn = QPushButton('设置')
        settings_btn.clicked.connect(lambda: self.open_settings(device))
        self.table.setCellWidget(row, 7, settings_btn)

        # 千牛开关
        sop_btn = QPushButton('开启')
        sop_btn.setCheckable(True)
        # 使用 lambda 传递正确的参数
        sop_btn.clicked.connect(lambda checked, d=device: self.toggle_sop(checked, d))
        self.table.setCellWidget(row, 8, sop_btn)

        # 预览按钮
        preview_btn = QPushButton('预览')
        preview_btn.setCheckable(True)
        # 使用 lambda 传递正确的参数
        preview_btn.clicked.connect(lambda checked, d=device: self.toggle_preview(checked, d))
        self.table.setCellWidget(row, 9, preview_btn)

    def toggle_preview(self, checked, device):
        """切换预览窗口"""
        if checked:
            self.preview_window.add_device(device)
        else:
            self.preview_window.remove_device(device)

    def update_devices_and_battery(self):
        current_devices = self.auto_adb.get_devices()
        existing_devices = []

        for row in range(self.table.rowCount()):
            device_item = self.table.item(row, 0)
            if device_item:
                existing_devices.append(device_item.text())

        if set(current_devices) != set(existing_devices):
            self.get_devices()
            return

        for row in range(self.table.rowCount()):
            device_item = self.table.item(row, 0)
            if device_item:
                device = device_item.text()
                battery_level, is_charging = self.auto_adb.get_battery_info(device)
                battery_widget = self.create_battery_widget(battery_level, is_charging)
                self.table.setCellWidget(row, 4, battery_widget)

    def toggle_sop(self, checked, device):
        """切换养号状态"""
        button = self.sender()
        if checked:
            try:
                package = 'com.taobao.qianniu'
                if not AppManager.check_app_installed(device, package):
                    button.setChecked(False)
                    button.setText('开启')
                    reply = QMessageBox.question(
                        self,
                        "提示",
                        "千牛未安装，是否现在安装？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.install_douyin(device)
                    return

                # 检查配置是否正确加载
                config = Config(device)
                if not config.nurture_config_file.exists():
                    button.setChecked(False)
                    button.setText('开启')
                    QMessageBox.warning(self, "错误", "配置文件不存在，请先进行设置")
                    return

                # 创建养号实例并确保配置正确加载
                sop_instance = LiveBroadcastAccount(device)
                if not sop_instance:
                    raise Exception("无法创建实例")

                # 创建线程
                sop_thread = threading.Thread(
                    target=sop_instance.run_qainniu_account
                )
                sop_thread.daemon = True  # 设置为守护线程
                sop_thread.start()

                self.sop_instances[device] = {
                    'instance': sop_instance,
                    'thread': sop_thread
                }

                button.setText('关闭')
                print(f"设备 {device} 千牛已开启")
            except Exception as e:
                button.setChecked(False)
                button.setText('开启')
                error_msg = f"启动千牛失败: {str(e)}\n详细错误: {type(e).__name__}"
                print(error_msg)  # 打印详细错误信息到控制台
                QMessageBox.warning(self, "错误", error_msg)
        else:
            # 停止养号运营
            if device in self.sop_instances:
                try:
                    sop_instance = self.sop_instances[device]['instance']
                    sop_thread = self.sop_instances[device]['thread']
                    
                    # 调用停止方法
                    sop_instance.stop()
                    
                    # 等待线程结束，设置较长的超时时间确保清理完成
                    sop_thread.join(timeout=10)
                    
                    # 检查线程是否真的结束了
                    if sop_thread.is_alive():
                        print(f"警告：设备 {device} 的千牛线程未能正常结束")
                        # 可以选择强制结束或者提示用户
                    
                    # 清理实例
                    del self.sop_instances[device]
                    button.setText('开启')
                    print(f"设备 {device} 千牛已关闭")
                except Exception as e:
                    print(f"停止设备 {device} 千牛时出错: {str(e)}")
                    QMessageBox.warning(self, "错误", f"停止千牛失败: {str(e)}")

    def open_settings(self, device):
        """打开设置对话框"""
        try:
            # 确保设备的配置目录和养号配置文件存在
            config = Config(device)
            config.ensure_config_dir()

            # 如果养号配置文件不存在，创建默认配置
            if not config.nurture_config_file.exists():
                default_config = NurtureConfigManager.get_default_config()
                config.save_nurture_config(default_config)

            # 打开设置对话框
            dialog = SettingsDialog(device, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开设置失败: {str(e)}")

    def create_battery_widget(self, level, is_charging):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)

        if is_charging:
            charging_label = QLabel()
            charging_label.setPixmap(QIcon('icon/Charging.ico').pixmap(16, 16))
            layout.addWidget(charging_label)

        progress = QProgressBar()
        progress.setValue(level)
        progress.setAlignment(Qt.AlignCenter)
        progress.setFormat(f"{level}%")
        progress.setStyleSheet("""
            QProgressBar {
                text-align: center;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        progress.setMaximumWidth(100)
        layout.addWidget(progress)

        widget.setLayout(layout)
        return widget
    
    def install_adb_keyboard(self, device):
        """安装并设置ADBKeyboard输入法"""
        install_worker = AppInstallWorker(device, 'adbkeyboard.apk')
        install_worker.installComplete.connect(self.handle_install_complete)
        install_worker.start()
        
    def handle_install_complete(self, device, success):
        """处理安装完成事件"""
        if success:
            if AppManager.set_input_method(device):
                self.get_devices()  # 刷新设备列表
            QMessageBox.information(self, "成功", "ADBKeyboard 安装成功！")
        else:
            QMessageBox.warning(self, "错误", "ADBKeyboard 安装失败！")



    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        # 停止所有养号实例
        for device, instance_data in self.sop_instances.items():
            instance_data['instance'].stop()
            instance_data['thread'].join(timeout=1.0)

        # 关闭预览窗口
        if self.preview_window:
            self.preview_window.close()

        event.accept()
    
    def init_device_config(self, device):
        """初始化设备配置"""
        try:
            config = Config(device)
            config.ensure_config_dir()

            # 检查并初始化配置
            if not config.nurture_config_file.exists():
                default_config = NurtureConfigManager.get_default_config()
                config.save_nurture_config(default_config)
                print(f"设备 {device} 配置初始化成功")
        except Exception as e:
            print(f"初始化设备 {device} 配置失败: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    manager = DeviceManager()
    manager.show()
    sys.exit(app.exec_())

