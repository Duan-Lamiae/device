from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
from common.auto_adb import AutoAdb
from common.get_app import AppManager

class DeviceInfoWorker(QThread):
    deviceInfoReady = pyqtSignal(str, dict)
    batteryInfoReady = pyqtSignal(str, int, bool)
    appStatusReady = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.auto_adb = AutoAdb()
        self.device = None
        
    def set_device(self, device):
        self.device = device
        
    def run(self):
        if not self.device:
            return
            
        try:
            # 获取设备基本信息
            info = {
                'brand': self.auto_adb.get_brand(self.device),
                'model': self.auto_adb.get_model(self.device),
                'serial': self.auto_adb.get_serialno(self.device),
                'android_ver': self.auto_adb.test_device_os(),
                'resolution': self.auto_adb.get_screen(self.device).replace("Physical size: ", "")
            }
            self.deviceInfoReady.emit(self.device, info)
            
            # 获取电池信息
            battery_level, is_charging = self.auto_adb.get_battery_info(self.device)
            self.batteryInfoReady.emit(self.device, battery_level, is_charging)
            
            # 获取应用安装状态
            app_status = {
                'adb_keyboard': AppManager.check_adb_keyboard(self.device),
                'douyin': AppManager.check_app_installed(self.device, 'com.ss.android.ugc.aweme')
            }
            self.appStatusReady.emit(self.device, app_status)
            
        except Exception as e:
            print(f"获取设备信息失败: {str(e)}")

class AppInstallWorker(QThread):
    installComplete = pyqtSignal(str, bool)
    
    def __init__(self, device, apk_path):
        super().__init__()
        self.device = device
        self.apk_path = apk_path
        
    def run(self):
        try:
            result = AppManager.install_adb_keyboard(self.apk_path, self.device)
            self.installComplete.emit(self.device, result)
        except Exception as e:
            print(f"安装失败: {str(e)}")
            self.installComplete.emit(self.device, False)
