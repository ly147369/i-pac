from collections import deque
from socket import *
from threading import Thread
import math
import numpy as np
import cv2


class PdrMatchMethod(object):
    def __init__(self):
        self.cv_number = 10  # 记录X帧内的动作
        self.cv_queue = deque(maxlen=self.cv_number)  # 临时存放接受到的cv帧们
        self.pdr_cv = dict()  # pdr_id:[(x,y,w,h),color,cv_id]
        get_pdr_thread = Thread(target=PdrMatchMethod.get_pdr, args=(self,))
        get_pdr_thread.start()  # 接收pdr数据
        self.stand_disance = 3  # 多少像素的移动算是不静止
        self.angle_diff = -30  # 角度偏移，根据摄像头的位姿决定
        self.threshold_color = 0.2  # 越高容错率越高

    def get_pdr(self):
        BUFfSIZE = 2048
        ADDRESS = ("", 21567)
        tcpSerSock = socket(AF_INET, SOCK_STREAM)
        tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        tcpSerSock.bind(ADDRESS)
        tcpSerSock.listen(20)
        while 1:
            print('waiting for connection...')
            tcpCliSock, addr = tcpSerSock.accept()
            print('...connected from:', addr)
            while 1:
                data = bytes.decode(tcpCliSock.recv(BUFfSIZE))
                if not data:
                    break
                data_list = data.split(" ")
                if len(data_list) and data_list[0] == "PDR":  # 只接受符合类型的数据
                    data_list[:] = data_list[:0:-1]  # 传输数据问题，倒过来嘻嘻（id,step_length,angle）
                    print(data_list[0])
                    if self.pdr_cv.get(data_list[0], -1) == -1:  # 此条PDR未匹配过
                        self.match_pdr_cv(data_list)  # 就去尝试匹配CV（如果未绑定）
                    else:  # 匹配
                        # 主动更新PDR的位置。
                        self.update_pdr(data_list)
            tcpCliSock.close()

    def get_cv(self, cv_frame_result):
        # 帮助CV确定位置并被动更新PDR位置
        cv_add_frame = self.pdr_help_cv(cv_frame_result)
        # 保存cv帧
        self.cv_queue.append(cv_frame_result)  # ([x, y, w, h], color_hist, id)xN
        return cv_add_frame

    def match_pdr_cv(self, data_list):
        angle_pdr = (float(data_list[2]) + 180 + self.angle_diff + 360) % 360  # 从-180~180%转换到0-360%，再加上偏移
        pdr_id = data_list[0]
        step_length = float(data_list[1])
        stand = 0
        if step_length == 0:  # 没有移动
            stand = 1  # 静止
        match_cv = []
        match_angle = []
        new_cv = self.cv_queue[len(self.cv_queue) - 1]  # 最新的帧信息
        for detection in new_cv:  # 这一大步找出了所有cv的角度
            x1, y1, w1, h1 = detection[0]
            x1 = x1 + w1 / 2
            y1 = y1 + h1 / 2
            id = detection[2]  # id：新cv帧中的一个目标id
            flag = 0
            x2, y2 = 0, 0
            for i in range(len(self.cv_queue) - 1):
                for detection_before in self.cv_queue[i]:
                    if detection_before[2] == id:
                        x2, y2, w2, h2 = detection_before[0]
                        x2 = x2 + w2 / 2
                        y2 = y2 + h2 / 2
                        flag = 1  # 找到了就不找了
                if flag == 1:
                    break
            if flag:
                angle = self.cal_angle(x2, y2, x1, y1)  # 计算角度
                stand_dis = np.sqrt(np.sum(np.square(np.array([x2, y2]) - np.array([x1, y1]))))
                if stand_dis < self.stand_disance:  # 目标cv静止
                    if stand == 1:
                        angle = angle_pdr  # pdr也静止，这样让他们的距离最小
                    if stand == 0:
                        angle = 9999  # pdr不静止，所以不可能匹配cv点
                if angle != 180 + self.angle_diff:
                    print(str(angle) + " " + str(angle_pdr))
                match_cv.append(detection)
                match_angle.append(angle)
        min_distance = 20  # 20度以内的偏差都能接受
        match_detection = -1
        for i in range(len(match_angle)):  # 然后cv角度一个一个跟pdr角度匹配
            distance = np.sqrt(np.sum(np.square(angle_pdr - match_angle[i])))
            if distance < min_distance:
                min_distance = distance
                match_detection = i
        if match_detection is not -1:  # 有cv匹配成功
            self.pdr_cv[pdr_id] = match_cv[match_detection]
            print(pdr_id + ' ' + match_cv[match_detection][2] + "____________")

    # 计算方位角函数
    def cal_angle(self, x1, y1, x2, y2):
        angle = 0.0;
        dx = x2 - x1
        dy = y2 - y1
        if x2 == x1:
            angle = math.pi / 2.0
            if y2 == y1:
                angle = 0.0
            elif y2 < y1:
                angle = 3.0 * math.pi / 2.0
        elif x2 > x1 and y2 > y1:
            angle = math.atan(dx / dy)
        elif x2 > x1 and y2 < y1:
            angle = math.pi / 2 + math.atan(-dy / dx)
        elif x2 < x1 and y2 < y1:
            angle = math.pi + math.atan(dx / dy)
        elif x2 < x1 and y2 > y1:
            angle = 3.0 * math.pi / 2.0 + math.atan(dy / -dx)
        return (angle * 180 / math.pi)

    def pdr_help_cv(self, cv_frame):
        # 1.找PDR已经绑定的CV，有ID且位置相近，正确，更新PDR。
        # 2.压根没有对应cv，或有ID但很远。找最近的几个单位，比较颜色，是则给ID并更新PDR位置。
        # 3.方案2没找到合适的，则直接在PDR位置画框。
        cv_add_frame = []  # 使用这个方法增加的框放进去
        for pdr_id in self.pdr_cv:#绑定的
            (x0, y0, w1, h1), color1, cv_id = self.pdr_cv.get(pdr_id)
            x1 = x0 + w1 // 2
            y1 = y0 + h1 // 2
            cv_flag = 0
            for detection in cv_frame:
                if cv_id == detection[2]:  # pdr绑定的cv出现
                    cv_flag = 1
                    x2, y2, w2, h2 = detection[0]
                    color2 = detection[1]
                    x3 = x2 + w2 // 2
                    y3 = y2 + h2 // 2
                    if self.cal_distance([x1, y1], [x3, y3]) < (w1 + h1):  # 要找的cv很近
                        self.pdr_cv.get(pdr_id)[0] = [x2, y2, w2, h2]
                        self.pdr_cv.get(pdr_id)[1] = color2
                    else:  # 虽然出现了，但是有点远
                        cv_flag2 = 0
                        for detection2 in cv_frame:  # 所有目标，找出近的且颜色很像的
                            x4, y4, w4, h4 = detection2[0]
                            color3 = detection2[1]
                            x5 = x4 + w4 // 2
                            y5 = y4 + h4 // 2
                            if self.cal_distance([x1, y1], [x5, y5]) < (w1 + h1) \
                                    and self.compare_hist(color1, color3) < self.threshold_color:
                                # 找出近的且颜色很像的，给ID并更新PDR位置
                                cv_flag2 = 1
                                self.pdr_cv.get(pdr_id)[0] = [x4, y4, w4, h4]
                                self.pdr_cv.get(pdr_id)[1] = color3
                                detection2[2] = cv_id
                        if cv_flag2 == 0:
                            cv_add_frame.append([[x0, y0, w1, h1], color1, cv_id])
                            print([[x0, y0, w1, h1], cv_id])
            if cv_flag == 0:  # 这帧中没出现pdr的cv
                cv_flag2 = 0
                for detection2 in cv_frame:  # 所有目标，找出近的且颜色很像的
                    x4, y4, w4, h4 = detection2[0]
                    color3 = detection2[1]
                    x5 = x4 + w4 // 2
                    y5 = y4 + h4 // 2
                    if self.cal_distance([x0, y0], [x5, y5]) < (w1 + h1) \
                            and self.compare_hist(color1, color3) < self.threshold_color:
                        # 找出近的且颜色很像的，给ID并更新PDR位置
                        cv_flag2 = 1
                        self.pdr_cv.get(pdr_id)[0] = [x4, y4, w4, h4]
                        self.pdr_cv.get(pdr_id)[1] = color3
                        detection2[2] = cv_id
                if cv_flag2 == 0:  # 距离太远了
                    cv_add_frame.append([[x0, y0, w1, h1], color1, cv_id])
                    print([[x0, y0, w1, h1], cv_id])
        return cv_add_frame

    def compare_hist(self, hist1, hist2):
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)

    def cal_distance(self, loc1, loc2):
        return np.sqrt(np.sum(np.square(np.array(loc1) - np.array(loc2))))

    def update_pdr(self, data_list):
        # 主动更新主要用于长时间被遮挡无法被动更新PDR（静止不更新，移动更新）。
        # 因为没被遮挡的会被目标检测更新掉（如果识别正常）。
        pdr_id = data_list[0]
        move = float(data_list[1])
        step_length = self.pdr_cv.get(pdr_id)[0][2]
        cv_id = self.pdr_cv.get(pdr_id)[2]
        angle_pdr = (float(data_list[2]) + 180 + self.angle_diff + 360) % 360
        direction = math.radians(float(angle_pdr))
        if move == 0:  # PDR没有移动，所以不需要更新
            return
        x = int(math.cos(direction) * step_length)
        y = int(math.sin(direction) * step_length)
        self.pdr_cv.get(pdr_id)[0][0] += x
        self.pdr_cv.get(pdr_id)[0][1] += y
        pass
