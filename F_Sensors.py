import smbus
import time
from time import strftime, gmtime
import threading
import spidev
import RPi.GPIO as GPIO
import math as math
import datetime as dt

def read_MCP3008_SPI(SPIBus, SPI_device, ADC_Channel, Vref):
    spi = spidev.SpiDev()
    spi.open(SPIBus,SPI_device) #Operating SPI in 'low' state - as such data extracted corresponds to SPI communication where SCLK idles low
    spi.max_speed_hz = 1200000

    assert 0 <= ADC_Channel <=7 #there are 8 channels on the MCP3008
    r = spi.xfer2([1, 8 + ADC_Channel << 4,0])
    msg = ((r[1] & 3) << 8) + r[2] #the data out
    spi.close()
    voltage_ratio = msg / 1024 #per the data sheet for the MCP3008 to provide the LSB Size
    voltage = voltage_ratio * Vref
    return voltage

def R1_resistance_OHM(R2, Vin, Vout): #Used to calculate the first resistor in a voltage divide circuit - used where Vin is too high for Pi
    if Vout != 0:
        R1 = (R2 * (Vin - Vout)) / Vout
        return R1
    else:
        return 0

def R2_resistance_OHM(R1, Vin, Vout):   #Used to calculate the second resistor in a voltage divide circuit
    if Vin - Vout != 0:
        R2 = (R1 * Vout) / (Vin - Vout)
        return R2
    else:
        return 0

def TenK_NTC_Thermistor(R2_resistance):
    #Reistance = Ae^(Beta/T) for standard NTC resistor
    Rref = 10000 #10k Ohm resistor
    Beta = 3977 #For specific thermistor used in this project: https://www.sterlingsensors.co.uk/ntc-thermistor-sensor-with-fixed-process-connection.html
    TRef = 25   #DegC
    Kelvin = 273 #DegC to absolute zero

    #Rearranging formula: A = Resistance/(e^(Beta/T)
    A = Rref / (math.exp(Beta / (TRef + Kelvin)))

    #The thermistor has provided the actual resistance reading being R2_resistance
    #Rearranging formula: T (DegC) = Beta / LN(Resistance/A) - Kelvin
    if R2_resistance/A != 0:
        TempDegC = (Beta / math.log(R2_resistance/A)) - Kelvin
        return TempDegC
    else:
        return 0

def temp_from_MCP3008_10K_NTC_Thermistor(lstArgs):
    SPIBus = lstArgs[0]
    SPIChannel = lstArgs[1]
    MPC3008_Channel = lstArgs[2]
    R1 = 10000 #10k ohm thermistor - worth checking the actual resistance with multi-meter and updating
    Vref = 3.3  #The Raspberry Pi's SPI pins are 3.3V so the supply voltage should also be 3.3V not 5V

    voltage = read_MCP3008_SPI(SPIBus, SPIChannel, MPC3008_Channel, Vref)
    thermistor_resistance = R2_resistance_OHM(R1, Vref, voltage)
    TempDegC = TenK_NTC_Thermistor(thermistor_resistance)
    return TempDegC

'''
def test_NTC():
    boolContinue = True
    lstArgs = [0,0,0]
    while boolContinue == True:
        temp = temp_from_MCP3008_10K_NTC_Thermistor(lstArgs)
        print(temp)
        time.sleep(0.5)

test_NTC()
'''
'''
def test_SPI():
    for i in range(0,2):
        for j in range(0,8):
            lstArgs = [0,i,j]
            temp = temp_from_MCP3008_10K_NTC_Thermistor(lstArgs)
            print('Bus: ' + str(i) + '; channel: ' + str(j) + '; ' + str(temp))
            time.sleep(0.5)

test_SPI()
'''

