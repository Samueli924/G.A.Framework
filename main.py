import configparser
import os
import time
import win32gui
from utils.log import Logger
import psutil
import win32con
from src.game.game_control import GameControl
import pyautogui
import argparse

position = {
    "main_page": (781, 22),
    "join_meeting": (813, 440)
}


class Recorder:
    def __init__(self):
        self.obs_hwnd = None
        self.zoom_hwnd = None
        self.meeting_hwnd = None
        self.logger = Logger("Recorder", debug=True, save=True, show=True)
        self.config = configparser.ConfigParser()
        self.config.read("config/config.ini")
        self.init_running()
        while True:
            win32gui.EnumWindows(self.winEnumHandler, None)     # 获取窗口hwnd
            if not (self.obs_hwnd and self.zoom_hwnd):
                time.sleep(1)
            else:
                self.logger.info("程序窗口检测结束，启动成功")
                break
        self.obs_gc = GameControl(self.obs_hwnd)
        self.logger.info("开始监测程录屏软件启动进程")
        while True:
            __temp_possibility, _ = self.obs_gc.find_img("img/obs_start.png")
            if __temp_possibility <= 0.8:
                time.sleep(1)
            else:
                self.logger.info("OBS窗口检测启动成功")
                break

        self.gc = GameControl(self.zoom_hwnd)
        self.logger.info("开始监测Zoom程序启动进度")
        while True:
            __temp_possibility, _ = self.gc.find_img("img/main_page.png")
            self.logger.info("当前页面处于主页的可能性为: %.2f%%" % (__temp_possibility * 100))
            if __temp_possibility <= 0.8:
                time.sleep(1)
            else:
                break
        time.sleep(1)
        self.front_obs()
        time.sleep(1)
        pyautogui.press("f12")
        self.logger.info("OBS开始录制")
        time.sleep(1)
        self.logger.info("最大化前置Zoom")
        self.front_zoom()
        time.sleep(1)
        self.gc.mouse_move(position["join_meeting"])
        self.gc.mouse_click()
        self.logger.info("点击成功，等待5秒")
        time.sleep(5)
        while True:
            win32gui.EnumWindows(self.get_meeting_hwnd, None)
            if self.meeting_hwnd:
                self.meeting_gc = GameControl(self.meeting_hwnd)
                while True:
                    __temp_possibility, _ = self.meeting_gc.find_img("img/join_page.png")
                    self.logger.info("当前页面处于会议填写页面的可能性为: %.2f%%" % (__temp_possibility * 100))
                    if __temp_possibility <= 0.8:
                        time.sleep(1)
                    else:
                        break
                break
        self.logger.info("正在输入会议号")
        self.meeting_gc.input_keyboard(meeting_number)
        self.logger.info("等待5秒")
        time.sleep(5)
        while True:
            win32gui.EnumWindows(self.get_meeting_hwnd, None)
            if self.meeting_hwnd:
                self.meeting_gc = GameControl(self.meeting_hwnd)
                while True:
                    __temp_possibility, _ = self.meeting_gc.find_img("img/meeting_password.png")
                    self.logger.info("当前页面处于密码填写页面的可能性为: %.2f%%" % (__temp_possibility * 100))
                    if __temp_possibility <= 0.8:
                        time.sleep(1)
                    else:
                        break
                break
        self.logger.info("正在输入会议密码")
        self.meeting_gc.input_keyboard(meeting_password)
        _t = 0
        dot_count = 1
        while _t < meeting_duration:
            print(f"会议已进行{self.t_time(_t)}/{self.t_time(meeting_duration)}, 正在录屏{'.'* dot_count}")
            _t += 1
            if dot_count >= 6:
                dot_count = 0
            self.front_zoom()
            time.sleep(1)
        self.logger.info("会议结束，正在结束录制")
        self.front_obs()
        time.sleep(1)
        pyautogui.press("f12")
        self.logger.info("程序运行结束，1分钟后关机")
        os.system("shutdown -s -t 60")

    def t_time(self, t):
        hour = t // 3600
        minute = (t - 3600 * hour) // 60
        second = (t - 3600 * hour - 60 * minute)
        return f"{hour}h {minute}m {second}s"

    def start_obs(self):
        self.logger.info("启动OBS Studio")
        obs_path = self.config.get("path", "obs_path")
        os.system(f'start /d "{obs_path}" "" obs64.exe')

    def start_zoom(self):
        self.logger.info("启动Zoom")
        zoom_path = self.config.get("path", "zoom_path")
        os.system(f'start /d "{zoom_path}" "" Zoom.exe')

    def front_zoom(self):
        win32gui.ShowWindow(self.zoom_hwnd, win32con.SW_MAXIMIZE)
        win32gui.SetForegroundWindow(self.zoom_hwnd)

    def front_obs(self):
        win32gui.ShowWindow(self.obs_hwnd, win32con.SW_MAXIMIZE)
        win32gui.SetForegroundWindow(self.obs_hwnd)

    def checkProcessRunning(self, processName: str):
        for proc in psutil.process_iter():
            try:
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def check_running_status(self):
        fail_time = 0
        while True:
            if fail_time >= 5:
                self.init_running()
                break
            if (not self.checkProcessRunning("OBS")) or (not self.checkProcessRunning("Zoom")):
                self.logger.info("程序未完成启动，等待5秒")
                fail_time += 1
                time.sleep(5)
            else:
                self.logger.info("程序启动成功，5秒后继续")
                time.sleep(5)
                break

    def init_running(self):
        if not self.checkProcessRunning("OBS"):
            self.logger.info("OBS Studio未运行")
            self.start_obs()
        self.start_zoom()
        self.check_running_status()

    def winEnumHandler(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            if "OBS" in win32gui.GetWindowText(hwnd):
                self.obs_hwnd = hwnd
            if "Zoom" in win32gui.GetWindowText(hwnd):
                self.zoom_hwnd = hwnd

    def get_meeting_hwnd(self, hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            if "Zoom" in win32gui.GetWindowText(hwnd) and hwnd != self.zoom_hwnd:
                self.meeting_hwnd = hwnd


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TripleE Boot Zoom And OBS on demand')  # 命令行传参
    parser.add_argument('-debug', '--debug', action='store_true', help='Enable debug output in console')
    parser.add_argument('-m', '--meeting', help='Meeting Number ID')
    parser.add_argument('-p', '--password', help='Meeting Password')
    parser.add_argument('-d', '--duration', help='Meeting Duration[Second(s)]')

    args = parser.parse_args()  # 定义专用参数变量
    if not (args.meeting and args.password and args.duration):
        input("参数不足,点击回车键退出")
        exit()
    debug = args.debug  # debug输出  Default:False
    meeting_number = str(args.meeting)  # 会议号
    meeting_password = str(args.password)  # 会议密码
    meeting_duration = int(args.duration)   # 会议时长
    recorder = Recorder()
    # python main.py -m 8936901699 -p Mx7pmU -d 10
