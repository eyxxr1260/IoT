import os
import lineTool
import time
import datetime
import requests
import sys
import time
import board
import adafruit_dht
import psutil
import RPi.GPIO as GPIO

Token = "jiMa4eK4FYnGdhstesCeWW5uiY0dkyf6ZAZySmgWyYD" #Line notify's token

MONITOR_PIN = 18 #BCM type PIN腳位
LED_PIN = 23
BUZZ_PIN = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(MONITOR_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUZZ_PIN, GPIO.OUT)

ENDPOINT = "industrial.api.ubidots.com"
DEVICE_LABEL = "Demo"
VARIABLE_LABEL = "temperature"
TOKEN = "BBFF-WrOsDisvkjPOiCqjguv1U14kbWUhY9" # ubidots's TOKEN
DELAY = 1  # Delay in seconds

pitches = [330, 262, 330, 262, 330, 262]
pwm = GPIO.PWM(BUZZ_PIN, pitches[0])
pwm.start(0)

def play(pitch, intv): #play sound with pitch frequency and rest for intv second
    pwm.ChangeFrequency(pitch)
    time.sleep(intv)


for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()
sensor = adafruit_dht.DHT11(board.D4)#DHT11偵測

def post_var(payload, url=ENDPOINT, device=DEVICE_LABEL, token=TOKEN):#post data to Ubidots
    try:
        url = "http://{}/api/v1.6/devices/{}".format(url, device)
        headers = {"X-Auth-Token": token, "Content-Type": "application/json"}

        attempts = 0
        status_code = 400

        while status_code >= 400 and attempts < 5:
            req = requests.post(url=url, headers=headers,
                                json=payload)
            status_code = req.status_code
            attempts += 1
            time.sleep(1)

        print(req.text)
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))

def action(channel): # 若18角位偵測到為RISING則觸發
    t = time.localtime() # 取得現在時間
    current_time = time.strftime("%H:%M:%S", t)
    print(current_time+"Motion detected")

    for i in range(3): #LED閃爍三次
        GPIO.output(LED_PIN, True)
        time.sleep(0.2)
        GPIO.output(LED_PIN, False)
        time.sleep(0.2)

GPIO.add_event_detect(MONITOR_PIN, GPIO.RISING, action, 200) #隨時偵測MONITOR_PIN的狀態


try:
    while True:
        try:
            temp = sensor.temperature #temp 為所偵測到的溫度
            payload = {VARIABLE_LABEL: temp}
            post_var(payload)#將偵測到的溫度傳送到Ubidots
            inp=GPIO.input(MONITOR_PIN)
            if inp==1 and temp>=30:#判斷GPIO.input(MONITOR_PIN)是否為true且溫度大於30
                pwm.ChangeDutyCycle(50)
                for pitch in pitches:#播放pitches中的頻率
                    play(pitch, 0.5)
                pwm.ChangeDutyCycle(0)#停止播放
                Time_message = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())#將時間以yyyy-mm-dd hh-mm-ss格式呈現
                MESSAGE = ''
                time.sleep(3)
                MESSAGE = "\n車內現在溫度:"+str(temp)+"度\n偵測到生物\n"+ Time_message #Line notify中呈現的訊息 
                print("Send message to Line \n%s\n" % MESSAGE)
                lineTool.lineNotify(Token, MESSAGE)
                time.sleep(5)

        except RuntimeError as error:
            print(error.args[0])
            time.sleep(1.0)
            continue
        except Exception as error:
            sensor.exit()
            raise error
        time.sleep(DELAY)
except KeyboardInterrupt:
    print("Exception: KeyboardInterrupt")
    sensor.exit()
finally:
    GPIO.cleanup()