from collections import deque

import cv2
import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment
import copy

class BackDiffMethod(object):
    def __init__(self, current_image):
        self.background_image = current_image  # 计算的背景图片
        self.background_need_num = 60  # 计算背景的滑动窗口大小
        self.background_queue = deque(maxlen=self.background_need_num)  # 计算背景的队列（滑动窗口）
        self.skip_frame = 40  # 每间隔多少帧计算一次背景&&加入滑动窗口一帧
        self.skip_frame_now = 0  # 目前跳过多少帧了
        self.current_image = current_image  # 当前帧
        self.image_height = current_image.shape[0]  # 当前帧的宽
        self.image_width = current_image.shape[1]  # 当前帧的高
        print(self.image_height,self.image_width)
        self.threshold_level = 20  # 差分的阈值，越大越严格
        self.erosion_kernel = np.ones((2, 2), np.uint8)  # 腐蚀卷积核
        self.dilation_kernel = np.ones((6, 6), np.uint8)  # 膨胀卷积核
        self.min_area = self.image_height * self.image_width / 200  # 消去场景中噪音
        self.backage_need_number = 20  # 目标匹配使用的滑动窗口
        self.backage_queue = deque(maxlen=self.backage_need_number)  # 目标匹配使用的滑动队列（放前几帧的目标）
        self.threshold_color = 0.2  # 越高容错率越高

    def cal_background_image(self):
        self.skip_frame_now += 1
        # 计算背景时跳过几帧的思想是：1.连续帧差别不明显，具有时间差的帧对背景贡献大 2.减少运算量
        if self.skip_frame_now == self.skip_frame:
            self.skip_frame_now = 0
            background_image = np.zeros((self.image_height, self.image_width, 3), np.float32)
            self.background_queue.append(self.current_image)
            queue_size = len(self.background_queue)
            for i in self.background_queue:
                background_image += i
            background_image /= queue_size
            self.background_image = background_image.astype(np.uint8)

    def cal_positions(self, current_image):
        self.current_image = current_image
        # 计算非背景的前景图片
        background_grey = cv2.cvtColor(self.background_image, cv2.COLOR_BGR2GRAY)
        image_grey = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)
        front_image = cv2.absdiff(background_grey, image_grey)
        threshold_image = np.full((self.image_height, self.image_width), self.threshold_level)
        front_image = np.array(front_image < threshold_image, dtype=np.int8) * 255
        front_image = np.fmax(np.array(front_image), image_grey)
        front_image = cv2.cvtColor(np.asarray(Image.fromarray(front_image).convert('RGB')), cv2.COLOR_RGB2BGR)
        cv2.imshow("front",front_image)
        cv2.waitKey(1)
        # 腐蚀+膨胀
        image = cv2.cvtColor(front_image, cv2.COLOR_BGR2GRAY)
        ret, image = cv2.threshold(image, 127, 255, 0)
        cv2.bitwise_not(image, image)
        erosion_dilation_image = np.array(cv2.dilate(cv2.erode(image, self.erosion_kernel), self.dilation_kernel))
        cv2.imshow("erosion_dilation_image",erosion_dilation_image)
        cv2.waitKey(1)
        # 计算坐标+宽高
        image_copy=copy.copy(current_image)
        cv_location = []
        contours, hierarchy = cv2.findContours(erosion_dilation_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(image_copy,contours,-1,(0,255,0),3)
        cv2.imshow("contours",image_copy)
        cv2.waitKey(1)
        for i in range(0, len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            if w * h < self.min_area:
                continue
            cv_loc = (x, y, w, h)
            cv_location.append(cv_loc)
        return cv_location

    def cal_color(self, loc):
        image_rec = self.current_image[loc[1]:loc[1] + loc[3], loc[0]:loc[0] + loc[2]]  # 进行计算的区域
        image_grey = cv2.cvtColor(image_rec, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([image_grey], [0], None, [40], [0, 256])  # 分10个粒度计算颜色直方图
        hist = cv2.normalize(hist, cv2.NORM_L1)  # 归一化，方便比较
        return hist

    def cal_match(self, now_detections):
        # 选举当前目标在前几帧是哪个目标(目标匹配)
        # 选取匹配成功次数最多的目标（已实现）
        now_num = len(now_detections)
        most_list = []  # 统计与前几帧匹配到的目标，分别匹配成功的次数
        for i in range(now_num):
            most_list.append([])  # 初始化list(counter)
        for before_detections in self.backage_queue:
            before_num = len(before_detections)
            cost_matrix = np.zeros(shape=(now_num, before_num))  # 当前帧与前帧的代价矩阵
            for i in range(now_num):
                for j in range(before_num):
                    cost_matrix[i][j] = cv2.compareHist(now_detections[i][1], before_detections[j][1],
                                                        cv2.HISTCMP_BHATTACHARYYA)
            # 代价为颜色特征匹配（未加入距离匹配）
            row, col = linear_sum_assignment(cost_matrix)  # 求解矩阵
            match_num = len(row)
            for i in range(match_num):  # 如果真的成功（可能被迫分配）
                match_degree = cv2.compareHist(now_detections[row[i]][1], before_detections[col[i]][1],
                                               cv2.HISTCMP_BHATTACHARYYA)
                if match_degree <= self.threshold_color:
                    most_list[row[i]].append(before_detections[col[i]][2])

        # 分配矩阵2，当前帧目标vs编号，cost=次数
        for i in range(now_num):
            if len(most_list[i]) != 0:
                now_detections[i][2] = max(most_list[i], key=most_list[i].count)

    def add_backage_queue(self, detections):
        # 当前帧进入目标匹配滑动窗口的队列
        self.backage_queue.append(detections)
