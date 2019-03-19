import math
import time
from machine import ADC, Pin

class MQ135(object):
    """ Class for dealing with MQ13 Gas Sensors """
    # The load resistance on the board
    RLOAD = 16
    # Calibration resistance at atmospheric CO2 level
    RZERO = 76.63
    # Parameters for calculating ppm of CO2 from sensor resistance
    PARA = 116.6020682
    PARB = 2.769034857
    # Parameters to model temperature and humidity dependence
    CORA = 0.00035
    CORB = 0.02718
    CORC = 1.39538
    CORD = 0.0018
    CORE = -0.003333333
    CORF = -0.001923077
    CORG = 1.130128205
    # Atmospheric CO2 level for calibration purposes
    ATMOCO2 = 400

    def __init__(self, pin):
        self.pin = pin

    def get_correction_factor(self, temperature, humidity):
        if temperature < 20:
            return self.CORA * temperature * temperature - self.CORB * temperature + self.CORC - (humidity - 33.) * self.CORD
        return self.CORE * temperature + self.CORF * humidity + self.CORG

    def get_resistance(self):
        adc = ADC(self.pin)
        value = adc.read()
        #print(value)
        if value == 0:
            return -1
        return (1023./value - 1.) * self.RLOAD

    def get_corrected_resistance(self, temperature, humidity):
        """Gets the resistance of the sensor corrected for temperature/humidity"""
        return self.get_resistance()/ self.get_correction_factor(temperature, humidity)

    def get_ppm(self):
        #print(str(self.get_resistance()))
        #print(str(self.RZERO))
        """Returns the ppm of CO2 sensed (assuming only CO2 in the air)"""
        if self.get_resistance() <= 0 or self.RZERO <=0:
                return self.PARA * math.pow((abs(self.get_resistance())/ abs(self.RZERO)), -self.PARB)
        return self.PARA * math.pow((self.get_resistance()/ self.RZERO), -self.PARB)

    def get_corrected_ppm(self, temperature, humidity):
        """Returns the ppm of CO2 sensed (assuming only CO2 in the air)
        corrected for temperature/humidity"""
        if self.get_resistance() <= 0 or self.RZERO <=0:
                return self.PARA * math.pow((abs(self.get_corrected_resistance(temperature, humidity))/ abs(self.RZERO)), -self.PARB)
        return self.PARA * math.pow((self.get_corrected_resistance(temperature, humidity)/ self.RZERO), -self.PARB)

    def get_rzero(self):
        """Returns the resistance RZero of the sensor (in kOhms) for calibratioin purposes"""
        return self.get_resistance() * math.pow((self.ATMOCO2/self.PARA), (1./self.PARB))

    def get_corrected_rzero(self, temperature, humidity):
        """Returns the resistance RZero of the sensor (in kOhms) for calibration purposes
        corrected for temperature/humidity"""
        return self.get_corrected_resistance(temperature, humidity) * math.pow((self.ATMOCO2/self.PARA), (1./self.PARB))

def mq135lib_example():
    """MQ135 lib example"""
    # setup
    temperature = 21.0
    humidity = 25.0
    
    mq135 = MQ135(Pin(36)) # analog PIN 0
    print(mq135.get_resistance())
    # loop
    if True:
        rzero = mq135.get_rzero()
        corrected_rzero = mq135.get_corrected_rzero(temperature, humidity)
        resistance = mq135.get_resistance()
        ppm = mq135.get_ppm()
        corrected_ppm = mq135.get_corrected_ppm(temperature, humidity)
        print("MQ135 RZero: " + str(rzero) +"\t Corrected RZero: "+ str(corrected_rzero)+
              "\t Resistance: "+ str(resistance) +"\t PPM: "+str(ppm)+
              "\t Corrected PPM: "+str(corrected_ppm)+"ppm")
        
        time.sleep(0.3)

if __name__ == "__main__":
    mq135lib_example()

