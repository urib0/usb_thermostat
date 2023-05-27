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
SSR_ON = True
SSR_OFF = False
SSR_RETRY = 3
P = 0
I = 0
D = 0
kP = 1
kI = 0
kD = 0

def ssr_controller(switch: bool):
        for i in range(SSR_RETRY):
            try:
                ssr = serial.Serial(conf["ssr"]["serial_port"],conf["ssr"]["serial_rate"],timeout=3)
                if switch:
                    ssr.write(b"1")
                else:
                    ssr.write(b"0")
                ssr.close()
                return True
            except Exception as e:
                print(f"error:{e}")
        return False

def conv(data):
    if data[0] in {"temp", "hum", "te"}:
        return int(data[1]) / 100
    else:
        return int(data[1])

def logger(s):
    print(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")[:-2]+":"+s)

temp_old = 0
while True:
    # 設定値読み込み
    f = open("./config.json", "r")
    conf = json.loads(f.read())
    f.close()
    try:
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
        ontime = P*kP+I*kI+D*kD
        temp_old = temp

        logger(f"temp:{str(temp)},ontime:{round(ontime,2)},tP:{str(round(P,2))},tI:{round((I),2)},tD:{round(D,2)}")
        logger("ontime:"+str(ontime)+",offtime:"+str(conf["interval"]-ontime))
        if ontime<=0:
            ssr_controller(SSR_OFF)
            time.sleep(conf["interval"])
        elif ontime > conf["interval"]:
            ssr_controller(SSR_ON)
            time.sleep(conf["interval"])
        else:
            ssr_controller(SSR_ON)
            time.sleep(ontime)
            ssr_controller(SSR_OFF)
            time.sleep(conf["interval"]-int(ontime))

    except KeyboardInterrupt:
        print("SSR OFF!!")
        ssr_controller(SSR_OFF)
        exit(0)
