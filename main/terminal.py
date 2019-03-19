from time import sleep
from main.simple import MQTTClient
from machine import Pin, I2C, ADC
import main.bmp280 as bmp280
from dht import DHT22
import main.adafruit_sgp30 as adafruit_sgp30
import main.mq135 as mq135
import network
import json

class Terminal:
    def __init__(self,node_name,node_ip,node_gateway,node_wifi_ssid,node_wifi_password):
        self.node_name = node_name
        self.node_ip = node_ip
        self.node_gateway = node_gateway
        self.node_wifi_ssid = node_wifi_ssid
        self.node_wifi_password = node_wifi_password
        self.client = MQTTClient(self.node_name,self.node_gateway)
        self.client.connect()
        self.sensordht = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))
        self.i2c = I2C(scl=Pin(22), sda=Pin(21))
        self.i2csgp30 = I2C(scl=Pin(17), sda=Pin(16))
        self.bmp = bmp280.BMP280(self.i2c)
        self.sgp30 = adafruit_sgp30.Adafruit_SGP30(self.i2csgp30)
        self.sgp30.iaq_init()
        self.mq135 = mq135.MQ135(Pin(36))
        self.data = {}
        self.data["node"] = self.node_name

    #publish json via mqtt to topic
    def sendframe(self):
        self.client.publish("/terminal", json.dumps(self.data))

   # 1) read dht22 temp and humidity
    def readDHT22(self):
        self.sensordht.measure()
        if isinstance(self.sensordht.temperature(), float) and isinstance(self.sensordht.humidity(), float):
            self.data["dht22_temp"] = self.sensordht.temperature()
            self.data["dht22_hum"] = self.sensordht.humidity()
        else:
            self.data["dht22_temp"] = -1
            self.data["dht22_hum"] = -1

    # 2) read mq135 CO2 PPM and other values
    def readMQ135(self):
        self.data["mq135_rzero"] = self.mq135.get_rzero()
        #print(self.data["rzero"])
        self.data["mq135_corrected_rzero"] = self.mq135.get_corrected_rzero(22,55)
        if self.data["mq135_rzero"] < 0: # sensor em aquecimento colocamos tudo a -1 e damos return
            self.data["mq135_rzero"] = -1
            self.data["mq135_corrected_rzero"] = -1
            self.data["mq135_ppm"] = -1
            self.data["mq135_corrected_ppm"] = -1
            self.data["mq135_resistance"] = -1
            return
        else:
            self.data["mq135_ppm"] = self.mq135.get_ppm()
            print('Temperature: ' + str(self.data["dht22_temp"]) + 'Humidity: ' + str(self.data["dht22_hum"]))
            self.data["mq135_corrected_ppm"] = self.mq135.get_corrected_ppm(self.data["dht22_temp"],self.data["dht22_hum"])
            #se o valor do ppm for maior que 4000
            if self.data["mq135_ppm"] >= 4000 or self.data["mq135_corrected_ppm"] >= 4000:
                self.data["mq135_ppm"] = -1
                self.data["mq135_corrected_ppm"] = -1
            self.data["mq135_resistance"] = self.mq135.get_resistance()
            return


    # 3) read bmp280 temp and pressure
    def readBMP280(self):
        self.data["bmp280_temp"] = self.bmp.temperature
        self.data["bmp280_pressure"] = self.bmp.pressure

    # 4) read sgp30 co2 and tvoc
    def readSGP30(self):
        #self.co2eq,self.tvoc = self.sgp30.iaq_measure()
        self.data["sgp30_co2"] = self.sgp30.co2eq
        self.data["sgp30_tvoc"] = self.sgp30.tvoc

    # 5) read sensor data
    def read(self):
        self.readDHT22()
        self.readMQ135()
        self.readBMP280()
        self.readSGP30()
        self.sendframe()
