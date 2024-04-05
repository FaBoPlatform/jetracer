
#BOARD_NAME = GPIO.gpio_pin_data.get_data()[0]

mode_descriptions = {
    "JETSON_NX": ["15W_2CORE", "15W_4CORE", "15W_6CORE", "10W_2CORE", "10W_4CORE"],
    "JETSON_XAVIER": ["MAXN", "MODE_10W", "MODE_15W", "MODE_30W"],
    "JETSON_NANO": ["MAXN", "5W"],
    "JETSON_ORIN": ["MAXN", "MODE_15W", "MODE_30W", "MODE_40W"],
    "JETSON_ORIN_NANO": ["MODE_15W", "MODE_7W"]
}

product_names = {
    "JETSON_NX": "Jetson Xavier NX",
    "JETSON_XAVIER": "Jetson AGX Xavier",
    "JETSON_NANO": "Jetson Nano",
    "JETSON_ORIN": "Jetson AGX Orin",
    "JETSON_ORIN_NANO": "Jetson Orin Nano"
}

# ボードごとのI2Cバス番号と初期Powerモードを定義する
board_settings = {
    "JETSON_NX": (8, 3),
    "JETSON_XAVIER": (8, 2),
    "JETSON_NANO": (1, 0),
    "JETSON_ORIN": (7, 0),
    "JETSON_ORIN_NANO": (7, 0)
}
BOARD_NAME = "JETSON_ORIN_NANO"
i2c_busnum, power_mode = board_settings.get(BOARD_NAME, (None, None))
mode_description = mode_descriptions.get(BOARD_NAME, [])
product_name = product_names.get(BOARD_NAME, "未知のボード")

if power_mode is not None and power_mode < len(mode_description):
    mode_str = mode_description[power_mode]
    print("------------------------------------------------------------")
    print(f"{product_name}を認識: I2Cバス番号: {i2c_busnum}, Powerモード: {mode_str}({power_mode})に設定します。")
    print("------------------------------------------------------------")
else:
    print("未知のボードまたは不正なモードです。")
    
import os
import glob
import traceback

process_no = 0
DEBUG = False
def write_log(msg):
    global process_widget, process_no
    process_no = process_no + 1
    log_message = f"{process_no}: {msg}\n"    
    # ログファイルに書き込む
    if DEBUG:
        with open("/home/jetson/data/notebooks/logfile.log", "a") as log_file:
            log_file.write(log_message)
            print(log_message)

print("PCA9685の初期化")

import Fabo_PCA9685
import time
import pkg_resources
import smbus
import time
import json

try:
    SMBUS='smbus'
    BUSNUM=i2c_busnum
    SERVO_HZ=60
    INITIAL_VALUE=300
    bus = smbus.SMBus(BUSNUM)
    PCA9685 = Fabo_PCA9685.PCA9685(bus,INITIAL_VALUE,address=0x40)
    PCA9685.set_hz(SERVO_HZ)
except Exception as e:
    print(f"Error:{e}")

STEERING_CH = 0
THROTTLE_CH = 1
direction = 0
REVERSE = 0
NORMAL = 1

pwm_front = 0
pwm_back = 0

print("PWM Paramsの取得と反映")

with open('/home/jetson/data/notebooks/pwm_params.json') as f:
    json_str = json.load(f)
    
    pwm_stop = json_str["pwm_speed"]["stop"]
    pwm_front = json_str["pwm_speed"]["front"]
    pwm_back = json_str["pwm_speed"]["back"]
    pwm_left = json_str["pwm_steering"]["left"]
    pwm_center = json_str["pwm_steering"]["center"]
    pwm_right = json_str["pwm_steering"]["right"]

    
if pwm_front >= pwm_back:
    direction = REVERSE
else:
    direction = NORMAL

    
print("PWM初期値の設定")
PCA9685.set_channel_value(STEERING_CH, pwm_center)
PCA9685.set_channel_value(THROTTLE_CH, pwm_stop)

CAM0_FPS=60
CAM1_FPS=60

from jetcam.csi_camera import CSICamera

def open_camera():
    global cam0, cam1
    try:
        cam0 = CSICamera(capture_device=0,width=224, height=224, capture_fps=CAM0_FPS)
    except Exception as e:
        # スタックトレースを含むエラーメッセージを取得
        #error_message = f"Error open_camera:{e}\n{''.join(traceback.format_exception(None, e, e.__traceback__))}"
        write_log("Error:open_camera:cam0")
    try:
        cam1 = CSICamera(capture_device=1,width=224, height=224, capture_fps=CAM1_FPS)
    except Exception as e:
        # スタックトレースを含むエラーメッセージを取得
        #error_message = f"Error open_camera:{e}\n{''.join(traceback.format_exception(None, e, e.__traceback__))}"
        write_log("Error:open_camera:cam0")        
        
CATEGORIES = ["mall","diner","bank","school","hotel","supermarket","hospital","campus","etc"]