def PT100_temperature(lstArgs):
    SensorWires = lstArgs[0] #You can get 2 wire, 3 wire and 4 wire PT100 sensors
    Vref = lstArgs[1] #The voltage of the circuit - for Pi this would be 3.3V

    SPIBusSensor = lstArgs[2] #The actual PT100 sensor's SPI bus
    SPIChannelSensor = lstArgs[3] #The actual PT100 sensor's SPI select
    MPC3008_ChannelSensor = lstArgs[4] #The actual PT100 sensor's MCP3008 channel
    R1Sensor = lstArgs[5] #The resistance of the resistor on the circuit board - expected to be 1k Ohms

    SPIBusWire1 = lstArgs[6] #Either the live or ground wire resistance test of the PT100 SPI bus
    SPIChannelWire1 = lstArgs[7] #Either the live or ground wire resistance test of the PT100 SPI select
    MPC3008_ChannelWire1 = lstArgs[8] #Either the live or ground wire resistance test of the PT100 MCP3008 channel
    R1Wire1 = lstArgs[9] #The resistance of the resistor on the circuit board - expected to be 1k Ohms

    SPIBusWire2 = lstArgs[10] #Either the live or ground wire resistance test of the PT100 SPI bus ONLY WHEN 4 WIRE SENSOR USED
    SPIChannelWire2 = lstArgs[11] #Either the live or ground wire resistance test of the PT100 SPI select ONLY WHEN 4 WIRE SENSOR USED
    MPC3008_ChannelWire2 = lstArgs[12] #Either the live or ground wire resistance test of the PT100 MCP3008 channel ONLY WHEN 4 WIRE SENSOR USED
    R1Wire2 = lstArgs[13] #The resistance of the resistor on the circuit board - expected to be 1k Ohms ONLY WHEN 4 WIRE SENSOR USED

    #A PT100 sensor has a resistance of 100 Ohms at 0DegC. Each degree C will increment 0.39Ohms of resistance with positive correlation

    Sensor_Vout = read_MCP3008_SPI(SPIBusSensor, SPIChannelSensor, MPC3008_ChannelSensor, Vref)
    #print(Sensor_Vout)
    Sensor_Resistance = R2_resistance_OHM(R1Sensor, Vref, Sensor_Vout) #The HeatSet circuit board has the sensor as the second resistor in the voltage divider cirucit
    #print('SENS RES:' + str(Sensor_Resistance))

    if SensorWires > 2: #If a 3 or 4 wire sensor is used
        Wire1_Vout = read_MCP3008_SPI(SPIBusWire1, SPIChannelWire1, MPC3008_ChannelWire1, Vref)
        Wire1_Resistance = R2_resistance_OHM(R1Wire1, Vref, Wire1_Vout)
        #print('WIRE RES:' + str(Wire1_Resistance))

    if SensorWires == 3: #If a 3 wire sensor is used
        Sensor_Resistance = Sensor_Resistance - Wire1_Resistance

    if SensorWires == 4: #If a 4 wire sensor is used
        Wire2_Vout = read_MCP3008_SPI(SPIBusWire2, SPIChannelWire2, MPC3008_ChannelWire2, Vref)
        Wire2_Resistance = R2_resistance_OHM(R1Wire2, Vref, Wire2_Vout)
        Sensor_Resistance = Sensor_Resistance - (Wire1_Resistance + Wire2_Resistance)/2

    temperature = (Sensor_Resistance - 100) / 0.39
    return temperature

