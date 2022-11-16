import cv2
from see_through_wall.back_diff_method import BackDiffMethod
from see_through_wall.pdr_match_method import PdrMatchMethod
import random
import copy
from time import time
color_blue = (255, 245, 0)

def main():
    # video_dir = "../data/chang2_ok.avi"
    # fps = 25
    # img_size = (480, 270)
    #fourcc = cv2.VideoWriter_fourcc(*'XVID')  # opencv3.0
    #videoWriter = cv2.VideoWriter(video_dir, fourcc, fps, img_size)
    # video = cv2.VideoCapture("rtsp://admin:a1234567@192.168.34.119:554/Streaming/Channels/301?transportmode=unicast")
    video = cv2.VideoCapture("../data/video2.mp4")
    ok, frame = video.read()
    print(int(frame.shape[1] / 4), int(frame.shape[0] / 4))
    if not ok:
        return
    frame = cv2.resize(frame, (int(frame.shape[1] / 4), int(frame.shape[0] / 4)), interpolation=cv2.INTER_AREA)
    back_diff = BackDiffMethod(frame)
    # 以上完成初始化，创建背景差分法的对象
    pdr_matcher = PdrMatchMethod()
    # pdr匹配类
    while True:
        a = time()
        ok, frame = video.read()

        if ok:
            now_detections = []  # 目前帧检测到的目标们
            frame = cv2.resize(frame, (int(frame.shape[1] / 4), int(frame.shape[0] / 4)), interpolation=cv2.INTER_AREA)
            frame_copy = copy.copy(frame)  # 用来画图展示，保护原图
            # cv2.imshow("detect_o", frame)
            # wait_char = cv2.waitKey(1)
            locations = back_diff.cal_positions(frame)  # 计算这一帧的目标们
            #back_diff.cal_background_image()  # 更新背景
            for (x, y, w, h) in locations:
                hist = back_diff.cal_color((x, y, w, h))  # 计算目标的颜色特征
                random_str = str(random.randint(0, 999))  # 目标的ID（随机）
                now_detections.append([[x, y, w, h], hist, random_str])  # 保存目标们
            back_diff.cal_match(now_detections)  # 计算当前帧的目标们在前几帧是哪些目标，即：目标追踪
            back_diff.add_backage_queue(now_detections)  # 保存当前帧用于目标追踪
            cv_add_frame = pdr_matcher.get_cv(now_detections)  # ID二次确定后
            for detection in now_detections:  # 绘图原本存在的
                (x, y, w, h) = detection[0]
                cv2.rectangle(frame_copy, (x, y), (x + w, y + h),color_blue, 2)
                #cv2.putText(frame_copy, detection[2], (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            for detection2 in cv_add_frame:  # 绘图PDR推测的
                (x, y, w, h) = detection2[0]
                cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 0, 255), 1)
                cv2.putText(frame_copy, detection2[2], (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            #videoWriter.write(frame_copy)
            cv2.imshow("detect", frame_copy)
            wait_char = cv2.waitKey(30)
            if wait_char == 27:
                break
            if wait_char == 112:
                cv2.waitKey(0)
            b = time()
            # print(b - a)  # 计算时间，若时间大于帧周期，则会造成延迟。
        else:
            break
    print("finish")




main()
