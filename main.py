import time
import sys
import numpy as np
import cv2
import win32gui
import json
import configparser
from matplotlib import pyplot as plt
import ctypes
import src.game.game_control as gc
import src.game.game_config as game_conf



class Gamer():
    def __init__(self, hwnd):
        self.gamectl = gc.GameControl(hwnd)
        self.gamePos = game_conf.GamePos()
        self.gameSce = game_conf.GameScene()

    def check_scene(self, name):
        if self.gameSce.get_scene(name):
            maxVallist, maxLoclist = self.gamectl.find_multi_img(self.gameSce.get_scene(name)[:-1],
                                                                 gray=self.gameSce.get_scene(name)[-1])
            if sorted(maxVallist, reverse=True)[0] >= 0.95:
                return True
            else:
                return False
        # TODO 添加错误反馈

    def get_scene(self):
        all_scene = self.gameSce.get_all()
        mps = ""
        mpp = 0

        for scene in all_scene:
            maxVallist, maxLoclist = self.gamectl.find_multi_img(all_scene[scene][:-1],gray=all_scene[scene][-1])
            if sorted(maxVallist, reverse=True)[0] > mpp:
                # print("该页面为{}的可能性为{}".format(scene,sorted(maxVallist, reverse=True)[0]))
                mps = scene
                mpp = sorted(maxVallist, reverse=True)[0]

        return mps


    def index_start(self):
        start_button = self.gamePos.get_pos("start_button")
        self.gamectl.mouse_move(start_button[0],start_button[1])
        self.gamectl.mouse_click()
        time.sleep(3)
        if self.get_scene() != "start_index":
            return True
        else:
            print("页面跳转失败")
            input()
            exit()

    def stabled(self):
        img_src = self.gamectl.screenshot_window(gray=True)
        color = img_src[225][80]
        time.sleep(3)
        img_src = self.gamectl.screenshot_window(gray=True)
        if img_src[225][80] == color:
            return True
        else:
            time.sleep(1)
            return self.stabled()

    def pre_img(self):
        if self.stabled():
            img_src = self.gamectl.screenshot_window(gray=True)
            img_crop = img_src[200:550, 0:450]
            # (0, 200), (450, 550)
            img_list = img_crop.tolist()
            color = img_src[225][80]
            img = np.zeros(img_crop.shape, dtype=np.uint8)
            up = (0, 0)
            found = False
            stage_color = 0
            for h in img_list:
                for w in h:
                    if (img_list.index(h) != 0) and (h.index(w) != 0):
                        if w != color:
                            # print(img_list.index(h),h.index(w))
                            stage_color = h[h.index(w) + 2]
                            up = (img_list.index(h) + 2, h.index(w))
                            found = True
                            break
                if found:
                    break


            last_pos = (0, 0)
            for h in img_list:
                for w in h:
                    if (abs(w - stage_color) <= 2) and (abs(h[h.index(w) + 2]) > 2) and h.index(w) > last_pos[1] + 3:
                        img[img_list.index(h)][h.index(w)] = 255
                        last_pos = (img_list.index(h), h.index(w))

            right = last_pos
            right = (right[1],right[0]+200)
            up = (up[1],up[0]+200)
            stage_point = (int((right[0] + up[0]) / 2),int((right[1] + up[1]) / 2))
            return stage_point

            # cv2.namedWindow("image")
            # cv2.imshow("image", img)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
        # cv2.imshow("contours", img_src)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # binary,contours, hierarchy = cv2.findContours(img_src,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        # # 创建白色幕布
        # temp = np.ones(img_src.shape, np.uint8) * 255
        # # 画出轮廓：temp是白色幕布，contours是轮廓，-1表示全画，然后是颜色，厚度
        # cv2.drawContours(temp, contours, -1, (0, 255, 0), 3)
        #
        # cv2.imshow("contours", temp)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    def play(self):
        maxLoc = self.gamectl.find_game_img("img/player.png",gray=True,thread=0.75)
        if maxLoc:
            player_pos = (maxLoc[0]+15, maxLoc[1]+80)
            stage_point = self.pre_img()
            distance = (((stage_point[0] - player_pos[0]) ** 2 + (stage_point[1] - player_pos[1]) ** 2) ** 0.5)
            jump_pad = self.gamePos.get_pos("jump_tap")
            self.gamectl.mouse_move(jump_pad[0],jump_pad[1])
            self.gamectl.mouse_hold(distance*0.00275)
        else:
            jump_pad = self.gamePos.get_pos("jump_tap")
            self.gamectl.mouse_move(jump_pad[0], jump_pad[1])
            self.gamectl.mouse_hold(0.01)
        time.sleep(1)


    def over_page(self):
        retry_button = self.gamePos.get_pos("retry")
        self.gamectl.mouse_move(retry_button[0], retry_button[1])
        self.gamectl.mouse_click()
        time.sleep(3)
        if self.get_scene() != "over_page":
            return True
        else:
            self.over_page()

    def start(self):
        while True:
            current_scene = self.get_scene()
            print("当前场景: {}".format(current_scene))
            if current_scene == 'start_index':
                self.index_start()
            elif current_scene == 'play_page':
                self.play()
            elif current_scene == 'over_page':
                self.over_page()




def is_admin():
    # UAC申请，获得管理员权限
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if __name__ == '__main__':
    # if is_admin():
    #     pass
    # else:
    #     ctypes.windll.shell32.ShellExecuteW(
    #         None, "runas", sys.executable, __file__, None, 1)
    hwnd = win32gui.FindWindow(0, u'跳一跳')
    game = Gamer(hwnd)
    game.start()