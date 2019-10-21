#!/usr/bin/python
# Importing modules
import blynklib
import time
import spidev # To communicate with SPI devices
from numpy import interp	# To scale values
from time import sleep	# To add delay
import RPi.GPIO as GPIO	# To use GPIO pins
from prettytable import PrettyTable
import os
# Start SPI connection
spi = spidev.SpiDev() # Created an object
spi.open(0,0)	
# Initializing LED pin as OUTPUT pin

BLYNK_AUTH = 'cDmplVIRR37OONz6GUATP-2zQPVWGAbk' #insert your Auth Token here
# base lib init
blynk = blynklib.Blynk(BLYNK_AUTH)

output_LDR = 0.0
output_POT = 0.0
output_TEMP = 0.0
output_DAC = 0

alarm = 0
alarmtime0 = 0
alarmtime = 0
firstAlarm = True

localtime=0
systime=0
date =0
t0=time.time()

sampletime=1
check = -1
send_blink = True

monitoring = True
cleartable = False

t=PrettyTable(['RTC Time', 'System Time', 'Light', 'Temperature', 'Humidity', 'DAC', 'Alarm'])

GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(25, GPIO.OUT)

def changeSampleTime(channel):
  
    global sampletime

    if sampletime==1:
        sampletime=2
    elif sampletime==2:
        sampletime=5
    elif sampletime==5:
        sampletime=1
    print("Sample time changed to " +str(sampletime))

GPIO.add_event_detect(5, GPIO.RISING, callback=changeSampleTime, bouncetime=300)

def toggleMonitoring(channel):

  global monitoring

  if monitoring:
    monitoring=False
    print("Stopping monitoring")
  else:
    monitoring=True
    print("Starting monitoring")

GPIO.add_event_detect(6, GPIO.RISING, callback=toggleMonitoring, bouncetime=300)

def resetCallback(channel):
  
    global cleartable
    global t0
    global alarmtime0
    global firstAlarm
    global alarm

    cleartable=True
    alarm = 0
    t0=time.time()
    alarmtime0 = 0
    firstAlarm = True
  

GPIO.add_event_detect(13, GPIO.RISING, callback=resetCallback, bouncetime=300)

def alarmResetCallback(channel):

    global alarm
    if alarm == 1:
        print("Alarm Dismissed!")
        GPIO(25, GPIO.LOW)
    alarm = 0
    


GPIO.add_event_detect(26, GPIO.RISING, callback=alarmResetCallback, bouncetime=300)

# Read MCP3008 data
def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

def Volts(data):
    volts = (data * 3.3) / float(1023)
    volts = round(volts, 2) # Round off to 2 decimal places
    return volts
 
# Below function will convert data to temperature.
def Temp(data):
    temp = (data*3.3)/float(1023)
    temp = round((temp-0.5)/0.01,2)
    return temp

@blynk.VIRTUAL_WRITE(0)
def write_handler0(value);
	print(str(output_LDR))
	
@blynk.VIRTUAL_WRITE(1)
def write_handler1(value);
	print(str(round(output_POT,2)))
	
@blynk.VIRTUAL_WRITE(2)
def write_handler2(value);
	print(str(round(output_TEMP,1)))
	
@blynk.VIRTUAL_WRITE(3)
def write_handler3(value);
	print(systime)
	
@blynk.VIRTUAL_WRITE(4)
def write_handler4(value);
	print(alarm*255)

while True:
    
    blynk.run()
    if cleartable:
        t.clear_rows()
        cleartable=False
        os.system('clear')
        send_blink=True

    localtime = time.strftime("%H:%M:%S", time.gmtime(time.time()))
    systime = time.strftime("%H:%M:%S", time.gmtime(time.time()-t0))
    alarmtime = time.strftime("%H:%M:%S", time.gmtime(time.time()-alarmtime0))
    second = int(systime[-2:])
    alarmtime_minute = int(alarmtime[3:5])
    alarmtime_hour = int(alarmtime[:2])
    alarmtime_second = int(alarmtime[-2:])

    if (second != check and second%sampletime==0 and monitoring):
        
        check = second
        #print(str(alarmtime_hour) + str(alarmtime_minute) + str(alarmtime_second))
        #print( str(output_DAC) + "; Alarm:" + str(alarm))
        output_LDR = analogInput(0) # Reading from CH0
    
        output_POT = analogInput(1) # Reading from CH1
        output_POT = interp(output_POT, [0, 1023], [0, 33])/10
    
        output_TS = analogInput(2) # Reading from CH2
        output_TS = interp(output_TS, [0, 1023], [0, 33])/10
        output_TEMP = Temp(output_TS)

        output_DAC = (output_LDR/1023)*output_POT

        if ((output_DAC>2.65 or output_DAC<0.65) and (alarmtime_minute>=3 or alarmtime_hour>=1)) or ((output_DAC>2.65 or output_DAC<0.65) and firstAlarm):
            alarm = 1
            alarmtime0 = time.time()
            firstAlarm = False
            GPIO(25, GPIO.HIGH)

        send_blink = True

        t.add_row([str(localtime), str(systime), str(round(output_LDR,2)), str(round(output_POT,2)), str(round(output_TEMP,1)),str(round(output_DAC,2)), str(alarm)])
        print(t)

        #print(systime[-2:])
        #print(localtime)
        #print(systime)
        #print("Light: " + str(round(output_LDR,2)))
        #print("Humidity: " + str(round(output_POT,2)))
        #print("Temp Voltage: " + str(output_TS))
        #print("Temperature: " + str(round(output_TEMP,1))+"\n")
    


	#pwm.ChangeDutyCycle(output)

    #sleep(1)
