from main.time import sleep

from main.simple import MQTTClient

from main.machine import Pin, I2C, ADC

import main.bmp280

from dht import DHT22

import main.adafruit_sgp30

import main.mq135

import network

import json



SERVER = '192.168.1.1'  # MQTT Server Address (Change to the IP address of your Pi)

CLIENT_ID = 'node8'

TOPIC = '/terminal'



#station = network.WLAN(network.STA_IF)
#station.active(True)
#station.ifconfig(('192.168.1.28','255.255.255.0','192.168.1.1','1.1.1.1'))
#station.connect("terminalUTAD","ecocampus2019")
#while station.isconnected() == False:
#    print("Trying to connect...")





client = MQTTClient(CLIENT_ID, SERVER)

client.connect()   # Connect to MQTT broker



sensordht = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))   # DHT-22 on GPIO 15 (input with internal pull-up resistor)

i2c = I2C(scl=Pin(22), sda=Pin(21))

i2csgp30 = I2C(scl=Pin(17), sda=Pin(16))

bmp = bmp280.BMP280(i2c)

sgp30 = adafruit_sgp30.Adafruit_SGP30(i2csgp30)

sgp30.iaq_init()

sgp30.set_iaq_baseline(0x8973, 0x8aae)

mq135 = mq135.MQ135(Pin(36))



while True:

    try:

        sensordht.measure()   # Poll sensor

        tempdht = sensordht.temperature()

        humdht = sensordht.humidity()

        data = {}

        if isinstance(tempdht, float) and isinstance(humdht, float):  # Confirm sensor results are numeric

            data["node"] = CLIENT_ID
            data["dht22_temp"] = tempdht
            data["dht22_hum"] = humdht
            rzero = mq135.get_rzero()
            if rzero < 0:
                corrected_rzero = -1
                rzero = -1
                resistance = -1
                corrected_ppm = 400
                ppm = 400
            else:
                corrected_rzero = mq135.get_corrected_rzero(22,55)
                resistance = mq135.get_resistance()
                ppm = mq135.get_ppm()
                corrected_ppm = mq135.get_corrected_ppm(tempdht,humdht)
                if ppm > 1000 or corrected_ppm > 1000:
                    ppm = 400
                    corrected_ppm = 400

            data["mq135_rzero"] = rzero
            data["mq135_corrected_rzero"] = corrected_rzero
            data["mq135_resistance"] = resistance
            data["mq135_ppm"] = ppm
            data["mq135_corrected_ppm"] = corrected_ppm
            data["bmp280_temp"] = bmp.temperature
            data["bmp280_pressure"] = bmp.pressure
            data["sgp30_co2"] = sgp30.co2eq
            data["sgp30_tvoc"] = sgp30.tvoc
            #data["adc_0"] = ADC(Pin(0)).read()
            #data["adc_36"] = ADC(Pin(36)).read()
            client.publish(TOPIC, json.dumps(data))  # Publish sensor data to MQTT topic
        else:
            msg = "Error: Invalid sensor readings"
            client.publish(TOPIC,msg)

    except OSError:
            msg = "Error: Failed to read sensor"
            client.publish(TOPIC,msg)
    sleep(15)
