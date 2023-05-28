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
SSR_ON = True
SSR_OFF = False
kP = 1
kI = 0
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

#def thermocouple():
#    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
#    filename = conf["logdir"] + "/" +\
#        conf["thermo"]["sensor_name"] + "/" +\
#        conf["thermo"]["sensor_name"] + "_" +\
#        timestamp + ".csv"
#    f = open(filename,"r")
#    lines = f.readlines()[-1:][0][:-1]
#    f.close
#    temp = float(lines.split(",")[1].split(";")[0].split("=")[1])/100
#    return temp

def conv(data):
    if data[0] in {"temp", "hum", "te"}:
        return int(data[1]) / 100
    else:
        return int(data[1])

def log_print(s):
    print(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S:%f")[:-2]+":"+s)

def log_export(path,name,data):
    timestamp = datetime.datetime.now()
    filename = name + "_" + timestamp.strftime("%Y-%m-%d") + ".csv"
    write_str = timestamp.strftime("%Y/%m/%d %H:%M:%S") + "," + data
    path = path + "/" + name + "/"

    os.makedirs(path, exist_ok=True)
    f = open(path + filename, mode="a")
    f.write(write_str + "\n")
    f.close()

def digit_alignment(num):
    return "{:.3f}".format(num)

# 設定値読み込み
f = open("./config.json", "r")
conf = json.loads(f.read())
f.close()

path = conf['logdir']
name = "thermo"

ssr = ssr_controller(conf["ssr"]["serial_port"],conf["ssr"]["serial_rate"])
thermo = themocouple_controller(conf["thermo"]["serial_port"],conf["thermo"]["serial_rate"])

interval = conf["interval"]
temp_target = conf["TEMP_TARGET"]
temp_old = thermo.read_temp()

while True:
    #　熱電対読み込み
    ret = thermo.read_temp()
    print(f"{ret=}")
    if ret is None:
        continue
    else:
        temp = float(ret)

    dt = interval
    P = temp_target-temp
    I = P/dt
    D = (temp-temp_old)*dt
    ontime = P*kP+I*kI+D*kD
    temp_old = temp

    log_print(f"interval:{round(interval,3)},ontime:{round(ontime,3)},offtime:{round(interval-ontime,3)},temp:{digit_alignment(temp)},tP:{digit_alignment(P*kP)},tI:{digit_alignment(I*kI)},tD:{digit_alignment(D*kD)}")

    if ontime<=0:
        ssr.off()
        time.sleep(interval)
    elif ontime > interval:
        ssr.on()
        time.sleep(interval)
    else:
        ssr.on()
        time.sleep(ontime)
        ssr.off()
        time.sleep(interval-int(ontime))
