#!/usr/bin/env python3
# python3.7で動作確認済み

import ambient
import time
import json
import datetime as dt
import sys
import random
import os
import subprocess
import requests
import serial

DEBUG = False
REPETITIONS = 3
SSR_ON = b"1"
SSR_OFF = b"0"
TEMP_TARGET = 60
TEMP_OFFSET = 2

def conv(data):
    if data[0] in {"temp", "hum", "te"}:
        return int(data[1]) / 100
    else:
        return int(data[1])


# 設定値読み込み
f = open("./config.json", "r")
conf = json.loads(f.read())
f.close()

while conf["interval"]:
    #　熱電対読み込み
    filename = conf["logdir"] + "/" + conf["thermo"]["sensor_name"] + "/" + conf["thermo"]["sensor_name"] + "_" + dt.datetime.now().strftime("%Y-%m-%d") + ".csv"
    f = open(filename,"r")
    lines = f.readlines()[-1:][0][:-1]
    f.close
    ser = serial.Serial(conf["ssr"]["serial_port"],conf["ssr"]["serial_rate"],timeout=3)

    # ログに含まれるセンサの数がconfig.jsonと同じか確認
    data_list = lines.split(",")[1].split(";")
    data_num = (len(data_list) - 2)
    if len(conf["thermo"]["sensors"]) == data_num:
        for i in range(data_num):
            # センサ名と数字のペアができる ex) ["temp","2657"]
            temp_now = data_list[i].split("=")[1]

    # 目標温度より低かったらSSRをON、高かったらOFFする
    if int(temp_now) < ( ( TEMP_TARGET - TEMP_OFFSET ) * 100 ) :
        ser.write(SSR_ON)
        print("temp:" + str(int(temp_now)/100)+" " + "SSR:" + SSR_ON.decode("utf-8"))
    else:
        ser.write(SSR_OFF)
        print("temp:" + str(int(temp_now)/100)+" " + "SSR:" + SSR_OFF.decode("utf-8"))
        time.sleep(conf["interval"])
    time.sleep(conf["interval"])