def get_target(target):
    prebuilding = ""
    if target == "mall":
        prebuilding = "school"
    elif target == "diner":
        prebuilding = "mall"
    elif target == "bank":
        prebuilding = "hospital"
    elif target == "school":
        prebuilding = "campus"
    elif target == "hotel":
        prebuilding = "supermarket"
    elif target == "supermarket":
        prebuilding = "mall"
    elif target == "hospital":
        prebuilding = "supermarket"
    elif target == "campus":
        prebuilding = "diner"
    
    return prebuilding

def init_led():
    global i2c_busnum,i2c
    i2c = smbus.SMBus(i2c_busnum)
    
def change_color(color):
    global i2c
    colors = {
        'normal': 0x10,
        'red':    0x1a,
        'blue':   0x1b,
        'yellow': 0x1c,
        'green':  0x1d,
        'white':  0x1e,
        'orange': 0x1f,
        'purple': 0x20,
        'lime':   0x21,
        'pink':   0x22,
        'off':    0x30,
        'error1':    0x40,
        'error2':    0x41,
        'error3':    0x42, # red, red, white
        'error4':    0x43, # red, white, red
    }
    if color in colors:
        i2c.read_i2c_block_data(0x08, colors[color])
    else:
        print(f"Error change_color: '{color}' is not a valid color.")

print("LEDの初期化")
init_led()
change_color("green")

print("各種import:threading")
import threading
print("各種import:torch")
import torch
print("各種import:preprocess")
from utils import preprocess
print("各種import:subprocess")
import subprocess
print("各種import:cv2")
import cv2
print("各種import:time")
import time
print("各種import:TRTModule")
from torch2trt import TRTModule
print("各種import:subprocess")
import subprocess
print("各種import:datetime")
import datetime
print("各種import:torch.nn.functional")
import torch.nn.functional as F
print("import終了")

record = False
running = False
load = False
speed_ai_flag = False
running_cam0 = False
running_cam1 = False

