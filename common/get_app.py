# -*- coding: utf-8 -*-
import subprocess


class AppManager:
    @staticmethod
    def get_all_app(device=None):
        """获取所有应用程序的包名"""
        cmd = ['adb']
        if device:
            cmd.extend(['-s', device])
        cmd.extend(['shell', 'pm', 'list', 'packages'])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            package_names = result.stdout.strip().split('\n')
            return package_names
        else:
            print("未找到应用程序")
            return None

    @staticmethod
    def get_app_id(app_name, device=None):
        """获取应用程序的包名"""
        cmd = ['adb']
        if device:
            cmd.extend(['-s', device])
        cmd.extend(['shell', 'pm', 'list', 'packages', '|', 'grep', app_name])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            package_name = result.stdout.strip().split(':')[-1]
            return package_name
        else:
            print("未找到应用程序")
            return None

    @staticmethod
    def open_app(package_name, device=None):
        """打开指定的安卓应用程序"""
        cmd = ['adb']
        if device:
            cmd.extend(['-s', device])
        cmd.extend(['shell', 'monkey', '-p', package_name,
                   '-c', 'android.intent.category.LAUNCHER', '1'])
        subprocess.run(cmd)

    @staticmethod
    def check_adb_keyboard(device):
        """检查ADB键盘是否安装"""
        result = subprocess.run(
            ['adb', '-s', device, 'shell', 'ime', 'list', '-a'],
            capture_output=True,
            text=True
        )
        return 'com.android.adbkeyboard/.AdbIME' in result.stdout

    @staticmethod
    def check_app_installed(device, package_name):
        """检查指定应用是否安装"""
        result = subprocess.run(
            ['adb', '-s', device, 'shell', 'pm', 'list', 'packages', package_name],
            capture_output=True,
            text=True
        )
        return package_name in result.stdout

    @staticmethod
    def install_adb_keyboard(apk_path, device=None):
        """安装ADBKeyboard输入法"""
        if not apk_path:
            print('apk_path 为空, 安装失败！')
            return False

        cmd = ['adb']
        if device:
            cmd.extend(['-s', device])

        # 检查是否已安装
        if AppManager.check_adb_keyboard(device):
            print('ADBKeyboard 已安装')
            return True

        try:
            cmd.extend(
                ['install', '-r', '--bypass-low-target-sdk-block', apk_path])
            subprocess.run(cmd)
            return True
        except Exception as e:
            print(f'安装失败！{e}')
            return False

    @staticmethod
    def set_input_method(device=None):
        """设置ADBKeyboard为默认输入法"""
        try:
            cmd_base = ['adb']
            if device:
                cmd_base.extend(['-s', device])

            # 设置为ADBKeyboard输入法
            cmd1 = cmd_base + ['shell', 'settings', 'put', 'secure',
                               'default_input_method', 'com.android.adbkeyboard/.AdbIME']
            subprocess.run(cmd1)

            # 启用输入法
            cmd2 = cmd_base + ['shell', 'ime', 'enable',
                               'com.android.adbkeyboard/.AdbIME']
            subprocess.run(cmd2)

            # 切换到ADBKeyboard
            cmd3 = cmd_base + ['shell', 'ime', 'set',
                               'com.android.adbkeyboard/.AdbIME']
            subprocess.run(cmd3)

            print('设置输入法成功')
            return True
        except Exception as e:
            print(f'设置输入法失败：{e}')
            return False


if __name__ == '__main__':
    # 使用示例
    app_manager = AppManager()

    # 获取所有应用
    # apps = app_manager.get_all_app()
    # print(apps)

    # 查找并打开抖音
    app_name = 'com.ss.android.ugc.aweme'
    package_name = app_manager.get_app_id(app_name)
    if package_name:
        app_manager.open_app(package_name)
