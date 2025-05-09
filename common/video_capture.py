import subprocess
import time
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import tempfile
import os


class PreviewWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.devices = set()
        self.scrcpy_processes = {}  # 存储每个设备的 QProcess 实例
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Devices Preview')
        self.setGeometry(100, 100, 1200, 800)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

    def add_device(self, device):
        if device not in self.devices:
            self.devices.add(device)
            self.start_scrcpy(device)

    def remove_device(self, device):
        if device in self.devices:
            self.stop_scrcpy(device)
            self.devices.remove(device)

    def start_scrcpy(self, device):
        try:
            process = QProcess(self)
            arguments = [
                '-s', device,
                '--window-width', '480',
                '--window-height', '800',
                '--no-audio',
                '--video-bit-rate', '2M',
                '--max-fps', '15',
                '--window-title', f'Device Preview - {device}',
                '--no-control',
                '--render-driver', 'software',
                '--always-on-top'
            ]
            print(f"启动预览命令: scrcpy {' '.join(arguments)}")
            process.start('scrcpy', arguments)
            if not process.waitForStarted(3000):  # 等待3秒确认进程是否启动
                print(f"无法启动 scrcpy 进程（设备 {device}）")
                return
            print(f"scrcpy 进程已启动（设备 {device}）")
            process.errorOccurred.connect(lambda error, dev=device: self.handle_error(error, dev))
            process.readyReadStandardError.connect(lambda dev=device: self.handle_std_error(dev))
            self.scrcpy_processes[device] = process
        except Exception as e:
            print(f"启动预览错误（设备 {device}）: {e}")

    def stop_scrcpy(self, device):
        process = self.scrcpy_processes.get(device)
        if process:
            process.terminate()
            if not process.waitForFinished(3000):
                process.kill()
            del self.scrcpy_processes[device]
            print(f"已停止设备 {device} 的预览")

    def handle_error(self, error, device):
        print(f"scrcpy 进程错误（设备 {device}）: {error}")

    def handle_std_error(self, device):
        process = self.scrcpy_processes.get(device)
        if process:
            err = process.readAllStandardError().data().decode()
            if err:
                print(f"scrcpy 标准错误（设备 {device}）: {err}")

    # def closeEvent(self, event):
    #     """关闭窗口时清理资源"""
    #     # 停止所有养号实例
    #     for device, instance_data in self.sop_instances.items():
    #         instance_data['instance'].stop()
    #         instance_data['thread'].join(timeout=1.0)

    #     # 关闭所有预览窗口
    #     for preview in self.preview_windows.values():
    #         preview.close()
    #     self.preview_windows.clear()

    #     event.accept()

    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        # 停止所有设备的预览
        for device in list(self.scrcpy_processes.keys()):
            self.stop_scrcpy(device)
        self.scrcpy_processes.clear()
        event.accept()


class VideoCapture(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, device):
        super().__init__()
        self.device = device
        self.running = True
        self.video_path = os.path.join(
            tempfile.gettempdir(), f'video-{device}')

    def run(self):
        try:
            import cv2
            cap = cv2.VideoCapture(self.video_path)

            while self.running and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_frame.shape
                    image = QImage(rgb_frame.data, w, h, ch *
                                   w, QImage.Format_RGB888)
                    scaled_image = image.scaled(
                        180, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.frame_ready.emit(scaled_image)

                self.msleep(33)

            cap.release()

        except Exception as e:
            print(f"视频捕获错误: {e}")

    def stop(self):
        self.running = False
