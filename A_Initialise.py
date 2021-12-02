import RPi.GPIO as GPIO
from time import strftime, gmtime
from PIL import Image, ImageTk
import datetime as dt

#############################################
'''USER DEFINED PARAMETERS'''
#############################################

#Core energy generation/storage in building
boolSolar = True            #Set to true if you are using solar thermal
boolSolarControl = False    #NOT USED BUT DO NOT CHANGE (setting to TRUE will amend the solar thermal GUI to a control GUI that has not been tested or fully developed)
boolHeatPump = True         #Set to true if you are using a heat pump
boolHeatPumpControl = False #NOT USED BUT DO NOT CHANGE
boolPV = True               #Set to true if you are using photo-voltaic panels
boolBattery = True          #Set to true if you are using domestic batteries
MainsVoltage = 230          #No longer used

#Location of code on Pi
dbLoc = '/media/HeatSet_data/' #USE A USB FLASHDRIVE. YOU NEED TO MOUNT THE USB CORRECTLY: SEE https://www.raspberrypi-spy.co.uk/2014/05/how-to-mount-a-usb-flash-disk-on-the-raspberry-pi/
fileLoc = '/home/pi/Documents/Home_BMS/'

#I2C
I2C_ADC_Address = 0x08      #No longer used

#Solar thermal related
boolPressurised = True      #If you are using a pressurised system (i.e. the solar loop is closed) then set to True - this will impact whether a pressure reading should be taken
boolImmersion = True        #If your solar tank has an immersion heater element that you want to be controlled by the PI set to True
SolarFlowPipeIDMM = 15      #No longer used
glycol_mix = 25             #Percentage expressed not in demical format e.g. 45% should be entered as 45 not 0.45
Solar_flow_meter_pulse_rate = 0.25    #Litres of water for each pulse sent
Solar_thermal_volume_L = 1.9    #No longer used
Heat_Pump_LperS = 31.8         #No longer used
pump_voltage = 230          #No longer used
solar_coil_loc = 0          #0 = bottom, 1 = mid, 2 = top

#HP related
PipeOutletDiameterMM = 15   #Internal diameter of outlet pipe from heat pump where temperature and flow rate measurements taken
boolHPTank = True           #If you are using a thermal store that is heated by the HP then set to True
HPThermalCapacity = 13      #No longer used
HPVoltage = 230             #No longer used
HP_flow_meter_pulse_rate = 1    #Litres of water for each pulse sent
HP_PHEx_L = 0.75            #No longer used
HP_glycol_mix = 25             #Percentage expressed not in demical format e.g. 45% should be entered as 45 not 0.45
Include_internal_unit_in_COP = False #Only include the internal unit if the system is calibrated to measure flow temperature that can be influenced by the internal unit

#PV related
PVArrayMaxOutputW = 1800     #No longer used

#Battery related
VoltageAtFullCharge = 13    #No longer used
VoltageAtMinCharge = 11.5   #No longer used
InverterVoltageToBAT = 9    #No longer used

#Screen measurements
lngScreenHeight = 480 #Pixel height of screen used to display the GUI
lngScreenWidth = 800 #Pixel width of screen used to display the GUI

#GPIO SET UP
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

