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

    dt = conf["interval"]
    P = conf["TEMP_TARGET"]-temp
    I = P/dt
    D = (temp-temp_old)*dt
    val = P*kP+I*kI+D*kD
    temp_old = temp

    logger(f"P:{str(P)},I:{str(I)},D:{str(D)},val:{str(val)},")
    ser = serial.Serial(conf["ssr"]["serial_port"],conf["ssr"]["serial_rate"],timeout=3)
    logger("ontime:"+str(val)+",offtime:"+str(conf["interval"]-val)) 
    if int(val*100)<=0:
        val = 0
        ser.write(SSR_OFF)
        ser.close()
    else:
        if int(val*100)>(conf["interval"]*100):
            val = conf["interval"]
        if int(val*100)<100:
            val = 1
        ser.write(SSR_ON)
        time.sleep(val+0.5)
        ser.write(SSR_OFF)    
        ser.close()

    time.sleep(conf["interval"]-int(val))