def PT1000_temperature(lstArgs):
    SensorWires = lstArgs[0] #You can get 2 wire, 3 wire and 4 wire PT100 sensors
    Vref = lstArgs[1] #The voltage of the circuit - for Pi this would be 3.3V

    SPIBusSensor = lstArgs[2] #The actual PT100 sensor's SPI bus
    SPIChannelSensor = lstArgs[3] #The actual PT100 sensor's SPI select
    MPC3008_ChannelSensor = lstArgs[4] #The actual PT100 sensor's MCP3008 channel
    R1Sensor = lstArgs[5] #The resistance of the resistor on the circuit board - expected to be 1k Ohms

    SPIBusWire1 = lstArgs[6] #Either the live or ground wire resistance test of the PT100 SPI bus
    SPIChannelWire1 = lstArgs[7] #Either the live or ground wire resistance test of the PT100 SPI select
    MPC3008_ChannelWire1 = lstArgs[8] #Either the live or ground wire resistance test of the PT100 MCP3008 channel
    R1Wire1 = lstArgs[9] #The resistance of the resistor on the circuit board - expected to be 1k Ohms

    SPIBusWire2 = lstArgs[10] #Either the live or ground wire resistance test of the PT100 SPI bus ONLY WHEN 4 WIRE SENSOR USED
    SPIChannelWire2 = lstArgs[11] #Either the live or ground wire resistance test of the PT100 SPI select ONLY WHEN 4 WIRE SENSOR USED
    MPC3008_ChannelWire2 = lstArgs[12] #Either the live or ground wire resistance test of the PT100 MCP3008 channel ONLY WHEN 4 WIRE SENSOR USED
    R1Wire2 = lstArgs[13] #The resistance of the resistor on the circuit board - expected to be 1k Ohms ONLY WHEN 4 WIRE SENSOR USED

    #A PT1000 sensor has a resistance of 1000 Ohms at 0DegC. Each degree C will increment 0.39Ohms of resistance with positive correlation

    Sensor_Vout = read_MCP3008_SPI(SPIBusSensor, SPIChannelSensor, MPC3008_ChannelSensor, Vref)
    #print(Sensor_Vout)
    Sensor_Resistance = R2_resistance_OHM(R1Sensor, Vref, Sensor_Vout) #The HeatSet circuit board has the sensor as the second resistor in the voltage divider cirucit
    #print('SENS RES:' + str(Sensor_Resistance))

    if SensorWires > 2: #If a 3 or 4 wire sensor is used
        Wire1_Vout = read_MCP3008_SPI(SPIBusWire1, SPIChannelWire1, MPC3008_ChannelWire1, Vref)
        Wire1_Resistance = R2_resistance_OHM(R1Wire1, Vref, Wire1_Vout)
        #print('WIRE RES:' + str(Wire1_Resistance))

    if SensorWires == 3: #If a 3 wire sensor is used
        Sensor_Resistance = Sensor_Resistance - Wire1_Resistance

    if SensorWires == 4: #If a 4 wire sensor is used
        Wire2_Vout = read_MCP3008_SPI(SPIBusWire2, SPIChannelWire2, MPC3008_ChannelWire2, Vref)
        Wire2_Resistance = R2_resistance_OHM(R1Wire2, Vref, Wire2_Vout)
        Sensor_Resistance = Sensor_Resistance - (Wire1_Resistance + Wire2_Resistance)/2

    temperature = (Sensor_Resistance - 1000) / 0.39
    return temperature

'''
def Test_PT100():
    boolTest = True
    while boolTest == True:
        lstTest = [3, 3.3, 0,0,0,1000, 0,0,1,1000, None,None,None,None]
        temperature = PT100_temperature(lstTest)
        print(temperature)
        time.sleep(1)

Test_PT100()
'''

def pressure_5V_via_MCP3008(lstArgs):
    #IMPORTANT: as the Pi's GPIOs are 3.3V a voltage divider is needed to protect the pi
    #Assumed component: 5V PRESSURE TRANSDUCER SENSOR 0 - 175 PSI 0 - 1.2 MPa OIL GAS AIR WATER 0.5-4.5V 1/4"
    #Output voltage: 0.5 - 4.5V DC, Working current: less than or equal to 10 mA
    #A voltage divider is used to step down the maximum 4.5V down to 3.3V as such

    SPIBus = lstArgs[0]
    SPIChannel = lstArgs[1]
    MCP3008_Channel = lstArgs[2]

    Vref = 3.3 #MCP3008 Vref and Vdd when connected to the Pi via SPI
    Vout = read_MCP3008_SPI(SPIBus, SPIChannel, MCP3008_Channel, Vref)
    #print(Vout)
    minVoltage = 0.5 * 10000 / 13600 #0.5V is minimum Vin * R2 (10k Ohm resistor) / (10k Ohm + 3k6 Ohm (R1) resistors)
    maxVoltage = 4.5 * 10000 / 13600 #4.5 is maximum Vin * R2 (10k Ohm resistor) / (10k Ohm + 3k6 Ohm (R1) resistors)
    #print(minVoltage)
    #print(maxVoltage)
    minPressure = 0 #PSI
    maxPressure = 175 #PSI
    fltInterpolatedPSI = minPressure + (((Vout - minVoltage) / (maxVoltage - minVoltage)) * (maxPressure - minPressure))
    fltBar = fltInterpolatedPSI * 0.0689476 #conversion of PSI to bar
    return fltBar