#Sensor wiring and data reading
#If sensor or derived value then list[1] == F_Sensors/H_Derived_Values function with list[2:] being function arguments
#If pulse meter then list[1] == GPIO Pin for pulse input
lstSolarSensors = [['DictID=0','temp_from_MCP3008_10K_NTC_Thermistor', 0,0,0],      #COLLECTOR SPIBus, SPISelect 0, MCP3008 Channel 0
                    ['DictID=1','temp_from_MCP3008_10K_NTC_Thermistor', 0,0,1],     #TANK (MID) SPIBus, SPISelect 0, MCP3008 Channel 1
                    ['DictID=2','temp_from_MCP3008_10K_NTC_Thermistor', 0,0,2],     #TANK (TOP) SPIBus, SPISelect 0, MCP3008 Channel 2
                    ['DictID=3','temp_from_MCP3008_10K_NTC_Thermistor', 0,0,3],     #TANK (BOTTOM) SPIBus, SPISelect 0, MCP3008 Channel 3
                    ['DictID=4','pressure_5V_via_MCP3008',0,1,0],               #Pressure gauge: SPI Bus 0, SPI Select 1, MCP3008 channel 0
                    ['DictID=5',None,None,None,None],                           #Not sensor or derived value
                    ['DictID=6',None,None,None,None],                           #Not sensor or derived value
                    ['DictID=7',None,None,None,None],                           #Not sensor or derived value
                    ['DictID=8',None,None,None,None],                           #Not sensor or derived value
                    ['DictID=9',None,None,None,None],                           #Not sensor or derived value
                    ['DictID=10',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=11',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=12',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=13',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=14',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=15',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=16',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=17',None,None,None,None],                          #Not sensor or derived value
                    ['DictID=18',None,None,None,None],                          #Derived value but derived via D_Database.Solar_Guage.
                    ['DictID=19',None,None,None,None],                          #Heat_load: Not sensor or derived value - populated on each pulse of the flow meter
                    ['DictID=20', 4, Solar_flow_meter_pulse_rate],              #GPIO pin for pulse read, litres per pulse, heat load dictionary to store heat transfer on each pulse, glycol_mix, strFlowKey, strCollectorKey, strTankKey
                    ['DictID=21', 17, 1]]                                       #GPIO for electricity meter pulse (solar pump), Wh per pulse (https://www.camax.co.uk/downloads/A100C-Datasheet.pdf)

lstHPSensors = [['DictID=0','temp_from_MCP3008_10K_NTC_Thermistor', 0,0,4],     #HP OUTLET: SPIBus, SPISelect 0, MCP3008 Channel 4
                ['DictID=1','temp_from_MCP3008_10K_NTC_Thermistor', 0,0,5],     #HP INLET: SPIBus, SPISelect 0, MCP3008 Channel 5
                ['DictID=2', 27, HP_flow_meter_pulse_rate],                     #Flow meter: GPIO Pin, L/pulse
                ['DictID=3',None,None,None,None],                               #Derived heat capacity at point in time of HP (Wth)
                ['DictID=4', 22, 1],                                            #External Unit electricity consumption: GPIO for electricity meter pulse (), Wh per pulse (https://www.camax.co.uk/downloads/A100C-Datasheet.pdf)
                ['DictID=5','temp_from_MCP3008_10K_NTC_Thermistor', 0,0,1],     #TANK (MID) SPIBus, SPISelect 0, MCP3008 Channel 1
                ['DictID=6',None,None,None,None],                               #Not sensor or derived value
                ['DictID=7',None,None,None,None],                               #'tech_heat_load_duration', 'HP_Inputs', glycol_mix, 'Outlet_Temperature', 'Inlet_Temperature', 'Heat_load', HP_PHEx_L],                               #Heat_load: Not sensor or derived value - populated on each pulse of the flow meter
                ['DictID=8','HP_External_Internal_Watts_from_Wh', 'Internal_Unit_Elec_Wh','External_Unit_Elec_Wh', 'HP_Inputs', 'Pulse_Minute_Readings', 'Pulse_reading_times'],        #Electricity input into HP at point in time We
                ['DictID=9', 5, 1],                                             #Internal unit electricity consumption: GPIO for electricity meter pulse (Heat Pump), Wh per pulse (https://www.camax.co.uk/downloads/A100C-Datasheet.pdf)
                ['DictID=10','pressure_5V_via_MCP3008',0,1,1]]                  #Pressure gauge: SPI Bus 0, SPI Select 1, MCP3008 channel 0

lstPVSensors = [['DictID=0',None,None,None,None],                               #Dervied We output
                ['DictID=1', 19, 1]]                                            #GPIO for electricity meter pulse (import), Wh per pulse (https://www.camax.co.uk/downloads/A100C-Datasheet.pdf)

lstBATSensors = [['DictID=0', 'Watts_from_Wh', 'Discharge_Supply', 'BAT_Inputs', 'Pulse_Minute_Readings', 'Pulse_reading_times'],             #Electrical instantaneous supply (We) on discharge
                ['DictID=1', 6, 1],                                            #GPIO for electricity meter pulse (export), Wh per pulse (https://www.camax.co.uk/downloads/A100C-Datasheet.pdf)
                ['DictID=2', 'Watts_from_Wh', 'Charge_Supply', 'BAT_Inputs','Pulse_Minute_Readings', 'Pulse_reading_times'],                 #Export from inverter to house
                ['DictID=3', 13, 1]]                                            #GPIO for electricity meter pulse (import), Wh per pulse (https://www.camax.co.uk/downloads/A100C-Datasheet.pdf)

#For pulse meter mapping to Obems C++ server
lstObemsHeatSet_GPIOMap = [['Solar_Inputs', 20, 'pc00'], #Solar flow meter, [Technolgy type, ID in GUI information, Obems server command]
                            ['Solar_Inputs',21, 'pc01'], #Solar electricity sub-meter
                            ['HP_Inputs', 2, 'pc02'], #HP flow meter
                            ['HP_Inputs', 4, 'pc03'], #HP external unit electricity sub-meter
                            ['HP_Inputs', 9, 'pc04'], #HP internal unit electricity sub-meter
                            ['BAT_Inputs', 1, 'pc05'], #Battery discharge electricity sub-meter
                            ['BAT_Inputs', 3, 'pc06'], #Battery charge electricity sub-meter['PV_Inputs', 1, 'pc07']] #PV electricity generation sub-meter
                            ['PV_Inputs', 1, 'pc07']] #PV array measured output

#############################################
'''COMMON SYSTEM PARAMETERS DO NOT ADJUST'''
#############################################
dictUser = {'Solar_Thermal': boolSolar,
                        'Solar_Control': boolSolarControl,
                        'Solar_Coil_Location': solar_coil_loc,
                        'Heat_Pump': boolHeatPump,
                        'Heat_Pump_Control': boolHeatPumpControl,
                        'PV': boolPV,
                        'Battery': boolBattery,
                        'DB_Location': dbLoc,
                        'Code_Location': fileLoc,
                        'Pressurised': boolPressurised,
                        'Solar_IntDiam_FlowPipe': SolarFlowPipeIDMM,
                        'Glycol_Mix': glycol_mix,
                        'HP_Glycol_Mix': HP_glycol_mix,
                        'Solar_meter_flow_rate': Solar_flow_meter_pulse_rate,
                        'HP_IntDiam_OutletPipe': PipeOutletDiameterMM,
                        'HP_Tank': boolHPTank,
                        'HP_Thermal_Capacity': HPThermalCapacity,
                        'HP_Operating_Voltage': HPVoltage,
                        'HP_meter_flow_rate': HP_flow_meter_pulse_rate,
                        'Include_internal_unit_in_COP': Include_internal_unit_in_COP,
                        'PV_Max_Output': PVArrayMaxOutputW,
                        'BAT_Voltage_At_Full_Charge': VoltageAtFullCharge,
                        'BAT_Voltage_At_Min_Charge': VoltageAtMinCharge,
                        'OBEMS': lstObemsHeatSet_GPIOMap}

dictTimeStamp = {'SQL_Table': None,
                        'SQL_Title': 'Time Stamp',
                        'GUI_Label': 'Last update',
                        'GUI_Val': None,
                        'GUI_Default': dt.datetime.now()}

#GUI common values
strFont = "Helvetica"
bytFontSize = 10

lngScreenDesignHeight = 480 #The pixel height that the GUI was designed to
lngScreenDesignWidth = 800 #The pixed width that the GUI was deisnged to

lngScreenHeightADJ = lngScreenHeight / lngScreenDesignHeight
lngScreenWidthADJ = lngScreenWidth / lngScreenDesignWidth

frmLogoHeightDefault = 50
frmLogoWidthDefault = 400
frmLogoHeight = frmLogoHeightDefault * lngScreenHeightADJ
frmLogoWidth = frmLogoWidthDefault * lngScreenWidthADJ
frmLogo_x = 0
frmLogo_y = 0

lngImgWidthDefault = 160
lngImgHeightDefault = 50
lngImgWidth = int(lngImgWidthDefault * lngScreenWidthADJ)
lngImgHeight = int(lngImgHeightDefault * lngScreenHeightADJ)

intInchToPixelRatio = 96 #96 pixels to 1 inch

dictCommonGUIParams = {'GUI_BMS': None,
                        'Time_Stamp': dictTimeStamp,
                        'Screen_Height': lngScreenHeight,
                        'Screen_Width': lngScreenWidth,
                        'Font': strFont,
                        'Font_size': bytFontSize,
                        'Height_ADJ': lngScreenHeightADJ,
                        'Width_ADJ': lngScreenWidthADJ,
                        'Logo_height': frmLogoHeight,
                        'Logo_width': frmLogoWidth,
                        'Logo_x': frmLogo_x,
                        'Logo_y': frmLogo_y,
                        'DB_Name': 'HeatSetDB_'}

dictThreads = {'BMS_thread_lock': None,
                'Time_Thread': None,
                'Pump_Thread': None,
                'Sensors_Thread': None,
                'DB_Graph_Thread': None,
                'Derived_Values_Thread': None,
                'Gauge_Thread': None,
                'Plot_reset_thread': None,
                'Flow_threads': [],
                'Obems_Execute': None}

#Initialise GPIOs
GPIO.setmode(GPIO.BCM)

#############################################
'''SOLAR SYSTEM PARAMETERS'''
#############################################

#Solar GPIO pin logic
if boolSolarControl == True:
    #IF YOU WANT TO USE THIS SECTION YOU WILL NEED TO REALIGN THE PINS AS THE CURRENT HEATSET PCB HAS BEEN DESIGNED FOR MONITORING ONLY
    GPIOSolarPump = 5 #GPIO 5: Pump;
    GPIOFlushValve = 6 #GPIO 6: System Flush - linked to a motorised valve allowing for emmergency flush to avoid pipe freezing
    GPIOImmersion = 13 #GPIO 13: Immersion heater
    GPIOFlowMeter = 19 #GPIO 19: Solar Flow meter
    lstSolarRelayGPIOs = [GPIOSolarPump, GPIOFlushValve, GPIOImmersion]
    GPIO.setup(lstSolarRelayGPIOs, GPIO.OUT) #Set the GPIOs as outputs rather than inputs
    GPIO.output(lstSolarRelayGPIOs,GPIO.HIGH) #The power relay switches items ON when the GPIO does not provide 3.3v - default position is to start with powered devices off

    dictSolarGPIOs = {'Solar_Pump': GPIOSolarPump,
                        'Emergency_Flush_Valve': GPIOFlushValve,
                        'Immersion_Heater': GPIOImmersion,
                        'Flow_meter': GPIOFlowMeter} #only the power relay is controlled via general GPIOs - all sensors are managed through the A2D board
else:
    dictSolarGPIOs = []

#Solar Thermal parameters
bytMaxTemp = 80 #0. Maximum temperature of the panel or tank
bytMinTemp = 2 #1. Temperature at which the system should be flushed
bytTargetTemp = 40 #2. Target temperature of the collector
bytDeltaT = 15 #3. The temperature differential between the collector and tank. The higher the DeltaT the better the heat transfer; however, if set too high the collector may never reach the temperature - the system will auto-correct the target temperature down; however, the delta T variable will stay constant
bytTempInc = 1 #4. Temperature increment in the event of either the algorithm increasing or decreasing the target temperature
bytPumpLastOnCheckWithTurnOn = 60 #5. minutes since last pump on and now going to switch pump on
bytPumpLastOnCheckStillOff = 30 #6. minutes since last pump on and pump still off as collector not hot enough
bytHrLightOn = 8 #7. Hour that light is first expected
bytHrLightOff = 17 #8. Hour that light is expected to end
bytTargetChangeWaitM = 30 #9. The number of minutes that should elapse before the target temperature is adjusted
dblLossADJ = 0.2 #10 The % applied to the delta T to assess at what point to stop pumping and sufficient heat transfer has been achieved
bytReadAvCount = 15 #11 Sensor readings will vary by approximately +/-0.5DegC on each reading as such need to take an average of readings. This is the number of loops the system will take an average over to make decisions and roughly equates to seconds.
dblMinPressure = 1.5 #12 Minimum system pressure expressed in bars.
dblMaxPressure = 3.0 #12 Minimum system pressure expressed in bars.
lstImmDefault = ['01:00', '02:30'] #Default start time is 1am and off at 2.30am.
imgSolarLogo = fileLoc + "LOGO.png" #location of the Heat Set logo

#SQL TABLE
strSolarSQLTable = 'SOLAR'

dictSolarDefaults = {'Logo': imgSolarLogo,
                        'Max_temp': bytMaxTemp,
                        'Min_temp': bytMinTemp,
                        'Target_temp': bytTargetTemp,
                        'Delta_T': bytDeltaT,
                        'Temp_increment': bytTempInc,
                        'PumpOn_lookback': bytPumpLastOnCheckWithTurnOn,
                        'PumpOff_lookback': bytPumpLastOnCheckStillOff,
                        'First_light_hr': bytHrLightOn,
                        'Last_light_hr': bytHrLightOff,
                        'Time_lapse_b4_temp_change': bytTargetChangeWaitM,
                        'DeltaT_loss_percent': dblLossADJ,
                        'Temp_reading_count': bytReadAvCount,
                        'Min_pressure': dblMinPressure,
                        'Max_pressure': dblMaxPressure,
                        'Immersion_default_times': lstImmDefault,
                        'Database_Table_Name': strSolarSQLTable,
                        'Last_Pump': strftime("%d/%m/%Y %H:%M:%S", gmtime()),
                        'Analog_interface_class': 'analog_measurement',
                        'Control_interface_class': 'RESOL'}

#GUI Lists
lstOnOff = ['ON','OFF']
lstMODEs = ['SYSTEM', 'MANUAL']
lstPressureStatus = ['OK', 'TOO LOW']
lstFlushMode = ['Open', 'Closed']
dictCommmands = {'On_Off': lstOnOff, 'Solar_modes': lstMODEs, 'Pressure_status': lstPressureStatus, 'Flush_Status': lstFlushMode}

#SOLAR GUI OBJECTS:
#Sensor dictraries
#ID, SQL_Title - database column title, GUI_Label - description used in GUI, GUI_Val - the python reference to the label - populated when the GUI is built
dictCollectorSensor = {'ID': 0,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Collector_Temp_DegC',
                        'GUI_Label': 'Collector Temperature (DegC)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Pulse_Meter': False,
                        'Interface_function': lstSolarSensors[0][1], #Function stored in F_Sensors
                        'Interface_args': lstSolarSensors[0][2:], #Arguments for the required function
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 1,
                        'Plot_colour': 'red',
                        'Plot_label': 'Collector',
                        'Derived_Val': False}
dictTankMidSensor = {'ID': 1,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Tank_Mid_Temp_DegC',
                        'GUI_Label': 'Tank Mid Temperature (DegC)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Pulse_Meter': False,
                        'Interface_function': lstSolarSensors[1][1], #Function stored in F_Sensors
                        'Interface_args': lstSolarSensors[1][2:], #Arguments for the required function
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 2,
                        'Plot_colour': 'blue',
                        'Plot_label': 'Tank_Mid',
                        'Derived_Val': False}
dictTopTankSensor = {'ID': 2,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Tank_Top_Temp_DegC',
                        'GUI_Label': 'Tank Top Temperature (DegC)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Pulse_Meter': False,
                        'Interface_function': lstSolarSensors[2][1], #Function stored in F_Sensors
                        'Interface_args': lstSolarSensors[2][2:], #Arguments for the required function
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 3,
                        'Plot_colour': 'green',
                        'Plot_label': 'Tank_Top',
                        'Derived_Val': False}
dictBotTankSensor = {'ID': 3,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Tank_Bottom_Temp_DegC',
                        'GUI_Label': 'Tank Bottom Temperature (DegC)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Pulse_Meter': False,
                        'Interface_function': lstSolarSensors[3][1], #Function stored in F_Sensors
                        'Interface_args': lstSolarSensors[3][2:], #Arguments for the required function
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 4,
                        'Plot_colour': 'purple',
                        'Plot_label': 'Tank_Bottom',
                        'Derived_Val': False}
dictPressureSensor = {'ID': 4,
                        'Include?': boolPressurised,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Pressure_bar',
                        'GUI_Label': 'System pressure (bar)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Pulse_Meter': False,
                        'Interface_function': lstSolarSensors[4][1], #Function stored in F_Sensors
                        'Interface_args': lstSolarSensors[4][2:], #Arguments for the required function
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None,
                        'Derived_Val': False}
dictFlowSensor = {'ID': 20,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Flow_Rate_L', #The extracted value is absolute litres to the SQL database so that the average L/Min can be derived
                        'GUI_Label': 'Flow Rate (L/Hr)',#For the GUI the derived L/Hr is shown as a flow rate - this is done in D_Database
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_GPIO': lstSolarSensors[20][1],
                        'Pulse_Minute_Readings': None,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstSolarSensors[20][2],
                        'Pulse_calc_flow': True,
                        'Pulse_calc_flow_load_dict': None,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None,
                        'Derived_Val': False}
dictSolarPumpElectrictyLoad = {'ID':21,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Pump_Electricity_Wh',
                        'GUI_Label': 'Pump electricity consumption (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': 0,
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstSolarSensors[21][2],
                        'Pulse_calc_flow': False,
                        'Pulse_calc_flow_load_dict': None,
                        'Pulse_GPIO': lstSolarSensors[21][1],
                        'Pulse_Minute_Readings': None,
                        'Derived_Val': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}
#Powered item dictraries
dictSolarPump = {'ID': 5,
                        'Include?': boolSolarControl,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Pump_status',
                        'GUI_Label': 'Pump on/off',
                        'GUI_Val': None,
                        'cmd_Val': None,
                        'cmd_def': None,
                        'GUI_Default': lstOnOff[1],
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictImmersion = {'ID': 6,
                        'Include?': boolImmersion,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Immersion_status',
                        'GUI_Label': 'Immer.on/off',
                        'GUI_Val': None,
                        'cmd_Val': None,
                        'cmd_def': None,
                        'GUI_Default': lstOnOff[1],
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictFlushValve = {'ID': 7,
                        'Include?': boolSolarControl,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Flush_valve',
                        'GUI_Label': 'Flush system',
                        'GUI_Val': None,
                        'cmd_Val': None,
                        'cmd_def': None,
                        'GUI_Default': lstOnOff[1],
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}

#System status dictraries
dictSysMode = {'ID':8, 'Include?': boolSolarControl,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'System_Mode',
                        'GUI_Label': 'System Mode',
                        'GUI_Val': None,
                        'cmd_count':1,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1': None,
                        'GUI_Default': lstMODEs[0],
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictImmersionStart = {'ID':9,
                        'Include?': boolImmersion,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Immersion_Start_Time',
                        'GUI_Label': 'Immersion start',
                        'GUI_Val': None,
                        'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': lstImmDefault[0],
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictImmersionEnd = {'ID':10,
                        'Include?': boolImmersion,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Immersion_End_Time',
                        'GUI_Label': 'Immersion end',
                        'GUI_Val': None,
                        'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': lstImmDefault[1],
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictMaxPressure = {'ID':11,
                        'Include?': boolPressurised,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Maximum_Pressure_bar',
                        'GUI_Label': 'Maximum pressure (bar)',
                        'GUI_Val': None, 'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': str(dblMaxPressure),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictPressureOK = {'ID':12,
                        'Include?': boolPressurised,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Pressure_Status',
                        'GUI_Label': 'Pressure status',
                        'GUI_Val': None,
                        'GUI_Default': lstPressureStatus[1],
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}

#System Targets
dictTargTemp = {'ID':13,
                        'Include?': boolSolarControl,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Target_Temperature_DegC',
                        'GUI_Label': 'Target temp (DegC)',
                        'GUI_Val': None, 'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': str(bytTargetTemp),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictMaxTemp = {'ID':14,
                        'Include?': boolSolarControl,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Max_sys_Temperature_DegC',
                        'GUI_Label': 'Max tank temp (DegC)',
                        'GUI_Val': None, 'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': str(bytMaxTemp),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictMinTemp = {'ID':15,
                        'Include?': boolSolarControl,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Min_Collector_Temperature_DegC',
                        'GUI_Label': 'Min collector temp (DegC)',
                        'GUI_Val': None,
                        'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': str(bytMinTemp),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictDeltaT = {'ID':16,
                        'Include?': boolSolarControl,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Target_DeltaT_DegC',
                        'GUI_Label': 'Target DeltaT (DegC)',
                        'GUI_Val': None,
                        'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': str(bytDeltaT),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictMinPressure = {'ID':17,
                        'Include?': boolPressurised,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Minimum_Pressure_bar',
                        'GUI_Label': 'Minimum pressure (bar)',
                        'GUI_Val': None, 'cmd_count':2,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': str(dblMinPressure),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}
dictSolarHeatCapacity = {'ID':18,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Heat_capacity_of_array_Wth',
                        'GUI_Label': 'Thermal capacity over prev hr (Wth)',
                        'GUI_Val': None,
                        'GUI_Default': 0,
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True, #Managed through D_Database.Solar_Gauge
                        'Derived_Val_Function': lstSolarSensors[18][1], #Function stored in F_Sensors,
                        'Derived_Val_Function_Args': lstSolarSensors[18][2:], #Arguments for the required function
                        'Derived_Minute_Average': None,
                        'Derived_total?': False,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}
dictSolarHeatLoad = {'ID':19,
                        'Include?': True,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'Heat_load_over_hour_Wh',
                        'GUI_Label': 'Heat transferred to tank during day (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': 0,
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True,
                        'Derived_Val_Function': None, #Function stored in H_Deived_Values,
                        'Derived_Val_Function_Args': None, #Arguments for the required function
                        'Derived_Minute_Average': None,
                        'Derived_total?': True,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': True,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}

#GLOBAL dictRARY FOR GUI OBJECTS
dictGlobalGUI = {'Collector_temp': dictCollectorSensor,
                        'Tank_temp': dictTankMidSensor,
                        'Tank_top_temp': dictTopTankSensor,
                        'Tank_bot_temp': dictBotTankSensor,
                        'Flow_Rate': dictFlowSensor,
                        'SYS_Pressure': dictPressureSensor,
                        'Solar_pump_electricity': dictSolarPumpElectrictyLoad,
                        'Solar_Pump': dictSolarPump,
                        'Immersion_heater': dictImmersion,
                        'Flush_Valve': dictFlushValve,
                        'System_mode': dictSysMode,
                        'Immersion_start': dictImmersionStart,
                        'Immersion_end': dictImmersionEnd,
                        'Pressure_Status': dictPressureOK,
                        'Target_temperature': dictTargTemp,
                        'Max_Temp': dictMaxTemp,
                        'Min_Temp': dictMinTemp,
                        'Target_DeltaT': dictDeltaT,
                        'Min_pressure': dictMinPressure,
                        'Max_pressure': dictMaxPressure,
                        'Heat_capacity': dictSolarHeatCapacity,
                        'Heat_load': dictSolarHeatLoad}

#This section allows for different items to be included on the GUI - some GUI values must be retained for derived calcualtions
if boolSolarControl == True:
    lstGUISensorNoADJ = [13, 0, 3, 1, 2, 20, 5, 6, 7, 12, 4] #Measured values on the GUI so not adjusted by the user
else:
    lstGUISensorNoADJ = [0, 3, 1, 2, 20, 18, 19, 4, 21] #Measured values on the GUI so not adjusted by the user

lstGUISensorADJ = [8, 14, 15, 16, 17, 11, 9, 10,] #Target values on the GUI that the user can adjust with up down arrows
lstGUISections = [lstGUISensorNoADJ, lstGUISensorADJ]

#SOLAR TAB SIZING
if boolSolarControl == True:
    frmSolarSensorsHeightDefault = 190
else:
    frmSolarSensorsHeightDefault = 150
frmSolarSensorsWidthDefault = frmLogoWidthDefault
frmSolarSensorsHeight = frmSolarSensorsHeightDefault * lngScreenHeightADJ
frmSolarSensorsWidth = frmSolarSensorsWidthDefault * lngScreenWidthADJ
frmSolarSensors_x = 0
frmSolarSensors_y = frmLogoHeight

dictSolarSensors = {'SensorFm_height': frmSolarSensorsHeight,
                        'SensorFm_width': frmSolarSensorsWidth,
                        'Sensor_x': frmSolarSensors_x,
                        'Sensor_y': frmSolarSensors_y}

frmSolarGraphHeight = lngScreenHeight
frmSolarGraphWidth = lngScreenWidth - frmLogoWidth
frmSolarGraph_x = frmSolarSensorsWidth
frmSolarGraph_y = 0

lstTankPlot = [[0,0]]
lstCollectorPlot = [[0,0]]
dictSolarGraph = {'GraphFm_height': frmSolarGraphHeight,
                        'GraphFm_width': frmSolarGraphWidth,
                        'Graph_x': frmSolarGraph_x,
                        'Graph_y': frmSolarGraph_y}

frmSolarSYSHeightDefault = lngScreenDesignHeight - frmSolarSensorsHeightDefault - frmLogoHeightDefault
frmSolarSYSWidthDefault = frmLogoWidthDefault
frmSolarSYSHeight = frmSolarSYSHeightDefault * lngScreenHeightADJ
frmSolarSYSWidth = frmSolarSYSWidthDefault * lngScreenWidthADJ
frmSolarSYS_x = 0
frmSolarSYS_y = frmLogoHeight + frmSolarSensorsHeight

dictSolarSYS = {'SYSFm_height': frmSolarSYSHeight, 'SYSFm_width': frmSolarSYSWidth, 'SYS_x': frmSolarSYS_x, 'SYS_y': frmSolarSYS_y}
dictSolarGauge = {'Fm_height': frmSolarSYSHeight, 'Fm_width': frmSolarSYSWidth, 'Gauge_x': frmSolarSYS_x, 'Gauge_y': frmSolarSYS_y}
dictSolarGUIParams = {'Sensor_Section': dictSolarSensors, 'System_Section': dictSolarSYS, 'Gauge_Section': dictSolarGauge,'Graph_Section': dictSolarGraph}

#SOLAR GRAPH
frm_Solar_Graph_bd = 1
bx_Solar_Graph_width = frmSolarGraphWidth
bx_Solar_Graph_height = frmSolarGraphHeight-40
bx_Solar_Graph_x0 = 0
bx_Solar_Graph_y0 = 0
tm_Solar_Graph_length = 5 #pixel length of the minor tm line
tm_Solar_Graph_major_length = 10 #pixel length of the major tm line
tm_Solar_Graph_x_count = 24*2 #Show tickmarks each half hour
tm_Solar_Graph_x_major = 2 #Show major tm on the hour
Solar_Graph_x_max = 24 #maximum value of x axis is 24th hour
Solar_Graph_x_min = 0 #minimum value on the x axis in the 0th hour
tm_Solar_Graph_y_count = 150 #Show a tm for each DegC
tm_Solar_Graph_y_major= 5 #Show major tm for every 5 DegC
Solar_Graph_y_max = 150 #Maximum temperature on y-axis is 150 Degrees celcius
Solar_Graph_y_min = 0 #Minimum temperature on y-axisis 0 DegC
frm_Solar_Graph_title = 'Solar tank & collector temperatures: ' + strftime("%d/%m/%Y", gmtime())
boolGrid_Solar_Graph = True
Solar_Graph_x_title = 'Time (hour of day)'
Solar_Graph_y_title = 'Degrees Celcius'

dict_Solar_Graph_Frame_Dims = {'frm_width': frmSolarGraphWidth,
                                'frm_height': frmSolarGraphHeight,
                                'frm_bd': frm_Solar_Graph_bd,
                                'bx_width': bx_Solar_Graph_width,
                                'bx_height': bx_Solar_Graph_height,
                                'bx_x0': bx_Solar_Graph_x0,
                                'bx_y0': bx_Solar_Graph_y0}
dict_Solar_Graph_Values = {'include_grid': boolGrid_Solar_Graph,
                                'graph_x_title': Solar_Graph_x_title,
                                'graph_x_max': Solar_Graph_x_max,
                                'graph_x_min': Solar_Graph_x_min,
                                'graph_y_title': Solar_Graph_y_title,
                                'graph_y_max': Solar_Graph_y_max,
                                'graph_y_min': Solar_Graph_y_min,
                                'tm_length': tm_Solar_Graph_length,
                                'tm_x_count': tm_Solar_Graph_x_count,
                                'tm_x_major': tm_Solar_Graph_x_major,
                                'tm_y_count': tm_Solar_Graph_y_count,
                                'tm_y_major': tm_Solar_Graph_y_major,
                                'tm_major_length': tm_Solar_Graph_major_length,
                                'frm_title':frm_Solar_Graph_title}
dict_Solar_Graph_Instructions = {'Dimensions': dict_Solar_Graph_Frame_Dims, 'Values': dict_Solar_Graph_Values}

#SOLAR THERMAL OUTPUT GAUGE (WHEN SOLAR CONTROL = FALSE)
frm_Solar_Gauge_bd = 1
bx_Solar_Gauge_width = frmSolarSYSWidth
bx_Solar_Gauge_height = frmSolarSYSWidth #the box height needs to be the same height as the width as this is to draw a full circle
bx_Solar_Gauge_x0 = 0
bx_Solar_Gauge_y0 = 0
tm_Solar_Gauge_length = 5
tm_Solar_Gauge_major_length = 10
tm_Solar_Gauge_count = 200
tm_Solar_Gauge_major = 10
gauge_max_Solar_Gauge = 2000 #Wth max
gauge_min_Solar_Gauge = 0
frm_Solar_Gauge_title = 'Array output (Wth)'

dict_Solar_Gauge_Frame_Dims = {'frm_width': frmSolarSYSWidth,
                                'frm_height': frmSolarSYSHeight,
                                'frm_bd': frm_Solar_Gauge_bd,
                                'bx_width': bx_Solar_Gauge_width,
                                'bx_height': bx_Solar_Gauge_height,
                                'bx_x0': bx_Solar_Gauge_x0,
                                'bx_y0': bx_Solar_Gauge_y0}
dict_Solar_Gauge_Values = {'gauge_max': gauge_max_Solar_Gauge,
                                'gauge_min': gauge_min_Solar_Gauge,
                                'tm_length': tm_Solar_Gauge_length,
                                'tm_count': tm_Solar_Gauge_count,
                                'tm_major': tm_Solar_Gauge_major,
                                'tm_major_length': tm_Solar_Gauge_major_length,
                                'frm_title':frm_Solar_Gauge_title}
dict_Solar_Instructions = {'Dimensions': dict_Solar_Gauge_Frame_Dims, 'Values': dict_Solar_Gauge_Values}

dictGlobalSolar = {'GUI_Information': dictGlobalGUI,
                                'GUI_Sections': lstGUISections,
                                'GPIOs': dictSolarGPIOs,
                                'GUI_Commands': dictCommmands,
                                'Defaults': dictSolarDefaults,
                                'GUI_params': dictSolarGUIParams,
                                'Graph_params': dict_Solar_Graph_Instructions,
                                'Gauge_params': dict_Solar_Instructions}

#############################################
'''HEAT PUMP SYSTEM PARAMETERS'''
#############################################

#SQL TABLE
strHPSQLTable = 'HP'

#GUI Lists
lstHPOnOff = ['ON','OFF']
dictHPCommmands = {'On_Off': lstHPOnOff}

#GUI Defaults
imgHPLogo = fileLoc + "LOGO.png" #location of the Heat Set logo
dictHPDefaults = {'Logo': imgHPLogo,
                    'Database_Table_Name': strHPSQLTable,
                    'Interface_function': ''}

#GUI Information relating to sensors
dictHPOutletTempSensor = {'ID': 0,
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_Outlet_Temp_DegC',
                        'GUI_Label': 'Outlet Temperature (DegC)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Interface_function': lstHPSensors[0][1],
                        'Interface_args': lstHPSensors[0][2:], #SPIBus, SPI Chip select, MCP3008 channel
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Pulse_Meter': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None,
                        'Derived_Val': False}

dictHPInletTempSensor = {'ID': 1,
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_Inlet_Temp_DegC',
                        'GUI_Label': 'Inlet Temperature (DegC)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Interface_function': lstHPSensors[1][1],
                        'Interface_args': lstHPSensors[1][2:], #SPIBus, SPI Chip select, MCP3008 channel
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Pulse_Meter': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None,
                        'Derived_Val': False}

dictHPFlowRateSensor = {'ID': 2,
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_Flow_Rate',
                        'GUI_Label': 'Flow over last hour (L/Hr)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_GPIO': lstHPSensors[2][1],
                        'Pulse_Minute_Readings': None,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstHPSensors[2][2],
                        'Pulse_calc_flow': True,
                        'Pulse_calc_flow_load_dict': None,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None,
                        'Derived_Val': False}

dictHPThermalCapacity = {'ID': 3,
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_Thermal_Capacity_Wth',
                        'GUI_Label': 'Thermal capacity (Wth)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True,
                        'Derived_Val_Function': lstHPSensors[3][1], #Function to get sensor reading from H_Derivd_Values
                        'Derived_Val_Function_Args': lstHPSensors[3][2:], #Arguments required for function
                        'Derived_Minute_Average': None,
                        'Derived_total?': False,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}

dictHPExternalUnitElectricityConsumption = {'ID': 4,
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_External_Unit_Electricity_Wh',
                        'GUI_Label': 'External Unit electricity in day (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstHPSensors[4][2],
                        'Pulse_calc_flow': False,
                        'Pulse_calc_flow_load_dict': None,
                        'Pulse_GPIO': lstHPSensors[4][1],
                        'Pulse_Minute_Readings': None,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 2,
                        'Plot_colour': 'blue',
                        'Plot_label': 'Ext. Unit Elec.',
                        'Derived_Val': False}

dictHPTank= {'ID': 5,
                        'Include?': boolHPTank,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_Tank_Temperature_DegC',
                        'GUI_Label': 'Tank Temperature (DegC)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Interface_function': lstHPSensors[5][1], #Function to get sensor reading from F_Sensors
                        'Interface_args': lstHPSensors[5][2:], #Arguments required for function
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Pulse_Meter': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None,
                        'Derived_Val': False}

dictHPOnOff = {'ID':6,
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_On_Off',
                        'GUI_Label': 'Heat Pump ON or OFF',
                        'GUI_Val': None,
                        'cmd_count':1,
                        'cmd_Val1': None,
                        'cmd_Val2': None,
                        'cmd_def1':None,
                        'cmd_def2':None,
                        'GUI_Default': str(lstHPOnOff[0]),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Plot_Values?': False}

dictHPHeatLoad = {'ID':7, #Derived via D_Database, routine 'heat_xchange_thread'
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'Heat_load_Wh_hr',
                        'GUI_Label': 'Heat supplied during the day (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': 0,
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True,
                        'Derived_Val_Function': None, #Function to get sensor reading from H_Derivd_Values
                        'Derived_Val_Function_Args': None, #Arguments required for function
                        'Derived_Minute_Average': None,
                        'Derived_total?': True,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': True,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 1,
                        'Plot_colour': 'red',
                        'Plot_label': 'Heat'}

dictHPElectricalInput = {'ID': 8,
                        'Include?': False,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_Electrical_Input_kWe',
                        'GUI_Label': 'Electrical Input (kWe)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True,
                        'Derived_Val_Function': lstHPSensors[8][1], #Function to get sensor reading from H_Derivd_Values
                        'Derived_Val_Function_Args': lstHPSensors[8][2:], #Arguments required for function
                        'Derived_Minute_Average': None,
                        'Derived_total?': False,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}

dictHPInternalUnitElectricityConsumption = {'ID': 9,
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_Internal_Unit_Electricity_Consumption_Wh',
                        'GUI_Label': 'Internal Unit Electricity in day (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_GPIO': lstHPSensors[9][1],
                        'Pulse_Minute_Readings': None,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstHPSensors[9][2],
                        'Pulse_calc_flow': False,
                        'Pulse_calc_flow_load_dict': None,
                        'Derived_Val': False,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 3,
                        'Plot_colour': 'green',
                        'Plot_label': 'Int. Unit Elec.'}

dictHPPressureSensor = {'ID': 10,
                        'Include?': boolPressurised,
                        'SQL_Table': strSolarSQLTable,
                        'SQL_Title': 'HP_Pressure_bar',
                        'GUI_Label': 'System pressure (bar)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': True,
                        'Pulse_Meter': False,
                        'Interface_function': lstHPSensors[10][1], #Function stored in F_Sensors
                        'Interface_args': lstHPSensors[10][2:], #Arguments for the required function
                        'Sensor_Read_Times': None,
                        'Minute_Average': None,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None,
                        'Derived_Val': False}

dictHPCoP = {'ID': 11, #Populated via D_Database heat_xchange_thread
                        'Include?': True,
                        'SQL_Table': strHPSQLTable,
                        'SQL_Title': 'HP_CoP_Prev_Hr',
                        'GUI_Label': 'CoP over last Hour',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True,
                        'Derived_Val_Function': None, #Function to get sensor reading from H_Derivd_Values
                        'Derived_Val_Function_Args': None, #Arguments required for function
                        'Derived_Minute_Average': None,
                        'Derived_total?': False,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}

dictGlobalHPGUI = {'Outlet_Temperature': dictHPOutletTempSensor,
                        'Inlet_Temperature': dictHPInletTempSensor,
                        'Flow_Rate': dictHPFlowRateSensor,
                        'Thermal_Capacity': dictHPThermalCapacity,
                        'External_Unit_Elec_Wh': dictHPExternalUnitElectricityConsumption,
                        'Internal_Unit_Elec_Wh': dictHPInternalUnitElectricityConsumption,
                        'HP_Tank': dictHPTank,
                        'HP_On_Off': dictHPOnOff,
                        'Heat_load': dictHPHeatLoad,
                        'Electricity_Input': dictHPElectricalInput,
                        'HP_Pressure': dictHPPressureSensor,
                        'HP_CoP': dictHPCoP}

lstGUIHPSensorNoADJ = [0, 1, 3, 7, 9, 4, 2, 11, 10] #Measured values on the GUI so not adjusted by the user
lstGUIHPSensorADJ = [6] #Target values on the GUI that the user can adjust with up down arrows
lstGUIHPSections = [lstGUIHPSensorNoADJ, lstGUIHPSensorADJ]

#HP TAB SIZING
if boolHeatPumpControl == True:
    frmHPSensorsHeightDefault = 120
else:
    frmHPSensorsHeightDefault = 150
frmHPSensorsWidthDefault = frmLogoWidthDefault
frmHPSensorsHeight = frmHPSensorsHeightDefault * lngScreenHeightADJ
frmHPSensorsWidth = frmHPSensorsWidthDefault * lngScreenWidthADJ
frmHPSensors_x = 0
frmHPSensors_y = frmLogoHeight

dictHPSensors = {'SensorFm_height': frmHPSensorsHeight,
                        'SensorFm_width': frmHPSensorsWidth,
                        'Sensor_x': frmHPSensors_x,
                        'Sensor_y': frmHPSensors_y}

frmHPGraphHeight = lngScreenHeight
frmHPGraphWidth = lngScreenWidth - frmLogoWidth
frmHPGraph_x = frmHPSensorsWidth
frmHPGraph_y = 0

dictHPGraph = {'GraphFm_height': frmHPGraphHeight,
                        'GraphFm_width': frmHPGraphWidth,
                        'Graph_x': frmHPGraph_x,
                        'Graph_y': frmHPGraph_y}

frmHPSYSHeightDefault = 40
frmHPSYSWidthDefault = frmLogoWidthDefault
frmHPSYSHeight = frmHPSYSHeightDefault * lngScreenHeightADJ
frmHPSYSWidth = frmHPSYSWidthDefault * lngScreenWidthADJ
frmHPSYS_x = 0
frmHPSYS_y = frmLogoHeight + frmHPSensorsHeight

dictHPSYS = {'SYSFm_height': frmHPSYSHeight, 'SYSFm_width': frmHPSYSWidth, 'SYS_x': frmHPSYS_x, 'SYS_y': frmHPSYS_y}

if boolHeatPumpControl == True:
    frmHPGaugeHeightDefault = lngScreenDesignHeight - frmHPSYSHeightDefault - frmHPSensorsHeightDefault - frmLogoHeightDefault
    frmHPGauge_y = frmLogoHeight + frmHPSensorsHeight + frmHPSYSHeight
else:
    frmHPGaugeHeightDefault = lngScreenDesignHeight - frmHPSensorsHeightDefault - frmLogoHeightDefault
    frmHPGauge_y = frmLogoHeight + frmHPSensorsHeight

frmHPGaugeHeight = frmHPGaugeHeightDefault * lngScreenHeightADJ
frmHPGaugeWidthDefault = frmLogoWidthDefault
frmHPGaugeWidth = frmHPGaugeWidthDefault * lngScreenWidthADJ
frmHPGauge_x = 0


dictHPGauge = {'Fm_height': frmHPGaugeHeight, 'Fm_width': frmHPGaugeWidth, 'Gauge_x': frmHPGauge_x, 'Gauge_y': frmHPGauge_y}
dictHPGUIParams = {'Sensor_Section': dictHPSensors, 'Graph_Section': dictHPGraph, 'System_Section': dictHPSYS, 'Gauge_Section': dictHPGauge}

#HP GRAPH
frm_HP_Graph_bd = 1
bx_HP_Graph_width = frmHPGraphWidth
bx_HP_Graph_height = frmHPGraphHeight-40
bx_HP_Graph_x0 = 0
bx_HP_Graph_y0 = 0
tm_HP_Graph_length = 5 #pixel length of the minor tm line
tm_HP_Graph_major_length = 10 #pixel length of the major tm line
tm_HP_Graph_x_count = 24*2 #Show tickmarks each half hour
tm_HP_Graph_x_major = 2 #Show major tm on the hour
HP_Graph_x_max = 24 #maximum value of x axis is 24th hour
HP_Graph_x_min = 0 #minimum value on the x axis in the 0th hour
tm_HP_Graph_y_count = 60 #Maximum on graph assumes no more than 10 hours @ maximum capacity (which would be excessive!)
tm_HP_Graph_y_major= 2 #Show major tm for every Wh
HP_Graph_y_max = 30000 #Maximum wh per day
HP_Graph_y_min = 0 #Minimum capacity on y-axisis 0 kWh
frm_HP_Graph_title = 'Thermal output and electrical input: ' + strftime("%d/%m/%Y", gmtime())
boolGrid_HP_Graph = True
HP_Graph_x_title = 'Time (hour of day)'
HP_Graph_y_title = 'Cumulative energy transfer (Wh)'

dict_HP_Graph_Frame_Dims = {'frm_width': frmHPGraphWidth,
                                'frm_height': frmHPGraphHeight,
                                'frm_bd': frm_HP_Graph_bd,
                                'bx_width': bx_HP_Graph_width,
                                'bx_height': bx_HP_Graph_height,
                                'bx_x0': bx_HP_Graph_x0,
                                'bx_y0': bx_HP_Graph_y0}
dict_HP_Graph_Values = {'include_grid': boolGrid_HP_Graph,
                                'graph_x_title': HP_Graph_x_title,
                                'graph_x_max': HP_Graph_x_max,
                                'graph_x_min': HP_Graph_x_min,
                                'graph_y_title': HP_Graph_y_title,
                                'graph_y_max': HP_Graph_y_max,
                                'graph_y_min': HP_Graph_y_min,
                                'tm_length': tm_HP_Graph_length,
                                'tm_x_count': tm_HP_Graph_x_count,
                                'tm_x_major': tm_HP_Graph_x_major,
                                'tm_y_count': tm_HP_Graph_y_count,
                                'tm_y_major': tm_HP_Graph_y_major,
                                'tm_major_length': tm_HP_Graph_major_length,
                                'frm_title':frm_HP_Graph_title}
dict_HP_Graph_Instructions = {'Dimensions': dict_HP_Graph_Frame_Dims, 'Values': dict_HP_Graph_Values}

#HEAT PUMP CoP GAUGE
frm_HP_Gauge_bd = 1
bx_HP_Gauge_width = frmHPGaugeWidth
bx_HP_Gauge_height = frmHPGaugeWidth #the box height needs to be the same height as the width as this is to draw a full circle
bx_HP_Gauge_x0 = 0
bx_HP_Gauge_y0 = 0
tm_HP_Gauge_length = 5
tm_HP_Gauge_major_length = 10
tm_HP_Gauge_count = 50
tm_HP_Gauge_major = 10
gauge_max_HP_Gauge = 5
gauge_min_HP_Gauge = 0
frm_HP_Gauge_title = 'In-day CoP'

dict_HP_Gauge_Frame_Dims = {'frm_width': frmHPGaugeWidth,
                                'frm_height': frmHPGaugeHeight,
                                'frm_bd': frm_HP_Gauge_bd,
                                'bx_width': bx_HP_Gauge_width,
                                'bx_height': bx_HP_Gauge_height,
                                'bx_x0': bx_HP_Gauge_x0,
                                'bx_y0': bx_HP_Gauge_y0}
dict_HP_Gauge_Values = {'gauge_max': gauge_max_HP_Gauge,
                                'gauge_min': gauge_min_HP_Gauge,
                                'tm_length': tm_HP_Gauge_length,
                                'tm_count': tm_HP_Gauge_count,
                                'tm_major': tm_HP_Gauge_major,
                                'tm_major_length': tm_HP_Gauge_major_length,
                                'frm_title':frm_HP_Gauge_title}
dict_HP_Instructions = {'Dimensions': dict_HP_Gauge_Frame_Dims, 'Values': dict_HP_Gauge_Values}

dictGlobalHP = {'GUI_Information': dictGlobalHPGUI,
                                'GUI_Sections': lstGUIHPSections,
                                'GPIOs': None,
                                'GUI_Commands': dictHPCommmands,
                                'Defaults': dictHPDefaults,
                                'GUI_params': dictHPGUIParams,
                                'Graph_params': dict_HP_Graph_Instructions,
                                'Gauge_params': dict_HP_Instructions}

#############################################
'''PHOTOVOLTAIC SYSTEM PARAMETERS'''
#############################################

#SQL TABLE
strPVSQLTable = 'PV'

#GUI Defaults
imgPVLogo = fileLoc + "LOGO.png" #location of the Heat Set logo
dictPVDefaults = {'Logo': imgPVLogo,
                    'Database_Table_Name': strPVSQLTable,
                    'Interface_function': ''}

#GUI Information relating to sensors
dictPVElectricalOutput = {'ID': 0,
                        'Include?': True,
                        'SQL_Table': strPVSQLTable,
                        'SQL_Title': 'PV_Electrical_Output_We',
                        'GUI_Label': 'Electrical output (We)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': False,
                        'Derived_Val_Function': lstPVSensors[0][1], ##Function to get sensor reading from H_Derived_Values
                        'Derived_Val_Function_Args': lstPVSensors[0][2:], #Arguments required for function,
                        'Derived_Minute_Average': None,
                        'Derived_total?': False,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}

dictWhGenerated = {'ID': 1,
                        'Include?': True,
                        'SQL_Table': strPVSQLTable,
                        'SQL_Title': 'PV_electricity_generated_Wh',
                        'GUI_Label': 'Electricity generated in day (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_GPIO': lstPVSensors[1][1],
                        'Pulse_Minute_Readings': None,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstPVSensors[1][2],
                        'Pulse_calc_flow': False,
                        'Pulse_calc_flow_load_dict': None,
                        'Derived_Val': False,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 1,
                        'Plot_colour': 'blue',
                        'Plot_label': 'Electricity'}

dictGlobalPVGUI = {'Electrical_output': dictPVElectricalOutput,
                        'Generation': dictWhGenerated}

lstGUIPVSensorNoADJ = [1] #Measured values on the GUI so not adjusted by the user
lstGUIPVSections = [lstGUIPVSensorNoADJ]

#PV TAB SIZING
frmPVSensorsHeightDefault = 150
frmPVSensorsWidthDefault = frmLogoWidthDefault
frmPVSensorsHeight = frmPVSensorsHeightDefault * lngScreenHeightADJ
frmPVSensorsWidth = frmPVSensorsWidthDefault * lngScreenWidthADJ
frmPVSensors_x = 0
frmPVSensors_y = frmLogoHeight

dictPVSensors = {'SensorFm_height': frmPVSensorsHeight,
                        'SensorFm_width': frmPVSensorsWidth,
                        'Sensor_x': frmPVSensors_x,
                        'Sensor_y': frmPVSensors_y}

frmPVGraphHeight = lngScreenHeight
frmPVGraphWidth = lngScreenWidth - frmLogoWidth
frmPVGraph_x = frmPVSensorsWidth
frmPVGraph_y = 0

dictPVGraph = {'GraphFm_height': frmPVGraphHeight,
                        'GraphFm_width': frmPVGraphWidth,
                        'Graph_x': frmPVGraph_x,
                        'Graph_y': frmPVGraph_y}

frmPVGaugeHeightDefault = lngScreenDesignHeight - frmPVSensorsHeightDefault - frmLogoHeightDefault
frmPVGaugeHeight = frmPVGaugeHeightDefault * lngScreenHeightADJ
frmPVGaugeWidthDefault = frmLogoWidthDefault
frmPVGaugeWidth = frmPVGaugeWidthDefault * lngScreenWidthADJ
frmPVGauge_x = 0
frmPVGauge_y = frmLogoHeight + frmPVSensorsHeight

dictPVGauge = {'Fm_height': frmPVGaugeHeight, 'Fm_width': frmPVGaugeWidth, 'Gauge_x': frmPVGauge_x, 'Gauge_y': frmPVGauge_y}
dictPVGUIParams = {'Sensor_Section': dictPVSensors, 'Graph_Section': dictPVGraph, 'Gauge_Section': dictPVGauge}

#PV GRAPH
frm_PV_Graph_bd = 1
bx_PV_Graph_width = frmPVGraphWidth
bx_PV_Graph_height = frmPVGraphHeight-40
bx_PV_Graph_x0 = 0
bx_PV_Graph_y0 = 0
tm_PV_Graph_length = 5 #pixel length of the minor tm line
tm_PV_Graph_major_length = 10 #pixel length of the major tm line
tm_PV_Graph_x_count = 24*2 #Show tickmarks each half hour
tm_PV_Graph_x_major = 2 #Show major tm on the hour
PV_Graph_x_max = 24 #maximum value of x axis is 24th hour
PV_Graph_x_min = 0 #minimum value on the x axis in the 0th hour
tm_PV_Graph_y_count = 20 #Show max xWh per minute
tm_PV_Graph_y_major= 1 #Show major tm for every xWh
PV_Graph_y_max = 10000 #Maximum Wh
PV_Graph_y_min = 0 #Minimum capacity on y-axisis  kWh
frm_PV_Graph_title = 'In-day electricity generated: ' + strftime("%d/%m/%Y", gmtime())
boolGrid_PV_Graph = True
PV_Graph_x_title = 'Time (hour of day)'
PV_Graph_y_title = 'Cumulative electrical output (Wh)'

dict_PV_Graph_Frame_Dims = {'frm_width': frmPVGraphWidth,
                                'frm_height': frmPVGraphHeight,
                                'frm_bd': frm_PV_Graph_bd,
                                'bx_width': bx_PV_Graph_width,
                                'bx_height': bx_PV_Graph_height,
                                'bx_x0': bx_PV_Graph_x0,
                                'bx_y0': bx_PV_Graph_y0}
dict_PV_Graph_Values = {'include_grid': boolGrid_PV_Graph,
                                'graph_x_title': PV_Graph_x_title,
                                'graph_x_max': PV_Graph_x_max,
                                'graph_x_min': PV_Graph_x_min,
                                'graph_y_title': PV_Graph_y_title,
                                'graph_y_max': PV_Graph_y_max,
                                'graph_y_min': PV_Graph_y_min,
                                'tm_length': tm_PV_Graph_length,
                                'tm_x_count': tm_PV_Graph_x_count,
                                'tm_x_major': tm_PV_Graph_x_major,
                                'tm_y_count': tm_PV_Graph_y_count,
                                'tm_y_major': tm_PV_Graph_y_major,
                                'tm_major_length': tm_PV_Graph_major_length,
                                'frm_title':frm_PV_Graph_title}
dict_PV_Graph_Instructions = {'Dimensions': dict_PV_Graph_Frame_Dims, 'Values': dict_PV_Graph_Values}

#PV Array GAUGE
frm_PV_Gauge_bd = 1
bx_PV_Gauge_width = frmPVGaugeWidth
bx_PV_Gauge_height = frmPVGaugeWidth #the box height needs to be the same height as the width as this is to draw a full circle
bx_PV_Gauge_x0 = 0
bx_PV_Gauge_y0 = 0
tm_PV_Gauge_length = 5
tm_PV_Gauge_major_length = 10
tm_PV_Gauge_count = int(PVArrayMaxOutputW / 10)
tm_PV_Gauge_major = 10
gauge_max_PV_Gauge = PVArrayMaxOutputW
gauge_min_PV_Gauge = 0
frm_PV_Gauge_title = 'Output last hr (We)'

dict_PV_Gauge_Frame_Dims = {'frm_width': frmPVGaugeWidth,
                                'frm_height': frmPVGaugeHeight,
                                'frm_bd': frm_PV_Gauge_bd,
                                'bx_width': bx_PV_Gauge_width,
                                'bx_height': bx_PV_Gauge_height,
                                'bx_x0': bx_PV_Gauge_x0,
                                'bx_y0': bx_PV_Gauge_y0}
dict_PV_Gauge_Values = {'gauge_max': gauge_max_PV_Gauge,
                                'gauge_min': gauge_min_PV_Gauge,
                                'tm_length': tm_PV_Gauge_length,
                                'tm_count': tm_PV_Gauge_count,
                                'tm_major': tm_PV_Gauge_major,
                                'tm_major_length': tm_PV_Gauge_major_length,
                                'frm_title':frm_PV_Gauge_title}
dict_PV_Instructions = {'Dimensions': dict_PV_Gauge_Frame_Dims, 'Values': dict_PV_Gauge_Values}

dictGlobalPV = {'GUI_Information': dictGlobalPVGUI,
                                'GUI_Sections': lstGUIPVSections,
                                'GPIOs': None,
                                'GUI_Commands': None,
                                'Defaults': dictPVDefaults,
                                'GUI_params': dictPVGUIParams,
                                'Graph_params': dict_PV_Graph_Instructions,
                                'Gauge_params': dict_PV_Instructions}

#############################################
'''BATTERY SYSTEM PARAMETERS'''
#############################################

#SQL TABLE
strBATSQLTable = 'BATTERY'

#GUI Defaults
imgBATLogo = fileLoc + "LOGO.png" #location of the Heat Set logo
dictBATDefaults = {'Logo': imgBATLogo,
                    'Database_Table_Name': strBATSQLTable,
                    'Interface_function': ''}

#GUI Information relating to sensors
dictDisChargeWattage = {'ID': 0,
                        'Include?': False,
                        'SQL_Table': strBATSQLTable,
                        'SQL_Title': 'BAT_Discharge_We',
                        'GUI_Label': 'Discharge wattage (We)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True,
                        'Derived_Val_Function': lstBATSensors[0][1], #Function to get sensor reading from H_Derived_Values
                        'Derived_Val_Function_Args': lstBATSensors[0][2:], #Arguments required for function,
                        'Derived_Minute_Average': None,
                        'Derived_total?': False,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}

dictDischargeSupply = {'ID': 1,
                        'Include?': True,
                        'SQL_Table': strBATSQLTable,
                        'SQL_Title': 'BAT_DischargeElectricity_Wh',
                        'GUI_Label': 'Electricity discharged during day (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_GPIO': lstBATSensors[1][1],
                        'Pulse_Minute_Readings': None,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstBATSensors[1][2],
                        'Pulse_calc_flow': False,
                        'Pulse_calc_flow_load_dict': None,
                        'Derived_Val': False,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 1,
                        'Plot_colour': 'blue',
                        'Plot_label': 'Discharge'}

dictChargeWattage = {'ID': 2,
                        'Include?': False,
                        'SQL_Table': strBATSQLTable,
                        'SQL_Title': 'BAT_Charge_We',
                        'GUI_Label': 'Charge wattage (We)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': False,
                        'Derived_Val': True,
                        'Derived_Val_Function': lstBATSensors[2][1], #Function to get sensor reading from H_Derived_Values
                        'Derived_Val_Function_Args': lstBATSensors[2][2:], #Arguments required for function,
                        'Derived_Minute_Average': None,
                        'Derived_total?': False,
                        'Derived_read_times': None,
                        'Derived_DB_Total?': False,
                        'Plot_Values?': False,
                        'Plot_Value_List': [],
                        'Plot_index': None,
                        'Plot_colour': None,
                        'Plot_label': None}
dictChargeSupply = {'ID': 3,
                        'Include?': True,
                        'SQL_Table': strBATSQLTable,
                        'SQL_Title': 'BAT_ChargeElectricity_Supply_Wh',
                        'GUI_Label': 'Electricity charged during day (Wh)',
                        'GUI_Val': None,
                        'GUI_Default': str(0),
                        'Sensor': False,
                        'Pulse_Meter': True,
                        'Pulse_GPIO': lstBATSensors[3][1],
                        'Pulse_Minute_Readings': None,
                        'Pulse_reading_times': None,
                        'Pulse_Value': lstBATSensors[3][2],
                        'Pulse_calc_flow': False,
                        'Pulse_calc_flow_load_dict': None,
                        'Derived_Val': False,
                        'Plot_Values?': True,
                        'Plot_Value_List': [],
                        'Plot_index': 2,
                        'Plot_colour': 'red',
                        'Plot_label': 'Charge'}

dictGlobalBATGUI = {'Discharge_Wattage': dictDisChargeWattage,
                        'Discharge_Supply': dictDischargeSupply,
                        'Charge_Wattage': dictChargeWattage,
                        'Charge_Supply': dictChargeSupply}

lstGUIBATSensorNoADJ = [1, 3] #Measured values on the GUI so not adjusted by the user
lstGUIBATSections = [lstGUIBATSensorNoADJ]

#BAT TAB SIZING
frmBATSensorsHeightDefault = 150
frmBATSensorsWidthDefault = frmLogoWidthDefault
frmBATSensorsHeight = frmBATSensorsHeightDefault * lngScreenHeightADJ
frmBATSensorsWidth = frmBATSensorsWidthDefault * lngScreenWidthADJ
frmBATSensors_x = 0
frmBATSensors_y = frmLogoHeight

dictBATSensors = {'SensorFm_height': frmBATSensorsHeight,
                        'SensorFm_width': frmBATSensorsWidth,
                        'Sensor_x': frmBATSensors_x,
                        'Sensor_y': frmBATSensors_y}

frmBATGraphHeight = lngScreenHeight
frmBATGraphWidth = lngScreenWidth - frmLogoWidth
frmBATGraph_x = frmBATSensorsWidth
frmBATGraph_y = 0

dictBATGraph = {'GraphFm_height': frmBATGraphHeight,
                        'GraphFm_width': frmBATGraphWidth,
                        'Graph_x': frmBATGraph_x,
                        'Graph_y': frmBATGraph_y}

frmBATGaugeHeightDefault = lngScreenDesignHeight - frmBATSensorsHeightDefault - frmLogoHeightDefault
frmBATGaugeHeight = frmBATGaugeHeightDefault * lngScreenHeightADJ
frmBATGaugeWidthDefault = frmLogoWidthDefault
frmBATGaugeWidth = frmBATGaugeWidthDefault * lngScreenWidthADJ
frmBATGauge_x = 0
frmBATGauge_y = frmLogoHeight + frmBATSensorsHeight

dictBATGauge = {'Fm_height': frmBATGaugeHeight, 'Fm_width': frmBATGaugeWidth, 'Gauge_x': frmBATGauge_x, 'Gauge_y': frmBATGauge_y}
dictBATGUIParams = {'Sensor_Section': dictBATSensors, 'Graph_Section': dictBATGraph, 'Gauge_Section': dictBATGauge}

#BAT GRAPH
frm_BAT_Graph_bd = 1
bx_BAT_Graph_width = frmBATGraphWidth
bx_BAT_Graph_height = frmBATGraphHeight-40
bx_BAT_Graph_x0 = 0
bx_BAT_Graph_y0 = 0
tm_BAT_Graph_length = 5 #pixel length of the minor tm line
tm_BAT_Graph_major_length = 10 #pixel length of the major tm line
tm_BAT_Graph_x_count = 24*2 #Show tickmarks each half hour
tm_BAT_Graph_x_major = 2 #Show major tm on the hour
BAT_Graph_x_max = 24 #maximum value of x axis is 24th hour
BAT_Graph_x_min = 0 #minimum value on the x axis in the 0th hour
tm_BAT_Graph_y_count = 20 #Show a tm for each kWh
tm_BAT_Graph_y_major= 1 #Show major tm for every kWh generated in a minute
BAT_Graph_y_max = 10000 #Maximum Wh in a day
BAT_Graph_y_min = 0 #Minimum charge/discharge on y-axisis 0 Wh
frm_BAT_Graph_title = 'Charge/Discharge during day: ' + strftime("%d/%m/%Y", gmtime())
boolGrid_BAT_Graph = True
BAT_Graph_x_title = 'Time (hour of day)'
BAT_Graph_y_title = 'Cumulative charge/discharge (Wh)'

dict_BAT_Graph_Frame_Dims = {'frm_width': frmBATGraphWidth,
                                'frm_height': frmBATGraphHeight,
                                'frm_bd': frm_BAT_Graph_bd,
                                'bx_width': bx_BAT_Graph_width,
                                'bx_height': bx_BAT_Graph_height,
                                'bx_x0': bx_BAT_Graph_x0,
                                'bx_y0': bx_BAT_Graph_y0}
dict_BAT_Graph_Values = {'include_grid': boolGrid_BAT_Graph,
                                'graph_x_title': BAT_Graph_x_title,
                                'graph_x_max': BAT_Graph_x_max,
                                'graph_x_min': BAT_Graph_x_min,
                                'graph_y_title': BAT_Graph_y_title,
                                'graph_y_max': BAT_Graph_y_max,
                                'graph_y_min': BAT_Graph_y_min,
                                'tm_length': tm_BAT_Graph_length,
                                'tm_x_count': tm_BAT_Graph_x_count,
                                'tm_x_major': tm_BAT_Graph_x_major,
                                'tm_y_count': tm_BAT_Graph_y_count,
                                'tm_y_major': tm_BAT_Graph_y_major,
                                'tm_major_length': tm_BAT_Graph_major_length,
                                'frm_title':frm_BAT_Graph_title}
dict_BAT_Graph_Instructions = {'Dimensions': dict_BAT_Graph_Frame_Dims, 'Values': dict_BAT_Graph_Values}

#BAT Array GAUGE
frm_BAT_Gauge_bd = 11
bx_BAT_Gauge_width = frmBATGaugeWidth
bx_BAT_Gauge_height = frmBATGaugeWidth #the box height needs to be the same height as the width as this is to draw a full circle
bx_BAT_Gauge_x0 = 0
bx_BAT_Gauge_y0 = 0
tm_BAT_Gauge_length = 5
tm_BAT_Gauge_major_length = 10
tm_BAT_Gauge_count = 200
tm_BAT_Gauge_major = 10
gauge_max_BAT_Gauge = 100
gauge_min_BAT_Gauge = -100
frm_BAT_Gauge_title = 'Chg./(dischg.)(%)'

dict_BAT_Gauge_Frame_Dims = {'frm_width': frmBATGaugeWidth,
                                'frm_height': frmBATGaugeHeight,
                                'frm_bd': frm_BAT_Gauge_bd,
                                'bx_width': bx_BAT_Gauge_width,
                                'bx_height': bx_BAT_Gauge_height,
                                'bx_x0': bx_BAT_Gauge_x0,
                                'bx_y0': bx_BAT_Gauge_y0}
dict_BAT_Gauge_Values = {'gauge_max': gauge_max_BAT_Gauge,
                                'gauge_min': gauge_min_BAT_Gauge,
                                'tm_length': tm_BAT_Gauge_length,
                                'tm_count': tm_BAT_Gauge_count,
                                'tm_major': tm_BAT_Gauge_major,
                                'tm_major_length': tm_BAT_Gauge_major_length,
                                'frm_title':frm_BAT_Gauge_title}
dict_BAT_Instructions = {'Dimensions': dict_BAT_Gauge_Frame_Dims, 'Values': dict_BAT_Gauge_Values}

dictGlobalBAT = {'GUI_Information': dictGlobalBATGUI,
                                'GUI_Sections': lstGUIBATSections,
                                'GPIOs': None,
                                'GUI_Commands': None,
                                'Defaults': dictBATDefaults,
                                'GUI_params': dictBATGUIParams,
                                'Graph_params': dict_BAT_Graph_Instructions,
                                'Gauge_params': dict_BAT_Instructions}

dictGlobalInstructions = {'User_Inputs': dictUser,
                            'General_Inputs': dictCommonGUIParams,
                            'Threads': dictThreads,
                            'Solar_Inputs': dictGlobalSolar,
                            'HP_Inputs': dictGlobalHP,
                            'PV_Inputs': dictGlobalPV,
                            'BAT_Inputs': dictGlobalBAT,
                            'Database': None}