def map_rc(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def handle(x):
    global pwm_right,pwm_left,STEERING_CH,PCA9685
    x = map_rc(x, 224, 0, pwm_right, pwm_left)
    PCA9685.set_channel_value(STEERING_CH, x)
    
def throttle(speed):
    global pwm_front,pwm_back,THROTTLE_CH,PCA9685, low_gain
    speed = map_rc(speed, 224, 0, pwm_front, pwm_stop)
    #speed = map_rc(speed, 224, 0, pwm_front, pwm_stop + speed_low_gain_slider.value)
    PCA9685.set_channel_value(THROTTLE_CH, speed)

IMG_WIDTH=224

def get_model(status, target):
    if target == "campus" or target == "mall" or target == "diner" or target == "school":
        if status == STATUS_OUT_A:
            name = "model_a"
            return name,model_a_trt
        elif status == STATUS_OUT_B:
            name = "model_b"
            return name,model_b_trt
        elif status == STATUS_IN:
            name = "model_d"
            return name,model_d_trt
        else:
            name = "model_d"
            return name,model_d_trt 
    else:
        if status == STATUS_OUT_A:
            name = "model_a"
            return name,model_a_trt
        elif status == STATUS_OUT_B:
            name = "model_a"
            return name,model_a_trt
        elif status == STATUS_IN:
            name = "model_c"
            return name,model_c_trt
        else:
            name = "model_c"
            return name,model_c_trt 

print("LoRa Status設定")

# LoRaモジュールのステータス定義
LORA_STATUS_IDLE = 0
LORA_STATUS_DRIVING = 1
LORA_STATUS_BUILDING_DETECTED = 2
LORA_STATUS_ARRIVED = 3  # スペルミスの修正: ARIVED -> ARRIVED
LORA_STATUS_GO_BACK_HOME = 4

def send_data(send_address, send_ch, data):
    global ser
    data_size = len(data)
    message = bytearray(data_size + 4)  # plus 4 for address and ch, plus 1 for delimiter
    message[0] = (send_address >> 8) & 0xFF  # high byte of send_address
    message[1] = send_address & 0xFF  # low byte of send_address
    message[2] = send_ch
    message[3:data_size+3] = data.encode('utf-8')  # assuming data is a str object
    # add delimiter
    message[data_size+3] = ord('\n')
    # Write message
    ser.write(message)
    # Wait for data to become available
    timeout = time.time() + 1  # 1 second timeout
    while ser.in_waiting <= 0 and time.time() < timeout:
        time.sleep(0.01)  # Wait a bit for data to arrive

    # Read response (adjust the size of the read as needed)
    ser.flush()
    if ser.in_waiting > 0:
        response = ser.read(1)
        return response[0]
    else:
        print("No response received.")
        return None

def thread_send_data(send_address, send_ch, data):
    global ser  
    response = send_data(send_address, send_ch, data) 
    if response is not None:
        write_log(f"Response received: {response}")
    else:
        write_log("No response or an error occurred.")

def lora_send_status(car_id, car_status):
    lora_address = 0x0c
    lora_ch = 1
    lora_msg = f"{car_id},{car_status}"
    write_log(f"Sending LoRa message to {lora_address},{lora_msg}")
    send_thread = threading.Thread(target=thread_send_data, args=(lora_address, lora_ch, lora_msg))
    send_thread.start()
    write_log("LoRa send thread started successfully.")
    
status = 0

def live_cam0():
    """
    カメラ0(フロントカメラ)からの映像を使用して走行制御を行う関数。
    大回り直進、大回り右折、小回り直進、小回り右折の4つのモデルから選べらたモデルを用いて
    ステアリング操作（handle関数呼び出し）とスロットル制御（throttle関数呼び出し）を行います。
    
    カメラ映像の記録を行う機能も備えています。
    """
    global car_id, mode,cam0,target,speed_ai_flag,running_cam0,cam0,IMG_WIDTH,record,selected_model,model_a_trt,preprocess,pwm_stop,save_dir0,save_dir1,num,count_cam0,fps_type,FPS_30, status
    
    try:
        count_cam0 = 1
        num = 1
        frame_count = 0
        # 処理開始時間
        start_time = time.time()
        # 走行用推論実行時間
        process_drive_time = 0
        # 走行用推論実行時間(総計)
        total_process_drive_time = 0
        
        selected_model = model_a_trt

        stop_count = 30
        
        speed = 0
        
        if mode == MODE_RUN:
            status = STATUS_OUT_A
        elif mode == MODE_BACK:
            status = STATUS_BACK
            
            
    except Exception as e:
        write_log(f"Error live_cam0 init:{e}")

    while running_cam0:
        try:
            # カメラ画像を読込
            img0 = cam0.read()
            if record == True:
                remarked_img0 = img0.copy()
            process_drive_time = time.time()
            img0 = preprocess(img0).half()
            
            
            # 走行用の推論を実行
            output = selected_model(img0).detach().cpu().numpy().flatten()
            x = float(output[0])
            y = float(output[1])
            x = int(IMG_WIDTH * (x / 2.0 + 0.5))
            y = int(IMG_WIDTH * (y / 2.0 + 0.5))
            handle(x)
            """
            modeは、LoRaで受信したデータが1〜8の場合はMODE_RUN, 0の場合はMODE_BACK
            livecam1の認識で、STATUSが変化していく。
            通常モードは、STATUS_OUT_A -> STATUS_OUT_B -> STATUS_IN -> STATUS_TARGET -> STATUS_ARRIVE
            帰宅モードは、STATUS_BACK->STATUS_BACK_PARKING->STATUS_BACK_ARRIVE
            """
            if mode == MODE_RUN:
                # スピードを設定(statusによって速度を変える)
                if status == STATUS_OUT_A or status == STATUS_OUT_B:
                    speed = SPEED_FAST
                    throttle(speed)
                elif status == STATUS_IN:
                    speed = SPEED_SLOW
                    throttle(speed)
                elif status == STATUS_TARGET:
                    speed = SPEED_SLOW
                    throttle(speed)
                elif status == STATUS_ARRIVE:
                    PCA9685.set_channel_value(THROTTLE_CH, pwm_stop)
                    speed = 0
                    write_log("到着 LoRa送信")
                    lora_send_status(car_id, LORA_STATUS_ARRIVED)
                    write_log("到着 Stop呼び出し")
                    stop(None)
                    
                    
                model_name, selected_model = get_model(status, target)
            elif mode == MODE_BACK:
                if status == STATUS_BACK:
                    change_color("pink")
                    selected_model = model_a_trt
                    speed = SPEED_FAST
                    throttle(speed)
                elif status == STATUS_BACK_PARKING:
                    selected_model = model_e_trt
                    speed = SPEED_SLOW
                    throttle(speed)
                elif status == STATUS_BACK_ARRIVE:
                    PCA9685.set_channel_value(THROTTLE_CH, pwm_stop)
                    speed = 0
                    change_color("orange")
                                        
                    #lora_address = 0x0c
                    #lora_ch = 1
                    #LORA_MSG_BACK = 2
                    #lora_msg = f"[{car_id}],{LORA_MSG_BACK}]"
                    #response = send_data(lora_address, lora_ch, lora_msg)
                    #write_log("Send lora")
                    stop(None)
                    lora_send_status(car_id, LORA_STATUS_IDLE)
            
            # 走行用の推論実行時間を計測
            total_process_drive_time += time.time() - process_drive_time
            
            # 現在の時間を取得
            current_time = time.time()
            
            # 走行のカメラ画像を保存
            if record == True:
                name = "0_0_{:0=5}.jpg".format(count_cam0)
                image_path0 = os.path.join(save_dir0, name)
                cv2.imwrite(image_path0, remarked_img0)

            # カウンターを増加
            count_cam0 += 1
            # フレーム用のカウンターを増加
            frame_count += 1
            

            # 走行時の処理時間計測
            if time.time() - start_time > 3.0:
                fps = frame_count / 3.0
                speed_type = ""
                
                write_log(f"Cam0(走行用) FPS: {fps:.1f}, Speed: {speed:.1f} {speed_type}, Steering Gain: {1.0},  走行推論: {total_process_drive_time/(fps*3)*1000:.1f}ms ")
                frame_count = 0
                start_time = time.time() 
                total_process_drive_time = 0
            
        except Exception as e:
            # スタックトレースを含むエラーメッセージを取得
            change_color("error1")
            error_message = f"Error live_cam0:{e}\n{''.join(traceback.format_exception(None, e, e.__traceback__))}"
            write_log(error_message)
            
    if record == True:
        write_log(f"画像を{count_cam0}枚の走行データを保存しました。")
        
print("Camera Status設定")
   
STATUS_WAIT = 99
STATUS_IN = 1
STATUS_OUT_A = 2
STATUS_OUT_B = 3
STATUS_TARGET = 4
STATUS_ARRIVE = 5
STATUS_BACK_WAIT = 6
STATUS_BACK = 7
STATUS_BACK_PARKING = 8
STATUS_BACK_TARGET = 9
STATUS_BACK_ARRIVE = 10

MODE_RUN = 1
MODE_BACK = 2
MODE_WAIT = 3

mode = MODE_RUN

last_detect_time = 0  # 最後に検出があった時刻（秒）

def check_non_detection_period(elapsed_time_ms):
    """
    特定の期間内にイベントが検出されていないかどうかをチェックする。
    elapsed_time_msはミリ秒単位で指定する。

    Args:
        elapsed_time_ms (int): 検出がないと判断する期間（ミリ秒）

    Returns:
        bool: 指定された非検出期間を超えていればTrue、そうでなければFalse
    """
    global last_detect_time
    current_time = time.time()  # 現在時刻を取得（秒）
    
    if last_detect_time == 0:  # 初期状態の場合
        last_detect_time = current_time  # 最初の検出時刻を設定

    period_time_ms = (current_time - last_detect_time) * 1000  # 経過時間をミリ秒に変換
    
    if period_time_ms > elapsed_time_ms:
        return True  # 指定された非検出期間を超えている
    else:
        return False  # 指定された非検出期間を超えていない

def update_last_detect_time():
    """
    イベント検出時に最後の検出時刻を現在時刻に更新する。
    """
    global last_detect_time
    last_detect_time = time.time()  # 現在時刻を更新（秒）
    
def get_stop_time(target):
    if target == CATEGORIES[0]:
        return CAT0_STOP_TIME
    elif target == CATEGORIES[1]:
        return CAT1_STOP_TIME
    elif target == CATEGORIES[2]:
        return CAT2_STOP_TIME
    elif target == CATEGORIES[3]:
        return CAT3_STOP_TIME
    elif target == CATEGORIES[4]:
        return CAT4_STOP_TIME
    elif target == CATEGORIES[5]:
        return CAT5_STOP_TIME
    elif target == CATEGORIES[6]:
        return CAT6_STOP_TIME
    elif target == CATEGORIES[7]:
        return CAT7_STOP_TIME
    else:
        return 2000
    
def check_stop_time(current_time, target_detected_time, stop_time_ms):
    # target_detected_time および current_time は秒単位であるため、
    # ミリ秒単位での停止時間を判断するには、秒単位の差をミリ秒単位に変換する
    elapsed_time_ms = (current_time - target_detected_time) * 1000
    if elapsed_time_ms >= stop_time_ms:
        return True
    else:
        return False

def update_status_and_action(current_status, category_index, last_detect, detect_count, prebuilding, target, stop_time, target_detected_time=None):
    """
    現在の状態に基づき、次のアクションを決定し、状態を更新します。ターゲット発見後、指定された秒数でSTOPに遷移します。

    Args:
        current_status (int): 現在の状態
        category_index (int): 現在の認識結果のカテゴリインデックス
        last_detect (int): 前回の認識結果のカテゴリインデックス
        detect_count (int): 連続して認識された回数
        prebuilding (str): ターゲットの1つ前の建物名
        target (str): ターゲットとなる建物名
        stop_time (int): ターゲットを検出してから停止するまでの秒数
        target_detected_time (float, optional): ターゲットを最初に検出した時刻

    Returns:
        tuple: 更新された状態、連続認識回数、ターゲット検出時刻
    """
    global selected_model, car_id
    new_status = current_status
    new_detect_count = detect_count
    current_time = time.time()  # 現在時刻を取得

    # STATUS_TARGETに遷移した直後にタイムスタンプを記録
    if current_status == STATUS_TARGET and target_detected_time is None:
        target_detected_time = current_time

    # STATUS_TARGET状態で、指定された秒数が経過した場合にSTATUS_ARRIVEに遷移
    if current_status == STATUS_TARGET:
        if check_stop_time(current_time, target_detected_time, stop_time):
            change_color("orange")
            new_status = STATUS_ARRIVE
            PCA9685.set_channel_value(THROTTLE_CH, pwm_stop)    
            target_detected_time = None  # タイムスタンプをリセット
            write_log("STOP!")
            

    if current_status == STATUS_OUT_A:
        if check_non_detection_period(5000) == True:
            # DEBUG
            #write_log(f"new_status:{STATUS_ARRIVE}")
            #change_color("orange")
            #new_status = STATUS_ARRIVE
            
            if CATEGORIES[category_index] == target:
                if CATEGORIES[last_detect] == target:
                    new_detect_count += 1
                    if new_detect_count > 10:
                        write_log(f"Detect1 {target}")
                        change_color("yellow")
                        lora_send_status(car_id, LORA_STATUS_BUILDING_DETECTED)
                        new_status = STATUS_OUT_B
                        new_detect_count = 0
                        update_last_detect_time()

                else:
                    new_detect_count = 1
    elif current_status == STATUS_OUT_B:
        if check_non_detection_period(3000) == True:
            if CATEGORIES[category_index] == prebuilding:
                if CATEGORIES[last_detect] == prebuilding:
                    new_detect_count += 1
                    if new_detect_count > 5:
                        write_log(f"Detect2 {prebuilding}")
                        change_color("purple")
                        new_status = STATUS_IN
                        new_detect_count = 0
                else:
                    new_detect_count = 1
    elif current_status == STATUS_IN:
        if CATEGORIES[category_index] == target:
            if CATEGORIES[last_detect] == target:
                new_detect_count += 1
                if new_detect_count > 5:
                    change_color("orange")
                    write_log(f"Detect3 {target}")
                    new_status = STATUS_TARGET
                    new_detect_count = 0
            else:
                new_detect_count = 1
    
    return new_status, new_detect_count, target_detected_time

def update_status_and_action_back(current_status, category_index, last_detect, detect_count, prebuilding, target, stop_time, target_detected_time=None):
    """
    現在の状態に基づき、次のアクションを決定し、状態を更新します。ターゲット発見後、指定された秒数でSTOPに遷移します。

    Args:
        current_status (int): 現在の状態
        category_index (int): 現在の認識結果のカテゴリインデックス
        last_detect (int): 前回の認識結果のカテゴリインデックス
        detect_count (int): 連続して認識された回数
        prebuilding (str): ターゲットの1つ前の建物名
        target (str): ターゲットとなる建物名
        stop_time (int): ターゲットを検出してから停止するまでの秒数
        target_detected_time (float, optional): ターゲットを最初に検出した時刻

    Returns:
        tuple: 更新された状態、連続認識回数、ターゲット検出時刻
    """
    new_status = current_status
    new_detect_count = detect_count
    current_time = time.time()  # 現在時刻を取得

    # STATUS_BACK_TARGETに遷移した直後にタイムスタンプを記録
    if current_status == STATUS_BACK_TARGET and target_detected_time is None:
        target_detected_time = current_time

    # STATUS_BACK_TARGET状態で、指定された秒数が経過した場合にSTATUS_BACK_ARRIVEに遷移
    if current_status == STATUS_BACK_TARGET:
        if check_stop_time(current_time, target_detected_time, stop_time):
            change_color("orange")
            new_status = STATUS_BACK_ARRIVE
            PCA9685.set_channel_value(THROTTLE_CH, pwm_stop)    
            target_detected_time = None  # タイムスタンプをリセット
            write_log("STOP!")
            
    if current_status == STATUS_BACK:
        if check_non_detection_period(3000) == True:
            if CATEGORIES[category_index] == prebuilding:
                if CATEGORIES[last_detect] == prebuilding:
                    write_log("find_target")
                    new_detect_count += 1
                    if new_detect_count > 10:
                        change_color("yellow")
                        new_status = STATUS_BACK_PARKING
                        new_detect_count = 0
                        update_last_detect_time()

                else:
                    new_detect_count = 1
    elif current_status == STATUS_BACK_PARKING:
        if CATEGORIES[category_index] == target:
            if CATEGORIES[last_detect] == target:
                new_detect_count += 1
                if new_detect_count > 5:
                    change_color("orange")
                    write_log(f"Detect3 {target}")
                    new_status = STATUS_BACK_TARGET
                    new_detect_count = 0
            else:
                new_detect_count = 1
    
    return new_status, new_detect_count, target_detected_time

def live_cam1():
    """
    カメラ1(サイドカメラ)からの映像を使用して環境認識を行う関数。
    クラス分類して認識した結果から現在の状態を変えていく
    """
    global last_detect_time,mode,target, cam1, speed_ai_flag,running_cam1,cam1,IMG_WIDTH,record,model_a_trt,model_b_trt,model_c_trt,model_d_trt,model_e_trt,model_class_trt,preprocess,pwm_stop,save_dir0,save_dir1,num,count_cam1,fps_type,FPS_30,status
    
    try:
        # 現在の環境情報の認識(live_cam0とも共有する)
        if mode == MODE_RUN:
            status = STATUS_OUT_A
            last_detect_time = 0
        elif mode == MODE_BACK:
            status = STATUS_BACK
            last_detect_time = 0
            
        # 認識回数
        detect_count = 0    
        # 環境情報の認識時間計測
        total_process_detect_time = 0
        # カウンター
        count_cam1 = 1
        # フレーム用カウンター
        frame_count = 0
        start_time = time.time()
        last_detect = 0
        
        init_led()
        change_color("pink")
        
        # 停止するまでのカウント
        stop_time = get_stop_time(target)
        
        target_detected_time = None
    except Exception as e:
        write_log(f"Error live_cam1 init:{e}")


    while running_cam1:
        try:
            # サイドカメラ画像の読込
            img1 = cam1.read()
            if record == True:
                remarked_img1 = img1.copy()
            
            # 環境情報の認識開始時間
            process_detect_time = time.time()
            # 横画像の画像認識は model_class_trtを使用します。
            img1 = preprocess(img1).half()
            output = model_class_trt(img1).detach()
            output = F.softmax(output, dim=1).cpu().numpy().flatten()
            category_index = output.argmax()
            # 環境情報の認識時間
            total_process_detect_time += time.time() - process_detect_time 
            
            # 現在の時間を取得
            current_time = time.time()
            
            if mode == MODE_RUN:
                # ターゲットの1つ前の建物名を取得
                prebuilding = get_target(target)
                #last_detect_time = 0
                # 環境認識後の処理（動画作成時も同じロジックを使う)
                status, detect_count, target_detected_time = update_status_and_action(status, category_index, last_detect, detect_count, prebuilding, target, stop_time, target_detected_time)
                last_detect = category_index
            elif mode == MODE_BACK:
                """
                prebuildingでモデルを切り替え
                停止時間をホーム位置で取得し、その時間指定で停止処理をおこなう
                """
                if car_id == 1 or car_id == 5:
                    target = "campus"
                    stop_time = HOME0_STOP_TIME
                elif car_id == 2 or car_id == 6:
                    target = "school"
                    stop_time = HOME1_STOP_TIME
                elif car_id == 3 or car_id == 7:
                    target = "hotel"
                    stop_time = HOME2_STOP_TIME
                elif car_id == 4 or car_id == 8:
                    target = "hospital"
                    stop_time = HOME3_STOP_TIME
                else:
                    target = "campus"
                    stop_time = HOME0_STOP_TIME
                prebuilding = get_target(target)
                status, detect_count, target_detected_time = update_status_and_action_back(status, category_index, last_detect, detect_count, prebuilding, target, stop_time, target_detected_time)
                last_detect = category_index               
            
            # 走行のカメラ画像を保存
            if record == True:
                name = "0_0_{:0=5}.jpg".format(count_cam1)
                image_path1 = os.path.join(save_dir1, name)
                cv2.imwrite(image_path1, remarked_img1)
                
            count_cam1 += 1
            frame_count += 1

            # 走行時の処理時間計測
            if time.time() - start_time > 3.0:
                fps = frame_count / 3.0
                speed_type = ""
                if speed_ai_flag == False:
                    speed_type = f"(固定)"
                else:
                    speed_type = f"(推論)"

                write_log(f"Cam1(環境用) target {target}, detect_count{detect_count}, prebuiling {prebuilding}, target {target}, status {status}, mode {mode}, car_id {car_id}, FPS: {fps:.1f}, 環境推論: {total_process_detect_time/(fps*3)*1000:.1f}ms")
                frame_count = 0
                start_time = time.time() 
                total_process_detect_time = 0
        except Exception as e:
            change_color("error2")
            error_message = f"Error live_cam1:{e}\n{''.join(traceback.format_exception(None, e, e.__traceback__))}"
            
    if record == True:
        write_log(f"画像を{cam1_count}枚の走行データを保存しました。")
        
def start_cameras():
    global cam0, cam1, running_cam0, running_cam1, execute_thread_cam0, execute_thread_cam1
    
    open_camera()
    
    # Cam0を起動
    running_cam0 = True
    execute_thread_cam0 = threading.Thread(target=live_cam0)
    execute_thread_cam0.start()
    write_log("Start cam0")

    # Cam1を起動
    running_cam1 = True
    execute_thread_cam1 = threading.Thread(target=live_cam1)
    execute_thread_cam1.start()
    write_log("Start cam1")

def setup_save_directory(base_path):
    # 指定された基本パスに基づいて保存ディレクトリを作成し、ログに記録します。
    if not os.path.exists(base_path):
        subprocess.call(['mkdir', '-p', base_path])
    write_log(f"{base_path}にデータを保存します。")

def run(change):
    global mode, running, start_time, save_dir0, save_dir1, load_model_a_trt, load_model_b_trt, load_model_c_trt, load_model_d_trt, load_model_e_trt, load_model_class_trt
    
    if not (load_model_a_trt and load_model_b_trt and load_model_c_trt and load_model_d_trt and load_model_e_trt and load_model_class_trt):
        write_log("モデルが読み込まれていません")
        return
    if not running:
        write_log("AIが起動しました。")
        if record:
            if name_widget.value != "":
                base_path = "camera/" + name_widget.value
                # Cam0とCam1の保存先を設定
                save_dir0 = f"{base_path}_cam0/xy/"
                save_dir1 = f"{base_path}_cam1/xy/"
                
                setup_save_directory(save_dir0)
                setup_save_directory(save_dir1)
            else:
                write_log("【Error】 映像の保存先を入力してください。")
                return
        write_log("カメラを起動中...")
        start_cameras()
        start_time = time.time()
        
        
def stop(change):
    global running_cam0,running_cam1,execute_thread_cam0,execute_thread_cam1,end_time,start_time,count_cam0,pwm_stop,mode_running
    if running_cam0 == True:
        PCA9685.set_channel_value(THROTTLE_CH, pwm_stop)
        try:
            end_time = time.time() - start_time
            fps = count_cam0/int(end_time)
            process_time = int((end_time/count_cam0)*1000)
        except:
            fps = -1
            process_time = -1
        
        write_log("AIを停止しました。")
        write_log("処理結果:FPS: " + str(round(fps,2)) + ",処理回数: " + str(count_cam0) + ",　処理時間(1回平均値): " + str(process_time) + " ms")
        running = False
        running_cam0 = False
        running_cam1 = False
        time.sleep(0.1)
        try:    
            execute_thread_cam0.join()
        except:
            write_log("Thread joinでエラー(すでにcam0 threadが存在しない")
        try:      
            execute_thread_cam1.join()
        except:
            write_log("Thread joinでエラー(すでにcam1 threadが存在しない")
        try:
            stop_camera(None)
        except:
            write_log("カメラの停止処理でエラー")
        
        write_log("走行モードの全処理を終了!!")
        mode_running = False
        
    else:
        PCA9685.set_channel_value(THROTTLE_CH, pwm_stop)
        write_log("現在AIは動いていません。")
        
import subprocess
import re

def get_jetson_nano_memory_usage(event=None):
    command = 'tegrastats'
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        mem_usage_pattern = re.compile(r'RAM (\d+)/(\d+)MB')
        
        max_lines_to_read = 10
        for _ in range(max_lines_to_read):
            line = process.stdout.readline()
            if not line:
                break 
            matches = mem_usage_pattern.search(line)
            if matches:
                #used_memory_widget.value = int(matches.group(1))
                #total_memory_widget.value = int(matches.group(2))
                process.kill()
                return
        
        process.kill()  
        return

    except subprocess.CalledProcessError as e:
        return

print("メモリ使用量取得")
get_jetson_nano_memory_usage()
#memory_button.on_click(get_jetson_nano_memory_usage)

import time

#release_button = ipywidgets.Button(description='Camera開放')

def stop_camera(c):
    global cam0,cam1
    cam0.running = False
    cam1.running = False
    time.sleep(0.1)
    cam0.cap.release()
    write_log("カメラ0を開放しました。")
    time.sleep(0.1)
    cam1.cap.release()
    write_log("カメラ1を開放しました。")

#release_button.on_click(stop_camera)

import serial
import time

import threading
import re  # 正規表現モジュール

def run_lora_threaded(c):
    global thread_lora
    write_log("LoRaスレッドを起動")
    try:
        thread_lora= threading.Thread(target=run_lora, args=(c,))
        thread_lora.start()
    except Exception as e:
        # スタックトレースを含むエラーメッセージを取得
        error_message = f"Error run_lora_thread:{e}\n{''.join(traceback.format_exception(None, e, e.__traceback__))}"
        write_log(error_message)

def stop_lora(c):
    global listening, thread_lora
    write_log("LoRaの受信状態を停止します。")
    try:
        listening = False
        thread_lora.join()
    except:
        write_log("Threadがjoinできません")
    stop(None)
    change_color("green")
    
def run_lora(c=None):
    global listening, ser, target, mode, car_id, mode_running
    listening = True  # リスニングを有効にする
    init_led()
    change_color("orange")
    port = '/dev/ttyUSB0'  # シリアルポートのデバイス名
    baudrate = 9600        # ボーレート（デバイスに合わせて設定）
    timeout = 1            # タイムアウトの秒数
    write_log("LoRaのリスニングを開始")
    #write_log(f"初期のcar_id {carid_dropbox.value}")
    mode_running = False
    try:
        # シリアル接続を開始する前にRTSを制御してLoRaモジュールをリセット
        pre_reset_ser = serial.Serial(port, baudrate, timeout=timeout)
        pre_reset_ser.setRTS(False)  # RTSをLOWに設定
        time.sleep(0.1)  # 少し待機
        pre_reset_ser.setRTS(True)  # RTSをHIGHに設定
        pre_reset_ser.close()  # RTS制御用の接続を閉じる

        # シリアルポートを開く
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            write_log(f"{port} でリスニング中...")
            try:
                lora_send_status(car_id, LORA_STATUS_IDLE)
                while listening:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8').strip()  # データを文字列として読み取り
                        write_log(f"受信データ: {data}")

                        # 正規表現を使って送信者IDと目的の値を抽出
                        match = re.search(r'\[([0-9]+)\]\s([0-9]+)', data)
                        if match:
                            car_id = int(match.group(1))  # 自車ID
                            value = int(match.group(2))  # 目的の値を整数に変換
                            write_log(f"自社ID: {car_id}, 抽出した値: {value}")
                            if mode_running == False:
                                # 抽出した値が1から8の範囲内か判定
                                if 1 <= value <= len(CATEGORIES):
                                    lora_send_status(car_id, LORA_STATUS_DRIVING)
                                    write_log(f"値は1〜{len(CATEGORIES)}の範囲内です。")
                                    target = CATEGORIES[value-1]  # 取得値は1〜8の範囲だが、配列を使うために-1している
                                    mode = MODE_RUN
                                    mode_running = True
                                    run(None)  # 実際に何かしらの処理を行う関数をここで呼び出す
                                # Building idが0が抽出された場合は、ホーム位置に戻す
                                elif value == 0:
                                    #lora_send_status(car_id, LORA_STATUS_DRIVING)
                                    mode = MODE_BACK
                                    lora_send_status(car_id, LORA_STATUS_GO_BACK_HOME)
                                    mode_running = True
                                    write_log("BACK modeで戻ります。")
                                    run(None)
                                else:
                                    write_log("値は0-8の範囲外です。")
                            else:
                                write_log("現在走行中です。")

                    time.sleep(0.1)  # CPU使用率の低減
            except Exception as e:
                error_message = f"Error run_lora:{e}\n{''.join(traceback.format_exception(None, e, e.__traceback__))}"
                write_log(error_message)
            finally:
                write_log("リスニング停止")

    except Exception as e:
        change_color("error3")
        error_message = f"Error run_lora:{e}\n{''.join(traceback.format_exception(None, e, e.__traceback__))}"
        write_log(error_message)

            
            
#run_lora_button.on_click(run_lora_threaded)
#stop_lora_button.on_click(stop_lora)

DEBUG = True
import numpy as np
def auto_load_model(path, model_var_name):
    try:
        write_log(f"{path}の読込を実行します(初回は時間がかかります)。")
        model = TRTModule()
        model.load_state_dict(torch.load(path))
        model(preprocess(np.zeros((224, 224, 3)).astype(np.uint8)))
        write_log(f"{path}の読込に成功しました。")
        globals()[model_var_name] = model  # 成功した場合、グローバル変数にモデルをセット
        load_flag_var_name = f"load_{model_var_name}"
        write_log(f"{load_flag_var_name}の読込に成功しました。")
        globals()[load_flag_var_name] = True  # 対応するフラグをTrueにセット
        get_jetson_nano_memory_usage()
    except Exception as e:
        write_log(f"【Error】 {e} : {widget.value} の読込に失敗しました。")
        
print(f"モデルの読み込み")
auto_load_model("/home/jetson/data/notebooks/model_trt/out_straight1.pth", 'model_a_trt')
auto_load_model("/home/jetson/data/notebooks/model_trt/out_right1.pth", 'model_b_trt')
auto_load_model("/home/jetson/data/notebooks/model_trt/in_straight1.pth", 'model_c_trt')
auto_load_model("/home/jetson/data/notebooks/model_trt/in_right1.pth", 'model_d_trt')
auto_load_model("/home/jetson/data/notebooks/model_trt/parking.pth", 'model_e_trt')
auto_load_model("/home/jetson/data/notebooks/model_class_trt/result.pth", 'model_class_trt')

car_id = 5

print(f"LoRa起動")
SPEED_FAST = 190
SPEED_SLOW = 120

CAT0_STOP_TIME = 1000
CAT1_STOP_TIME = 1000
CAT2_STOP_TIME = 1000
CAT3_STOP_TIME = 1000
CAT4_STOP_TIME = 1000
CAT5_STOP_TIME = 1000
CAT6_STOP_TIME = 1000
CAT7_STOP_TIME = 1000

HOME1_STOP_TIME = 1000
HOME2_STOP_TIME = 1000
HOME3_STOP_TIME = 1000
HOME4_STOP_TIME = 1000

run_lora_threaded(None)