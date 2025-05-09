# -*- coding: utf-8 -*-
# auto_adb.py
import os
import subprocess
import platform


class AutoAdb:
    def __init__(self):
        try:
            adb_path = 'adb'
            subprocess.Popen([adb_path], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            self.adb_path = adb_path
        except OSError:
            if platform.system() == 'Windows':
                adb_path = os.path.join('Tools', "adb", 'adb.exe')
                try:
                    subprocess.Popen(
                        [adb_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.adb_path = adb_path
                except OSError:
                    pass
            else:
                try:
                    subprocess.Popen(
                        [adb_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError:
                    pass
            print('请安装 ADB 及驱动并配置环境变量')
            exit(1)

    def get_devices(self):
        """获取已连接的设备列表"""
        result = subprocess.run([self.adb_path, 'devices'],
                                capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # 忽略标题行
        return [line.split('\t')[0] for line in lines if 'device' in line]

    def get_battery_info(self, device):
        """获取设备电池信息"""
        result = subprocess.run(
            [self.adb_path, '-s', device, 'shell', 'dumpsys', 'battery'],
            capture_output=True,
            text=True
        )
        level = 0
        is_charging = False
        for line in result.stdout.splitlines():
            if 'level' in line:
                level = int(line.strip().split(': ')[1])
            if 'status' in line:
                status = line.strip().split(': ')[1]
                if status == '2':  # 充电中
                    is_charging = True
        return level, is_charging

    # 获取手机型号
    def get_model(self, device=None):
        cmd = [self.adb_path]
        if device:
            cmd.extend(['-s', device])
        cmd.extend(['shell', 'getprop', 'ro.product.model'])
        process = subprocess.run(cmd, capture_output=True, text=True)
        return process.stdout.strip()

    # 获取设备品牌
    def get_brand(self, device=None):
        cmd = [self.adb_path]
        if device:
            cmd.extend(['-s', device])
        cmd.extend(['shell', 'getprop', 'ro.product.brand'])
        process = subprocess.run(cmd, capture_output=True, text=True)
        return process.stdout.strip()

    # 获取设备序列号
    def get_serialno(self, device=None):
        cmd = [self.adb_path]
        if device:
            cmd.extend(['-s', device])
        cmd.extend(['get-serialno'])
        process = subprocess.run(cmd, capture_output=True, text=True)
        return process.stdout.strip()

    # 获取屏幕尺寸
    def get_screen(self, device=None):
        cmd = [self.adb_path]
        if device:
            cmd.extend(['-s', device])
        cmd.extend(['shell', 'wm', 'size'])
        process = subprocess.run(cmd, capture_output=True, text=True)
        return process.stdout.strip()

    def run(self, raw_command, device=None):
        cmd = [self.adb_path]
        if device:
            cmd.extend(['-s', device])
        cmd.extend(raw_command.split())
        print(' '.join(cmd))
        process = subprocess.run(cmd, capture_output=True, text=True)
        return process.stdout.strip()

    def test_device(self, device=None):
        print('检查设备是否连接...')
        cmd = [self.adb_path, 'devices']
        if device:
            cmd.extend(['-s', device])
        process = subprocess.run(cmd, capture_output=True, text=True)
        output = process.stdout

        if output == 'List of devices attached\n\n':
            print('未找到设备')
            print('adb 输出:')
            print(output)
            return False
        print('设备已连接')
        print('adb 输出:')
        print(output)
        return True

    def test_density(self):
        process = os.popen(self.adb_path + ' shell wm density')
        output = process.read()
        return output

    def test_device_detail(self):
        process = os.popen(self.adb_path + ' shell getprop ro.product.device')
        output = process.read()
        return output

    # 设备系统版本
    def test_device_os(self):
        process = os.popen(
            self.adb_path + ' shell getprop ro.build.version.release')
        output = process.read()
        return output

    def adb_path(self):
        return self.adb_path
