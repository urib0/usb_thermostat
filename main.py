#!/usr/bin/env python3
# python3.7で動作確認済み

from os import kill
from sqlite3 import Timestamp
import time
import json
import datetime as dt
import serial
import datetime
from typing import Union
import os

DEBUG = False
kP = 1
kI = 0.1
kD = 0

class usb_comon_sense_controller():
    def __init__(self,port,rate):
        self.device = serial.Serial(port,rate,timeout=3)

    def write(self,data: str) -> bool:
        for i in range(3):
            try:
                self.device.write(data.encode())
                return True
            except Exception as e:
                print(f"error:{e}")
        return False

    def read(self) -> str:
        self.device.reset_input_buffer()
        return self.device.readline().decode().replace("\n","")

    def __del__(self):
        self.device.close()

class ssr_controller():
    def __init__(self,port,rate):
        try:
            self.ssr = usb_comon_sense_controller(port,rate)
        except Exception as e:
            print(e)
            exit(0)

    def on(self) -> bool:
        return self.ssr.write("1")

    def off(self) -> bool:
        return self.ssr.write("0")

    def __del__(self):
        self.off()

class themocouple_controller():
    def __init__(self,port,rate):
        try:
            self.thermo = usb_comon_sense_controller(port,rate)
        except Exception as e:
            print(e)
            exit(0)

    def read_temp(self) -> Union[float,None]:
        raw = self.thermo.read()
        log_export(path,name,raw)
        raw = raw.split(";")[0]
        if raw.split("=")[0] != "te":
            return None
        return int(raw.split("=")[1])/100

def log_print(s):
    print(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")[:-4]+":"+s)

def log_export(path,name,data):
    timestamp = datetime.datetime.now()
    filename = name + "_" + timestamp.strftime("%Y-%m-%d") + ".csv"
    write_str = timestamp.strftime("%Y/%m/%d %H:%M:%S") + "," + data
    path = path + "/" + name + "/"

    os.makedirs(path, exist_ok=True)
    with open(path + filename, mode="a") as f:
        f.write(write_str + "\n")

def digit_alignment(num):
    return "{:.2f}".format(num)

# 設定値読み込み
with open("./config.json", "r") as f:
    conf = json.loads(f.read())

path = conf['logdir']
name = "thermo"

ssr = ssr_controller(conf["ssr"]["serial_port"],conf["ssr"]["serial_rate"])
thermo = themocouple_controller(conf["thermo"]["serial_port"],conf["thermo"]["serial_rate"])

interval = conf["interval"]
temp_target = conf["TEMP_TARGET"]
temp_old = thermo.read_temp()

sumDiff = 0
preDiff = 0
while True:
    #　熱電対読み込み
    ret = thermo.read_temp()
    if ret is None:
        continue
    else:
        temp = float(ret)

    dt = interval
    nowDiff = temp_target-temp
    sumDiff += nowDiff
    P = nowDiff
    I = sumDiff*dt
    D = (nowDiff-preDiff)/dt
    ontime = P*kP+I*kI+D*kD
    preDiff = nowDiff

    log_print(f"interval:{digit_alignment(interval)},temp:{digit_alignment(temp)},on:{digit_alignment(ontime)},off:{digit_alignment(interval-ontime)},tP:{digit_alignment(P*kP)},tI:{digit_alignment(I*kI)},tD:{digit_alignment(D*kD)}")

    if ontime<1:
        ssr.off()
        time.sleep(interval)
    elif ontime > interval:
        ssr.on()
        time.sleep(interval)
    else:
        ssr.on()
        time.sleep(int(ontime))
        ssr.off()
        time.sleep(int(interval-ontime))
