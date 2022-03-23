#!/usr/bin/env python3
# python3.7で動作確認済み

from os import kill
from sqlite3 import Timestamp
import time
import json
import datetime as dt
import serial
import datetime

DEBUG = False
REPETITIONS = 3
SSR_ON = b"1"
SSR_OFF = b"0"
TEMP_DIFF_STANDARD = 20
ON_TIME = 5
P = 0
I = 0
D = 0
kP = 1
kI = 0
kD = 0

def conv(data):
    if data[0] in {"temp", "hum", "te"}:
        return int(data[1]) / 100
    else:
        return int(data[1])

def logger(s):
    print(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")[:-2]+":"+s)

# 設定値読み込み
f = open("./config.json", "r")
conf = json.loads(f.read())
f.close()

temp_old = 0
while conf["interval"]:
    #　熱電対読み込み
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = conf["logdir"] + "/" +\
        conf["thermo"]["sensor_name"] + "/" +\
        conf["thermo"]["sensor_name"] + "_" +\
        timestamp + ".csv"
    f = open(filename,"r")
    lines = f.readlines()[-1:][0][:-1]
    f.close
    temp = float(lines.split(",")[1].split(";")[0].split("=")[1])/100

    if False:
        # ログに含まれるセンサの数がconfig.jsonと同じか確認
        data_list = lines.split(",")[1].split(";")
        data_num = (len(data_list) - 2)
        if len(conf["thermo"]["sensors"]) == data_num:
            for i in range(data_num):
                # センサ名と数字のペアができる ex) ["temp","2657"]
                temp_now = data_list[i].split("=")[1]
        # 目標温度より低かったらSSRをON、高かったらOFFする
        temp_diff = (int(temp_now)-conf["TEMP_TARGET"]*100)*(-1)
        if temp_diff < 0:temp_diff = 0
        print("temp_diff:"+str(temp_diff))
        ontime = (temp_diff/TEMP_DIFF_STANDARD)/10
        print("ontime:"+str(ontime))
        print("temp_now:"+str(int(temp_now)+int(temp_diff*(-1)))+",target:"+str(conf["TEMP_TARGET"]*100))
        ser = serial.Serial(conf["ssr"]["serial_port"],conf["ssr"]["serial_rate"],timeout=3)
        if (int(temp_now)+int(temp_diff*(-1)))>(conf["TEMP_TARGET"]*100) :
            timestamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")[:-2]
            ser.write(SSR_ON)
            print(str(timestamp) + "," + "temp:" + str(int(temp_now)/100)+"," + "SSR:" + SSR_ON.decode("utf-8") + "," + str(temp_diff))
            time.sleep(ontime)
            ser.write(SSR_OFF)
            timestamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")[:-2]
            print(str(timestamp) + "," + "temp:" + str(int(temp_now)/100)+"," + "SSR:" + SSR_OFF.decode("utf-8") + "," + str(temp_diff))
        else:
            timestamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")[:-2]
            ser.write(SSR_OFF)
            print(str(timestamp) + "," + "temp:" + str(int(temp_now)/100)+"," + "SSR:" + SSR_OFF.decode("utf-8") + "," + str(temp_diff))
            ser.close()
        sleeptime = conf["interval"]-ontime

    dt = conf["interval"]
    P = conf["TEMP_TARGET"]-temp
    I = P/dt
    D = (temp-temp_old)*dt
    val = P*kP+I*kI+D*kD
    temp_old = temp

    logger("temp:"+str(temp)+",target:"+str(conf["TEMP_TARGET"]))
    logger("P:"+str(P))
#    logger("I:"+str(I))
#    logger("D:"+str(D))
    logger("val:"+str(val))
    ser = serial.Serial(conf["ssr"]["serial_port"],conf["ssr"]["serial_rate"],timeout=3)
    if int(val*100)<=0:
        val = 0
        ser.write(SSR_OFF)
        logger("SSR:OFF")
        ser.close()
    else:
        if int(val*100)>(conf["interval"]*100):
            val = conf["interval"]
        if int(val*100)<100:
            val = 1
        logger("ontime:"+str(val)+",offtime:"+str(conf["interval"]-val)) 
        ser.write(SSR_ON)
        logger("SSR:ON")
        time.sleep(val+0.5)
        ser.write(SSR_OFF)    
        logger("SSR:OFF")
        ser.close()

    time.sleep(conf["interval"]-int(val))