def light_sensor(lstArgs):

    SPIBus = lstArgs[0]
    SPIChannel = lstArgs[1]
    MCP3008_Channel = lstArgs[2]
    Zone_ID = lstArgs[3]

    Vref = 3.3 #MCP3008 Vref and Vdd when connected to the Pi via SPI
    voltage = read_MCP3008_SPI(SPIBus, SPIChannel, MCP3008_Channel, Vref)
    #print(voltage)
    R1_ohm = R1_resistance_OHM(10000, Vref, voltage) #Resistor 2 on HeatSet PCB = 10k ohm    #print(R1_ohm)
    #print(R1_ohm)
    Resistance_ON = 2000 #The resistance of the photoresistor will be different for different LED lights so this needs to be calbirated but need not be exact
    if R1_ohm >= Resistance_ON: #Photo resistors have a lower resistance with greater light intensity
        return Zone_ID + 1 #The graph will plot a straight line against each zone
    else:
        return 0

def run_sensors(dictGlobalInstructions):
    #time.sleep(20)
    BMS_GUI = dictGlobalInstructions['General_Inputs']['GUI_BMS']
    BMS_thread_lock = dictGlobalInstructions['Threads']['BMS_thread_lock']
    lstInclude = ['Solar_Thermal', 'Heat_Pump', 'PV', 'Battery', 'Zone']
    lstTech = ['Solar_Inputs', 'HP_Inputs', 'PV_Inputs', 'BAT_Inputs', 'ZONE_Inputs']

    for i in range(0,len(lstTech)):
        if dictGlobalInstructions['User_Inputs'][lstInclude[i]] == True: #If the technology is included
            #print(lstTech[i])
            for key in dictGlobalInstructions[lstTech[i]]['GUI_Information']: #For each sensor, pulse meter, derived value or other relevant metric
                if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Include?'] == True: #If the item is included
                    if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Sensor'] == True: #If the item selected is a sensor
                        strInterfaceFunction = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Interface_function'] #The function to read the sensor. This is user defined allowing for alternative approaches - the default is the HeatSet PCB that uses an analog 10k thermistor
                        lstArgs = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Interface_args'] #The arguments for the function
                        lstArgs.append([dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['ID']])
                        #print(dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['ID'])
                        #print(strInterfaceFunction)
                        #print(lstArgs)
                        time.sleep(0.005) #Wait 5 microseconds (allowing the MCP3008 to complete A2D conversion)
                        fltOutput = globals()[strInterfaceFunction](lstArgs) #Run the function to get a float output
                        if i == 4: #For Zone outputs
                            if fltOutput > 0:
                                fltOutput = "ON"
                            else:
                                fltOutput = "OFF"
                        dtReadTime = dt.datetime.now() #Record the current time

                        if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Minute_Average'] == None: #If this is the first read on GUI initialisation
                            lstLastMinute = [False, fltOutput, fltOutput] #Assume the sensor reading was the same at GUI launch and the first read (probably only a few microseconds difference in read times)
                            lstTimes = [False, BMS_GUI.time_created, dtReadTime] #Record the read times
                        else: #If this is not the first time a reading has been made
                            BMS_thread_lock.acquire(True)
                            lstLastMinute = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Minute_Average']
                            lstTimes = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Sensor_Read_Times']
                            BMS_thread_lock.release()

                            if lstLastMinute[0] == True: #The first 'bit' of the list is set by D_Database as to whether the minute's data has or has not been taken
                                lstReadingVal = lstLastMinute[len(lstLastMinute)-1] #Take the last reading of the previous minute
                                lstLastMinute = [False, lstReadingVal, fltOutput] #Transfer the last reading to the current minute's list and add the new reading
                                lstReadingTime = lstTimes[len(lstTimes)-1] #Take the last reading's time from teh previous minute
                                lstTimes = [False, lstReadingTime, dtReadTime]
                            else:
                                lstLastMinute.append(fltOutput)
                                lstTimes.append(dtReadTime)

                        BMS_thread_lock.acquire(True)
                        dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Minute_Average'] = lstLastMinute
                        dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Sensor_Read_Times'] =  lstTimes
                        BMS_thread_lock.release()
                        #print(fltOutput)
                        #print(lstLastMinute)
                        #Update GUI for collector temperature
                        strOutput = str(fltOutput)
                        lstGUIIncluded = dictGlobalInstructions[lstTech[i]]['GUI_Sections'][0]
                        ID = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['ID']
                        for j in range(0,len(lstGUIIncluded)):
                            if lstGUIIncluded[j] == ID:
                                dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['GUI_Val'].config(text=strOutput[:5])