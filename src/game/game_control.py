# from gameLib.image_proc import match_img_knn
import configparser
import ctypes
import logging
import os
import sys
import time
import traceback
import random
import cv2
import numpy as np
import win32api
import win32con
import win32gui
import json
import win32ui
from PIL import Image


class GameControl():
    def __init__(self, hwnd):
        self.run = True
        self.debug_enable = False



        self.hwnd = hwnd

        # 左 上 右 下 自左上
        l, t, r, b = win32gui.GetWindowRect(self.hwnd)
        l2, t2, r2, b2 = win32gui.GetClientRect(self.hwnd)

        # 内部控件的高和宽
        self._client_h = b2 - t2
        self._client_w = r2 - l2

        # 窗口的左右下边框宽度和窗口上边框宽度
        self._border_l = ((r - l) - (r2 - l2)) // 2
        self._border_t = ((b - t) - (b2 - t2)) - self._border_l

        print("游戏窗口左上点({},{}) ；宽{} 高{}；窗口内控件左上点({},{}) ;宽{} 高{}".format(l, t, r - l, b - t, l2, t2, self._client_w,
                                                                        self._client_h))

    def init_bitmap(self):
        self.hwindc = win32gui.GetWindowDC(self.hwnd)
        self.srcdc = win32ui.CreateDCFromHandle(self.hwindc)
        self.memdc = self.srcdc.CreateCompatibleDC()
        self.bmp = win32ui.CreateBitmap()
        self.bmp.CreateCompatibleBitmap(
            self.srcdc, self._client_w, self._client_h)
        self.memdc.SelectObject(self.bmp)

    def create_bitmap(self, w, h):
        hwindc = win32gui.GetWindowDC(self.hwnd)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, w, h)
        return hwindc, srcdc, memdc, bmp

    def screenshot_window(self, file_name=None, gray=False):
        """
        窗口截图
            :param file_name: 截图文件的保存名称
            :param gray: 是否返回灰度图像，0：返回BGR彩色图像，其他：返回灰度黑白图像
            :return: file_name为空则返回RGB数据
        """
        try:
            if not hasattr(self, 'memdc'):
                self.init_bitmap()
            self.memdc.BitBlt((0, 0), (self._client_w, self._client_h), self.srcdc,
                              (self._border_l, self._border_t), win32con.SRCCOPY)
            if file_name is not None:
                self.bmp.SaveBitmapFile(self.memdc, file_name)
                return
            else:
                signedIntsArray = self.bmp.GetBitmapBits(True)
                img = np.fromstring(signedIntsArray, dtype='uint8')
                img.shape = (self._client_h, self._client_w, 4)
                if gray:
                    return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                else:
                    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


        except Exception:
            self.init_bitmap()
            print("游戏窗口截图失败")
            a = traceback.format_exc()
            print(a)

    def screenshot_part(self, pos1, pos2, file_name=None, gray=False):
        """
        窗口区域截图
            :param pos1: (x,y) 截图区域的左上角坐标
            :param pos2: (x,y) 截图区域的右下角坐标
            :param file_name=None: 截图文件的保存路径
            :param gray=0: 是否返回灰度图像，0：返回BGR彩色图像，其他：返回灰度黑白图像
            :return: file_name为空则返回RGB数据
        """
        w = pos2[0] - pos1[0]
        h = pos2[1] - pos1[1]

        hwindc, srcdc, memdc, bmp = self.create_bitmap(w, h)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (w, h), srcdc,
                     (pos1[0] + self._border_l, pos1[1] + self._border_t), win32con.SRCCOPY)

        if file_name != None:
            bmp.SaveBitmapFile(memdc, file_name)
            srcdc.DeleteDC()
            memdc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwindc)
            win32gui.DeleteObject(bmp.GetHandle())
            return
        else:
            signedIntsArray = bmp.GetBitmapBits(True)
            img = np.fromstring(signedIntsArray, dtype='uint8')
            img.shape = (h, w, 4)
            srcdc.DeleteDC()
            memdc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwindc)
            win32gui.DeleteObject(bmp.GetHandle())
            if gray:
                return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            else:
                return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def find_color(self, region, color, tolerance=0):
        """
        寻找颜色
            :param region: ((x1,y1),(x2,y2)) 欲搜索区域的左上角坐标和右下角坐标
            :param color: (r,g,b) 欲搜索的颜色
            :param tolerance=0: 容差值
            :return: 成功返回客户区坐标，失败返回-1
        """
        img = Image.fromarray(self.screenshot_part(
            region[0], region[1]), 'RGB')
        width, height = img.size
        r1, g1, b1 = color[:3]
        for x in range(width):
            for y in range(height):
                try:
                    pixel = img.getpixel((x, y))
                    r2, g2, b2 = pixel[:3]
                    if abs(r1-r2) <= tolerance and abs(g1-g2) <= tolerance and abs(b1-b2) <= tolerance:
                        return x+region[0][0], y+region[0][1]
                except Exception:
                    print('查找颜色失败')
                    a = traceback.format_exc()
                    print(a)
                    return -1
        return -1

    def check_color(self, pos, color, tolerance=0):
        """
        对比窗口内某一点的颜色
            :param pos: (x,y) 欲对比的坐标
            :param color: (r,g,b) 欲对比的颜色
            :param tolerance=0: 容差值
            :return: 成功返回True,失败返回False
        """
        img = Image.fromarray(self.screenshot_window(), 'RGB')
        r1, g1, b1 = color[:3]
        r2, g2, b2 = img.getpixel(pos)[:3]
        if abs(r1-r2) <= tolerance and abs(g1-g2) <= tolerance and abs(b1-b2) <= tolerance:
            return True
        else:
            return False

    def find_img(self, img_template_path, part=False, pos1=None, pos2=None, gray=False):
        """
        查找图片
            :param img_template_path: 欲查找的图片路径
            :param part=0: 是否全屏查找
            :param pos1=None: 欲查找范围的左上角坐标
            :param pos2=None: 欲查找范围的右下角坐标
            :param gray=0: 是否彩色查找
            :return: (maxVal,maxLoc) maxVal为相关性，越接近1越好，maxLoc为得到的坐标
        """
        # 获取截图
        if part:
            img_src = self.screenshot_part(pos1, pos2,gray=gray)
        else:
            img_src = self.screenshot_window(None, gray)

        # 读入文件
        if gray:
            img_template = cv2.imread(img_template_path, cv2.IMREAD_GRAYSCALE)
        else:
            img_template = cv2.imread(img_template_path, cv2.IMREAD_COLOR)

        try:
            res = cv2.matchTemplate(
                img_src, img_template, cv2.TM_CCOEFF_NORMED)
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(res)

            return maxVal, maxLoc
        except Exception:
            print('查找图片失败')
            a = traceback.format_exc()
            print(a)
            return 0, 0

    def find_multi_img(self, *img_template_path, part=False, pos1=None, pos2=None, gray=False):
        """
        查找多张图片
            :param img_template_path: 欲查找的图片路径列表
            :param part=0: 是否全屏查找，1为否，其他为是
            :param pos1=None: 欲查找范围的左上角坐标
            :param pos2=None: 欲查找范围的右下角坐标
            :param gray=0: 是否彩色查找，0：查找彩色图片，1：查找黑白图片
            :return: (maxVal,maxLoc) maxVal为相关性列表，越接近1越好，maxLoc为得到的坐标列表
        """
        # 窗口截图
        if part:
            img_src = self.screenshot_part(pos1, pos2,gray=gray)
        else:
            img_src = self.screenshot_window(None, gray=gray)

        # 返回值列表
        maxVal_list = []
        maxLoc_list = []
        best = {}
        for item in img_template_path:
            # 读入文件
            if gray == 0:
                img_template = cv2.imread(item, cv2.IMREAD_COLOR)
            else:
                img_template = cv2.imread(item, cv2.IMREAD_GRAYSCALE)

            # 开始识别
            try:
                res = cv2.matchTemplate(
                    img_src, img_template, cv2.TM_CCOEFF_NORMED)
                minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(res)
                best[item] = maxVal
                maxVal_list.append(maxVal)
                maxLoc_list.append(maxLoc)
            except Exception:
                logging.warning('查找多个图片失败')
                a = traceback.format_exc()
                logging.warning(a)
                maxVal_list.append(0)
                maxLoc_list.append(0)
        # 返回列表
        # print(best)
        return maxVal_list, maxLoc_list

    def activate_window(self):
        user32 = ctypes.WinDLL('user32.dll')
        user32.SwitchToThisWindow(self.hwnd, True)

    def mouse_move(self, pos, pos_end=None):
        """
        模拟鼠标移动
            :param pos: (x,y) 鼠标移动的坐标
            :param pos_end=None: (x,y) 若pos_end不为空，则鼠标移动至以pos为左上角坐标pos_end为右下角坐标的区域内的随机位置
        """
        pos2 = win32gui.ClientToScreen(self.hwnd, pos)
        if pos_end == None:
            win32api.SetCursorPos(pos2)
        else:
            pos_end2 = win32gui.ClientToScreen(self.hwnd, pos_end)
            pos_rand = (random.randint(
                pos2[0], pos_end2[0]), random.randint(pos2[1], pos_end2[1]))
            win32api.SetCursorPos(pos_rand)

    def mouse_click(self):
        """
        鼠标单击
        """
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(random.randint(20, 80)/1000)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def mouse_drag(self, pos1, pos2):
        """
        鼠标拖拽
            :param pos1: (x,y) 起点坐标
            :param pos2: (x,y) 终点坐标
        """
        pos1_s = win32gui.ClientToScreen(self.hwnd, pos1)
        pos2_s = win32gui.ClientToScreen(self.hwnd, pos2)
        screen_x = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_y = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        start_x = pos1_s[0]*65535//screen_x
        start_y = pos1_s[1]*65535//screen_y
        dst_x = pos2_s[0]*65535//screen_x
        dst_y = pos2_s[1]*65535//screen_y
        move_x = np.linspace(start_x, dst_x, num=20, endpoint=True)[0:]
        move_y = np.linspace(start_y, dst_y, num=20, endpoint=True)[0:]
        self.mouse_move(pos1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        for i in range(20):
            x = int(round(move_x[i]))
            y = int(round(move_y[i]))
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE |
                                 win32con.MOUSEEVENTF_ABSOLUTE, x, y, 0, 0)
            time.sleep(0.01)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def mouse_click_bg(self, pos, pos_end=None):
        """
        后台鼠标单击
            :param pos: (x,y) 鼠标单击的坐标
            :param pos_end=None: (x,y) 若pos_end不为空，则鼠标单击以pos为左上角坐标pos_end为右下角坐标的区域内的随机位置
        """
        # if self.debug_enable:
        #     img = self.screenshot_window()
        #     self.img = cv2.rectangle(img, pos, pos_end, (0, 255, 0), 3)

        if pos_end == None:
            pos_rand = pos
        else:
            pos_rand = (random.randint(
                pos[0], pos_end[0]), random.randint(pos[1], pos_end[1]))
            win32gui.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE,
                                 0, win32api.MAKELONG(pos_rand[0], pos_rand[1]))
            win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN,
                                 0, win32api.MAKELONG(pos_rand[0], pos_rand[1]))
            time.sleep(random.randint(20, 80)/1000)
            win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONUP,
                                 0, win32api.MAKELONG(pos_rand[0], pos_rand[1]))

    def mouse_drag_bg(self, pos1, pos2):
        """
        后台鼠标拖拽
            :param pos1: (x,y) 起点坐标
            :param pos2: (x,y) 终点坐标
        """
        move_x = np.linspace(pos1[0], pos2[0], num=20, endpoint=True)[0:]
        move_y = np.linspace(pos1[1], pos2[1], num=20, endpoint=True)[0:]
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN,
                                 0, win32api.MAKELONG(pos1[0], pos1[1]))
        for i in range(20):
            x = int(round(move_x[i]))
            y = int(round(move_y[i]))
            win32gui.SendMessage(
                self.hwnd, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x, y))
            time.sleep(0.01)
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONUP,
                             0, win32api.MAKELONG(pos2[0], pos2[1]))

    def wait_game_img(self, img_path, max_time=100, quit=True):
        """
        等待图像
            :param img_path: 图片路径
            :param max_time=60: 超时时间
            :param quit=True: 超时后是否退出
            :return: 成功返回坐标，失败返回False
        """
        start_time = time.time()
        while time.time()-start_time <= max_time and self.run:
            maxVal, maxLoc = self.find_img(img_path)
            # print("最大相似点"+str(maxVal))
            if maxVal > 0.8:
                return maxLoc
            if max_time > 5:
                time.sleep(1)
            else:
                time.sleep(0.1)
        if quit:
            # 超时则退出游戏
            self.quit_game()
        else:
            return False

    def wait_game_color(self, region, color, tolerance=0, max_time=60, quit=True):
        """
        等待颜色
            :param region: ((x1,y1),(x2,y2)) 欲搜索的区域
            :param color: (r,g,b) 欲等待的颜色
            :param tolerance=0: 容差值
            :param max_time=30: 超时时间
            :param quit=True: 超时后是否退出
            :return: 成功返回True，失败返回False
        """
        start_time = time.time()
        while time.time()-start_time <= max_time and self.run:
            pos = self.find_color(region, color, tolerance)
            if pos != -1:
                return True
            time.sleep(1)
        if quit:
            # 超时则退出游戏
            self.quit_game()
        else:
            return False

    def find_game_img(self, img_path, part=False, pos1=None, pos2=None, gray=False, thread=0.9):
        '''
        查找图片
            :param img_path: 查找路径
            :param part=0: 是否全屏查找，0为否，其他为是
            :param pos1=None: 欲查找范围的左上角坐标
            :param pos2=None: 欲查找范围的右下角坐标
            :param gray=0: 是否查找黑白图片，0：查找彩色图片，1：查找黑白图片
            :param thread=0.9: 自定义阈值
            :return: 查找成功返回位置坐标，否则返回False
        '''
        maxVal, maxLoc = self.find_img(img_path, part, pos1, pos2, gray)
        # print(maxVal)
        if maxVal > thread:
            return maxLoc
        else:
            return False

    def quit_game(self):
        """
        退出游戏
        """
        self.clean_mem()    # 清理内存
        print("退出")
        input()

    def clean_mem(self):
        '''
        清理内存
        '''
        self.srcdc.DeleteDC()
        self.memdc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, self.hwindc)
        win32gui.DeleteObject(self.bmp.GetHandle())

    def debug(self):
        '''
        自检分辨率和点击范围
        '''
        # 开启自检
        self.debug_enable = True

        # 分辨率
        self.img = self.screenshot_window()
        print('游戏分辨率：' + str(self.img.shape))

        while(1):
            # 点击范围标记
            cv2.imshow('Click Area (Press \'q\' to exit)', self.img)

            # 候选图片

            k = cv2.waitKey(1) & 0xFF
            if k == ord('q'):
                break

        cv2.destroyAllWindows()
        self.debug_enable = False

if __name__ == '__main__':
    hwnd = win32gui.FindWindow(0, u'跳一跳')
    game_ctl = GameControl(hwnd)
    game_ctl.debug()