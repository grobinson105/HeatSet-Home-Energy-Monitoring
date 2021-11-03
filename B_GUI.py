from tkinter import ttk
from tkinter import *
import time
import datetime as dt
import subprocess
# from rpi_backlight import Backlight
import threading
from PIL import Image, ImageTk
from A_Initialise import *
import C_chart_plots as cht_plt
import D_Database as db
import E_Solar_Pump as pump
import F_Sensors as sensors
import G_Check_Time as chk_time
import H_Derived_Values as derived
import I_Pulse_Meters as pulse
#import TEST_Pulse as test_pulse

def cmdMode():
    print("USER ADJ: system mode changed: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lbl_Val = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['System_mode']['GUI_Val'] #On set up of the text boxes the libraries created within the System_Analyze module are updated with the label names
    strVal = lbl_Val.cget("text") #Get the current value of the label
    if strVal == dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['Solar_modes'][0]: #If the label is set to Manual then
        lbl_Val.config(text=dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['Solar_modes'][1]) #make the label show "SYSTEM"
    else:   #else if not then
        lbl_Val.config(text=dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['Solar_modes'][0]) #make the label show "MANUAL" - in manual mode the user can switch the mechanical valve on/off
    print(lbl_Val.cget("text"))

def cmdOnOff(lblUpdate): #provide the label to the routine
    strVal = lblUpdate.cget("text") #get the string value of the label
    if strVal == dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['On_Off'][0]: #if the string is set to "ON" then
        lblUpdate.config(text=dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['On_Off'][1]) #set it to OFF
    else:
        lblUpdate.config(text=dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['On_Off'][0]) #else set it to ON

def check_manual(lbl_SYS):
    strVal = lbl_SYS.cget("text")
    if strVal == dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['Solar_modes'][0]: #System mode so user cannot manually switch the pump on or off
        winError = Tk()
        winError.wm_title("ERROR: System mode currently set")
        winError.geometry('%dx%d+%d+%d' % (400, 30, 0, 0))
        frmError = Frame(winError)
        frmError.pack()
        lblError = Label(frmError,
                            text='You must set the sysetm to MANUAL mode.',
                            font=(dictGlobalInstructions['General_Inputs']['Font'],
                                dictGlobalInstructions['General_Inputs']['Font_size']))
        lblError.pack()
        return False
    else:
        return True

def pump_on_off(): #Routine for allowing for manual switch on and off of the pump
    lbl_SYS = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['System_mode']['GUI_Val']
    lblPump = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['GUI_Val'] #On system initialize the library Solar Pump is created and the label's name is created and uploaded to the library on set up of this GUI
    strPumpStatus = lblPump.cget("text")
    boolManual = check_manual(lbl_SYS)
    if boolManual == True: # The user must first switch to manual mode to allow for the pump to be manually operated
        boolPressurised = dictGlobalInstructions['User_Inputs']['Pressurised'] # if the user has selected to have a pressurised system then
        if boolPressurised == True:
            lblPressureStatus = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Pressure_Status']['GUI_Val']
            strPressureStatus = lblPressureStatus.cget("text")
            if strPressureStatus == dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['Pressure_status'][0]: #If the pressure reading is OK
                print("USER ADJ: pump status changed: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
                cmdOnOff(lblPump) #Swith the pump on/off (the routine run_system.py takes the GUI's label stutus and will either turn the pump on or off
                print(lblPump.cget("text"))
            else:
                winError = Tk()
                winError.wm_title("ERROR: Insufficient pressure")
                winError.geometry('%dx%d+%d+%d' % (600, 30, 0, 0))
                frmError = Frame(winError)
                frmError.pack()
                lblError = Label(frmError, text='There is insufficient system pressure to turn the pump on. Please re-prime the system.', font=(strFont, bytFontSize))
                lblError.pack()
        else:
            print("USER ADJ: pump status changed: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
            cmdOnOff(lblPump) #Swith the pump on/off (the routine run_system.py takes the GUI's label stutus and will either turn the pump on or off
            print(lblPump.cget("text"))

def HP_on_off(): #Routine for manual switch on off of the heat pump
    lblHP = dictGlobalInstructions['HP_Inputs']['GUI_Information']['HP_On_Off']['GUI_Val']
    print("USER ADJ: HP on/off adjustment: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    cmdOnOff(lblHP)
    print(lblHP.cget("text"))

def valve_on_off(): #Routine for allowing for manual switch on and off of the valve
    lbl_SYS = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['System_mode']['GUI_Val']
    lblValve = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Flush_Valve']['GUI_Val'] #On system initialize the library libReturnValve is created and the label's name is created and uploaded to the library on set up of this GUI
    boolManual = check_manual(lbl_SYS)
    if boolManual == True:
        print("USER ADJ: system flushed: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
        cmdOnOff(lblValve) #Swith the valve on/off (the routine run_system.py takes the GUI's label stutus and will either turn the pump on or off
        print(lblValve.cget("text"))

def increase_time(lblADJ, boolUp): #function to increase/decrease time shown on screen in increments of 15 minutes
    bytIncrement = 15 #increment in 15 minute slots
    strTime = lblADJ.cget("text")
    strMinCurr = strTime[len(strTime)-2:] #take last two characters of the time which are shown HH:MM as the GUI time values
    if strMinCurr[0] == str(0):
        intMinCurr = int(strMinCurr[1])
    else:
        intMinCurr = int(strMinCurr) #convert the string to an integer
    strHRCurr =  strTime[:2] #take the first two characters
    if strHRCurr[0] == str(0):
        intHRCurr = int(strHRCurr[1])
    else:
        intHRCurr = int(strHRCurr) #convert the string to an integer
    intPlusMin = intMinCurr + bytIncrement #increase the current minute by the increment
    intMinusMin = intMinCurr - bytIncrement #decrease teh current minute by the increment
    if boolUp == True: #if this is an upwards adjustment then
        if intPlusMin >= 60: #if the the current minute plus the increment is greater than or equal to 60 mintues then
            intHRADJ = intHRCurr + 1 #Adjust the current hour by one hour (we'll deal with 24 hour scenario in a minute)
            intMinADJ = intPlusMin - 60 #Now subtract 60 from the minute value as we have added 1 to the hour value
        else:
            intHRADJ = intHRCurr #As the minute adjustment has not taken the minute value over the hour threshold hold constants
            intMinADJ = intPlusMin #As above
    else: #the adjustment is a downwards adjustment
        if intMinusMin < 0: #If the current minute less the increment is less than zero then:
            intHRADJ = intHRCurr - 1 #adjust the current hour down by 1 (we will deal with the 0 scenario in a minute)
            intMinADJ = 60 - bytIncrement #We have crossed the hour threshold so take 60 minutes less the increment
        else:
            intHRADJ = intHRCurr #As the minute adjustment has not taken the minute value over the hour threshold hold constants
            intMinADJ = intMinusMin #As above

    if intHRADJ == 24: #If the adjusted hour has increased to 24 then
        intHRADJ = 0

    if intHRADJ == -1: #If the adjusted hour has reduced from 00:00 to -1:00 then
        intHRADJ = 23

    strMinADJ = str(intMinADJ) #Turn the adjusted minute to a string
    strHRADJ = str(intHRADJ) #Turn the adjusted hour to a string
    if len(strMinADJ) == 1: #if the minute is less than 10 (i.e. only 1 integer) then
        strMinADJ = str(0) + strMinADJ #Add a zero string infront
    if len(strHRADJ) == 1: #if the hour is less than 10 (i.e. only 1 integer) then
        strHRADJ = str(0) + strHRADJ #add a zero string infront

    strUpdate = strHRADJ + ":" + strMinADJ
    lblADJ.config(text=strUpdate) #Update the label to reflect the change

def increase_decrease(lblADJ, boolUP, bytIncrement, dp): #increase/decrease temperature
    strTemp = lblADJ.cget("text")
    floatTemp = float(strTemp) #turn the temperature shown on the GUI's label to an integer (it is presented as a string)
    if boolUP == True: #If the user has pressed the increment up button then
        floatTemp += bytIncrement #add the increment to the current value
    else: #else if the user has pressed the increment down button then
        floatTemp -= bytIncrement #subtract the increment from the current value

    if dp > 0:
        strFormat = "{:." + str(dp) + "f}"
        strfloatTemp = str(float(strFormat.format(floatTemp)))
    else:
        strfloatTemp = str(int(floatTemp))
    lblADJ.config(text=strfloatTemp) #Update the label with the increment

def Target_Temp_Increase():
    print("USER ADJ: increase target DeltaT: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblTarget = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_DeltaT']['GUI_Val']
    increase_decrease(lblTarget, True,1,0)
    print(lblTarget.cget("text"))

def Target_Temp_Decrease():
    print("USER ADJ: decrease target DeltaT: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblTarget = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_DeltaT']['GUI_Val']
    increase_decrease(lblTarget, False,1,0)
    print(lblTarget.cget("text"))

def Max_Temp_Increase():
    print("USER ADJ: increase maximum system temperature: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMax = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_Temp']['GUI_Val']
    increase_decrease(lblMax, True,1,0)
    print(lblMax.cget("text"))

def Max_Temp_Decrease():
    print("USER ADJ: decrease maximum system temperature: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMax = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_Temp']['GUI_Val']
    increase_decrease(lblMax, False,1,0)
    print(lblMax.cget("text"))

def Min_Temp_Increase():
    print("USER ADJ: increase minimum system temperature: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMin = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_Temp']['GUI_Val']
    increase_decrease(lblMin, True,1,0)
    print(lblMin.cget("text"))

def Min_Temp_Decrease():
    print("USER ADJ: decrease minimum system temperature: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMin = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_Temp']['GUI_Val']
    increase_decrease(lblMin, False,1,0)
    print(lblMin.cget("text"))

def Max_Pressure_Increase():
    print("USER ADJ: increase maximum system pressure: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMax = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_pressure']['GUI_Val']
    increase_decrease(lblMax, True, 0.1,1)
    print(lblMax.cget("text"))

def Max_Pressure_Decrease():
    print("USER ADJ: decrease maximum system temperature: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMax = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_pressure']['GUI_Val']
    increase_decrease(lblMax, False, 0.1,1)
    print(lblMax.cget("text"))

def Min_Pressure_Increase():
    print("USER ADJ: increase minimum system pressure: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMax = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_pressure']['GUI_Val']
    increase_decrease(lblMax, True, 0.1,1)
    print(lblMax.cget("text"))

def Min_Pressure_Decrease():
    print("USER ADJ: decrease minimum system temperature: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblMax = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_pressure']['GUI_Val']
    increase_decrease(lblMax, False, 0.1,1)
    print(lblMax.cget("text"))

def Immersion_Start_Increase():
    print("USER ADJ: increase immersion start time: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblImm = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_start']['GUI_Val']
    increase_time(lblImm, True)
    print(lblImm.cget("text"))

def Immersion_Start_Decrease():
    print("USER ADJ: decrease immersion start time: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblImm = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_start']['GUI_Val']
    increase_time(lblImm, False)
    print(lblImm.cget("text"))

def Immersion_End_Increase():
    print("USER ADJ: increase immersion end time: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblImm = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_end']['GUI_Val']
    increase_time(lblImm, True)
    print(lblImm.cget("text"))

def Immersion_End_Decrease():
    print("USER ADJ: decrease immersion end time: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
    lblImm = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_end']['GUI_Val']
    increase_time(lblImm, False)
    print(lblImm.cget("text"))

def Immersion_SYS():
    lbl_SYS = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['System_mode']['GUI_Val']
    lblImm = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_heater']['GUI_Val'] #On system initialize the library libReturnValve is created and the label's name is created and uploaded to the library on set up of this GUI
    boolManual = check_manual(lbl_SYS)
    if boolManual == True:
        print("USER ADJ: change immersion heater: " + strftime("%d/%m/%Y %H:%M:%S", gmtime()))
        cmdOnOff(lblImm)
        print(lblImm.cget("text"))

class build_GUI:
    def __init__(self, dictInstructions):
        self.quit_sys = False
        self.created_self = False
        self.create_master_window(dictInstructions)

    def quit_GUI(self):
        ####QUIT DEFAULTS
        self.quit_sys = True
        obems_server = dictGlobalInstructions['Threads']['Obems_Execute']
        obems_server.terminate()
        print("quit")

    def restart_GUI(self):
        ### RESET DEFAULTS
        self.quit_sys = True
        time.sleep(60)
        self.quit_sys = False
        strDir = dictGlobalInstructions['User_Inputs']['Code_Location']
        strCode = strDir + './ObemsPulseServer'
        obems = subprocess.Popen([strCode])
        dictGlobalInstructions['Threads']['Obems_Execute'] = obems
        self.initiate_all_threads()
        print("restart")

    def create_master_window(self, dictInstructions):
        self.RootWin = Tk() # Create the main GUI window
        self.RootWin.wm_title("HEATSET: Home Energy Management System")
        lngScreenWidth = dictInstructions['General_Inputs']['Screen_Width']
        lngScreenHeight = dictInstructions['General_Inputs']['Screen_Height']
        self.RootWin.geometry('%dx%d+%d+%d' % (lngScreenWidth, lngScreenHeight, 0, 0))

        # Create TABS
        self.TAB_CONTROL = ttk.Notebook(self.RootWin)
        if dictInstructions['User_Inputs']['Solar_Thermal'] == True:
            self.Solar_Tab = ttk.Frame(self.TAB_CONTROL)
            self.TAB_CONTROL.add(self.Solar_Tab, text='SolarThermal')
            self.populate_solar_tab(dictInstructions)

        if dictInstructions['User_Inputs']['Heat_Pump'] == True:
            self.HP_Tab = ttk.Frame(self.TAB_CONTROL)
            self.TAB_CONTROL.add(self.HP_Tab, text='HeatPump')
            self.populate_HP_tab(dictInstructions)

        if dictInstructions['User_Inputs']['PV'] == True:
            self.PV_Tab = ttk.Frame(self.TAB_CONTROL)
            self.TAB_CONTROL.add(self.PV_Tab, text='PV')
            self.populate_PV_tab(dictInstructions)

        if dictInstructions['User_Inputs']['Battery'] == True:
            self.BAT_Tab = ttk.Frame(self.TAB_CONTROL)
            self.TAB_CONTROL.add(self.BAT_Tab, text='Battery')
            self.populate_BAT_tab(dictInstructions)

        self.TAB_CONTROL.pack(expand=1, fill="both")
        self.time_created = dt.datetime.now()

    def populate_solar_tab(self, dictInstructions):
        #CREATE KEY FORMS WITHIN TAB
        self.frmSolarLogo = Frame(self.Solar_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #self.frmSolarLogo.bind('<Button>', cmd_lightUp)
        self.frmSolarLogo.pack()
        self.frmSolarLogo.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_x'],
                                    height=dictInstructions['General_Inputs']['Logo_height'],
                                    width=dictInstructions['General_Inputs']['Logo_width'])

        self.frmSolarSensors = Frame(self.Solar_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSensors.bind('<Button>', cmd_lightUp)
        self.frmSolarSensors.pack()
        self.frmSolarSensors.place(y=dictInstructions['Solar_Inputs']['GUI_params']['Sensor_Section']['Sensor_y'],
                                    x=dictInstructions['Solar_Inputs']['GUI_params']['Sensor_Section']['Sensor_x'],
                                    height=dictInstructions['Solar_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height'],
                                    width = dictInstructions['Solar_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width'])

        self.frmSolarSYS = Frame(self.Solar_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSYS.bind('<Button>',cmd_lightUp)
        self.frmSolarSYS.pack()
        self.frmSolarSYS.place(y=dictInstructions['Solar_Inputs']['GUI_params']['System_Section']['SYS_y'],
                                    x=dictInstructions['Solar_Inputs']['GUI_params']['System_Section']['SYS_x'],
                                    height=dictInstructions['Solar_Inputs']['GUI_params']['System_Section']['SYSFm_height'],
                                    width = dictInstructions['Solar_Inputs']['GUI_params']['System_Section']['SYSFm_width'])

        self.frmSolarGraph = Frame(self.Solar_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSolarGraph.bind('<Button>',cmd_lightUp)
        self.frmSolarGraph.pack()
        self.frmSolarGraph.place(y=dictInstructions['Solar_Inputs']['GUI_params']['Graph_Section']['Graph_y'],
                                    x=dictInstructions['Solar_Inputs']['GUI_params']['Graph_Section']['Graph_x'],
                                    height=dictInstructions['Solar_Inputs']['GUI_params']['Graph_Section']['GraphFm_height'],
                                    width = dictInstructions['Solar_Inputs']['GUI_params']['Graph_Section']['GraphFm_width'])

        # Place HeatSet Logo
        strImageLoc = str(dictInstructions['Solar_Inputs']['Defaults']['Logo'])
        self.tkSolarImage = ImageTk.PhotoImage(Image.open(strImageLoc))
        self.lblSolarImgLogo = Label(self.frmSolarLogo, image=self.tkSolarImage)
        #lblLogo.bind('<Button>',cmd_lightUp)
        self.lblSolarImgLogo.pack(side = "bottom", fill = "both", expand = "yes")
        self.lblSolarImgLogo.place(x=0,y=0)

        #Set up restart button
        self.btnSolarRestart = Button(self.frmSolarLogo,
                                    text="RESTART",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.restart_GUI)
        #btnRestart.bind('<Button>',cmd_lightUp)
        lngFreeSapce = dictInstructions['General_Inputs']['Logo_width'] - 160 #Logo width
        lngRestartWidth = lngFreeSapce / 3
        self.btnSolarRestart.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngRestartWidth - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngRestartWidth)

        self.btnSolarQuit = Button(self.frmSolarLogo,
                                    text="QUIT",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.quit_GUI)
        #self.btnSolarQuit.bind('<Button>',cmd_lightUp)
        self.btnSolarQuit.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngRestartWidth * 2 - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngRestartWidth)

        # Sensor & SYS section relative measurements
        self.lstSolarSensOrderByID = dictInstructions['Solar_Inputs']['GUI_Sections'][0]
        self.lstSolarSysOrderByID = dictInstructions['Solar_Inputs']['GUI_Sections'][1]
        self.frmSolarSensorHeight = dictInstructions['Solar_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height']
        self.frmSolarSensorsWidth = dictInstructions['Solar_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width']
        self.frmSolarSYSWidth = dictInstructions['Solar_Inputs']['GUI_params']['System_Section']['SYSFm_width']
        self.frmSolarSYSHeight = dictInstructions['Solar_Inputs']['GUI_params']['System_Section']['SYSFm_height']

        SensCounter = 0
        SysCounter = 0
        for key in dictInstructions['Solar_Inputs']['GUI_Information']:
            for i in range(0, len(self.lstSolarSensOrderByID)):
                if dictInstructions['Solar_Inputs']['GUI_Information'][key]['ID'] == self.lstSolarSensOrderByID[i]:
                    if dictInstructions['Solar_Inputs']['GUI_Information'][key]['Include?'] == True:
                        SensCounter += 1
            for i in range(0, len(self.lstSolarSysOrderByID)):
                if dictInstructions['Solar_Inputs']['GUI_Information'][key]['ID'] == self.lstSolarSysOrderByID[i]:
                    if dictInstructions['Solar_Inputs']['GUI_Information'][key]['Include?'] == True:
                        SysCounter += 1

        self.dblSolarSensHeight = int((self.frmSolarSensorHeight-10) / SensCounter)
        self.dblSolarSensWidthLBL = int((self.frmSolarSensorsWidth-10) * 2/3)
        self.dblSolarSensWidthVal = int((self.frmSolarSensorsWidth-10) * 1/3)
        self.dblSolarSYSWidthLBL = int((self.frmSolarSYSWidth-10) * 1.5/3)
        self.dblSolarSYSWidthVal = int((self.frmSolarSYSWidth-10) * 0.8/3)
        self.dblSolarSYSWidthCmd = int((self.frmSolarSYSWidth-10) * 0.7/3)
        self.dblSolarSYSHeight = int((self.frmSolarSYSHeight-10) / (SysCounter+3)) #Plus 3 as need last section to be free for final command buttons

        SensCounter = 0
        # Create sensor section labels and outputs and update global dictionary
        for i in range(0, len(self.lstSolarSensOrderByID)): #Loop through all of the global library lists as calibrated within System_Initialize
            boolContinue = False
            for key in dictInstructions['Solar_Inputs']['GUI_Information']:
                if boolContinue == True:
                    continue
                if dictInstructions['Solar_Inputs']['GUI_Information'][key]['ID'] == self.lstSolarSensOrderByID[i]: #if the ID of the library item
                    if dictInstructions['Solar_Inputs']['GUI_Information'][key]['Include?'] == True:
                        lblTitle = Label(self.frmSolarSensors,
                                        text=dictInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Label'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        anchor=W) #This is the label that provides the description to the value
                        #lblTitle.bind('<Button>', cmd_lightUp)
                        lblTitle.place(y=(self.dblSolarSensHeight * SensCounter),
                                        x=5,
                                        height=self.dblSolarSensHeight,
                                        width=self.dblSolarSensWidthLBL)
                        lblVal = Label(self.frmSolarSensors,
                                        text=dictInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Default'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        relief=SUNKEN)
                        #lblVal.bind('<Button>', cmd_lightUp)
                        lblVal.place(y=(self.dblSolarSensHeight * SensCounter),
                                        x=self.dblSolarSensWidthLBL,
                                        height=self.dblSolarSensHeight,
                                        width = self.dblSolarSensWidthVal)
                        dictInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Local level insturctions
                        dictGlobalInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Module level instructions
                        boolContinue = True
                        SensCounter += 1
                        continue
        if dictInstructions['User_Inputs']['Solar_Control'] == True:
            SysCounter = 0
            # Create SYS section labels and outputs and update global dictionary
            for i in range(0, len(self.lstSolarSysOrderByID)): #Loop through each library within the respective list
                boolContinue = False
                for key in dictInstructions['Solar_Inputs']['GUI_Information']: #The system_initialize allows the GUI to be calibrated as required
                    if dictInstructions['Solar_Inputs']['GUI_Information'][key]['ID'] == self.lstSolarSysOrderByID[i]: #if the ID of the library item
                        if dictInstructions['Solar_Inputs']['GUI_Information'][key]['Include?'] == True:
                            lblTitle = Label(self.frmSolarSYS,
                                            text=dictInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Label'],
                                            font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                            anchor=W) #This is the label that provides the description to the value
                            lblTitle.place(y=(self.dblSolarSYSHeight * SysCounter),
                                                x=5,
                                                height=self.dblSolarSYSHeight,
                                                width=self.dblSolarSYSWidthLBL)
                            #lblTitle.bind('<Button>', cmd_lightUp)
                            lblVal = Label(self.frmSolarSYS,
                                            text=dictInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Default'],
                                            font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                            relief=SUNKEN)
                            #lblVal.bind('<Button>', cmd_lightUp)
                            lblVal.place(y=(self.dblSolarSYSHeight * SysCounter),
                                x=self.dblSolarSYSWidthLBL,
                                height=self.dblSolarSYSHeight,
                                width = self.dblSolarSYSWidthVal)
                            dictInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Local level insturctions
                            dictGlobalInstructions['Solar_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Module level instructions
                            cmdCnt = dictInstructions['Solar_Inputs']['GUI_Information'][key]['cmd_count']
                            widthTemp = int(self.dblSolarSYSWidthCmd / cmdCnt)
                            if cmdCnt == 1:
                                txtCmd0 = "CHANGE"
                                lstTxt = [txtCmd0]
                            else:
                                txtCmd0 = "\N{black medium up-pointing triangle}" #Up symbol
                                txtCmd1 = "\N{black medium down-pointing triangle}" #down subol
                                lstTxt = [txtCmd0, txtCmd1]
                            for j in range(0,cmdCnt):
                                lblCmd = Button(self.frmSolarSYS,
                                                text=lstTxt[j],
                                                font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                                command=dictInstructions['Solar_Inputs']['GUI_Information'][key]['cmd_def' + str(j+1)])
                                lblCmd.place(y=(self.dblSolarSYSHeight * SysCounter),
                                                x=self.dblSolarSYSWidthLBL+self.dblSolarSYSWidthVal+widthTemp*j,
                                                height=self.dblSolarSYSHeight, width=widthTemp)
                                dictInstructions['Solar_Inputs']['GUI_Information'][key]['cmd_Val' + str(j+1)] = lblCmd
                            boolContinue = True
                            SysCounter += 1
                            continue

            #Update_Commands in global instructions
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['cmd_def'] = pump_on_off #global dictionary update
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Flush_Valve']['cmd_def'] = valve_on_off
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['System_mode']['cmd_def1'] = cmdMode
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_start']['cmd_def1'] = Immersion_Start_Increase
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_start']['cmd_def2'] = Immersion_Start_Decrease
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_end']['cmd_def1'] = Immersion_End_Increase
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_end']['cmd_def2'] = Immersion_End_Decrease
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Immersion_heater']['cmd_def'] = Immersion_SYS
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_DeltaT']['cmd_def1'] = Target_Temp_Increase
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_DeltaT']['cmd_def2'] = Target_Temp_Decrease
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_Temp']['cmd_def1'] = Max_Temp_Increase
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_Temp']['cmd_def2'] = Max_Temp_Decrease
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_Temp']['cmd_def1'] = Min_Temp_Increase
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_Temp']['cmd_def2'] = Min_Temp_Decrease
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_pressure']['cmd_def1'] = Max_Pressure_Increase
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_pressure']['cmd_def2'] = Max_Pressure_Decrease
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_pressure']['cmd_def1'] = Min_Pressure_Increase
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_pressure']['cmd_def2'] = Min_Pressure_Decrease

            #Create final buttons at bottom left of solar tab
            bytButtonsAtBottom = 4
            yStart = self.dblSolarSensHeight + self.dblSolarSYSHeight * (SysCounter - 1) + 5
            cmdPump = Button(self.frmSolarSYS,
                                text=dictInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['GUI_Label'],
                                font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                command=dictInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['cmd_def'])
            cmdPump.place(y=yStart,
                                x=5,
                                width = ((self.frmSolarSensorsWidth-10)/bytButtonsAtBottom-10),
                                height = (self.frmSolarSYSHeight - yStart - 35))

            cmdImmersion = Button(self.frmSolarSYS,
                                text=dictInstructions['Solar_Inputs']['GUI_Information']['Immersion_heater']['GUI_Label'],
                                font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                command=dictInstructions['Solar_Inputs']['GUI_Information']['Immersion_heater']['cmd_def'])
            cmdImmersion.place(y=yStart,
                                x=(self.frmSolarSYSWidth-10)/(bytButtonsAtBottom)*1+5,
                                width = ((self.frmSolarSensorsWidth-10)/bytButtonsAtBottom-10),
                                height = (self.frmSolarSYSHeight - yStart - 35))

            cmdFlush = Button(self.frmSolarSYS,
                                text=dictInstructions['Solar_Inputs']['GUI_Information']['Flush_Valve']['GUI_Label'],
                                font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                command=dictInstructions['Solar_Inputs']['GUI_Information']['Flush_Valve']['cmd_def'])
            cmdFlush.place(y=yStart,
                                x=(self.frmSolarSYSWidth-10)/(bytButtonsAtBottom)*2+5,
                                width = ((self.frmSolarSYSWidth-10)/bytButtonsAtBottom-10),
                                height = (self.frmSolarSYSHeight - yStart - 35))

            cmdScreenOff = Button(self.frmSolarSYS,
                                text="Screen OFF",
                                font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                command=None) #cmd_lightOff)
            cmdScreenOff.place(y=yStart,
                                x=(self.frmSolarSYSWidth-10)/(bytButtonsAtBottom)*3+5,
                                width = ((self.frmSolarSYSWidth-10)/bytButtonsAtBottom-10),
                                height = (self.frmSolarSYSHeight - yStart - 35))
        else:
            #If solar control has not been set to true then include the thermal output gauge instead
            self.Solar_Gauge = cht_plt.GUI_gauge(dictInstructions['Solar_Inputs']['Gauge_params'], self.frmSolarSYS)

        #Insert Solar Graph
        self.Solar_Graph = cht_plt.GUI_graph(dictInstructions['Solar_Inputs']['Graph_params'], self.frmSolarGraph)

        if dictInstructions['User_Inputs']['Solar_Control'] == True:
            #Loop through all system buttons per list lstSolarSysOrderByID defined in System_Initialize
            for i in range(0,len(self.lstSolarSysOrderByID)): #The system_initialize allows the GUI to be calibrated as required
                for key in dictGlobalInstructions['Solar_Inputs']['GUI_Information']: #Loop through each solar GUI dictionary
                    if dictInstructions['Solar_Inputs']['GUI_Information'][key]['Include?'] == True: #If the user has selected a non-pressurised system or no immersion heater in the tank then this adjusts for that
                        if dictGlobalInstructions['Solar_Inputs']['GUI_Information'][key]['ID'] == self.lstSolarSysOrderByID[i]: #if the ID of the library item
                            cmdCnt = dictGlobalInstructions['Solar_Inputs']['GUI_Information'][key]['cmd_count']
                            for j in range(0,cmdCnt):
                                lbl = dictGlobalInstructions['Solar_Inputs']['GUI_Information'][key]['cmd_Val'+ str(1+j)]
                                lbl.config(command=dictGlobalInstructions['Solar_Inputs']['GUI_Information'][key]['cmd_def' + str(1+j)])

    def populate_HP_tab(self, dictInstructions):
        #CREATE KEY FORMS WITHIN TAB
        self.frmHPLogo = Frame(self.HP_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #self.frmHPLogo.bind('<Button>', cmd_lightUp)
        self.frmHPLogo.pack()
        self.frmHPLogo.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_x'],
                                    height=dictInstructions['General_Inputs']['Logo_height'],
                                    width=dictInstructions['General_Inputs']['Logo_width'])

        self.frmHPSensors = Frame(self.HP_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmHPSensors.bind('<Button>', cmd_lightUp)
        self.frmHPSensors.pack()
        self.frmHPSensors.place(y=dictInstructions['HP_Inputs']['GUI_params']['Sensor_Section']['Sensor_y'],
                                    x=dictInstructions['HP_Inputs']['GUI_params']['Sensor_Section']['Sensor_x'],
                                    height=dictInstructions['HP_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height'],
                                    width = dictInstructions['HP_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width'])

        if dictInstructions['User_Inputs']['Heat_Pump_Control'] == True:
            self.frmHPSYS = Frame(self.HP_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
            #frmSYS.bind('<Button>',cmd_lightUp)
            self.frmHPSYS.pack()
            self.frmHPSYS.place(y=dictInstructions['HP_Inputs']['GUI_params']['System_Section']['SYS_y'],
                                        x=dictInstructions['HP_Inputs']['GUI_params']['System_Section']['SYS_x'],
                                        height=dictInstructions['HP_Inputs']['GUI_params']['System_Section']['SYSFm_height'],
                                        width = dictInstructions['HP_Inputs']['GUI_params']['System_Section']['SYSFm_width'])

        self.frmHPGraph = Frame(self.HP_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSolarGraph.bind('<Button>',cmd_lightUp)
        self.frmHPGraph.pack()
        self.frmHPGraph.place(y=dictInstructions['HP_Inputs']['GUI_params']['Graph_Section']['Graph_y'],
                                    x=dictInstructions['HP_Inputs']['GUI_params']['Graph_Section']['Graph_x'],
                                    height=dictInstructions['HP_Inputs']['GUI_params']['Graph_Section']['GraphFm_height'],
                                    width = dictInstructions['HP_Inputs']['GUI_params']['Graph_Section']['GraphFm_width'])

        self.frmHPGauge = Frame(self.HP_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSolarGraph.bind('<Button>',cmd_lightUp)
        self.frmHPGauge.pack()
        self.frmHPGauge.place(y=dictInstructions['HP_Inputs']['GUI_params']['Gauge_Section']['Gauge_y'],
                                    x=dictInstructions['HP_Inputs']['GUI_params']['Gauge_Section']['Gauge_x'],
                                    height=dictInstructions['HP_Inputs']['GUI_params']['Gauge_Section']['Fm_height'],
                                    width = dictInstructions['HP_Inputs']['GUI_params']['Gauge_Section']['Fm_width'])

        # Place HeatSet Logo
        strImageLoc = str(dictInstructions['HP_Inputs']['Defaults']['Logo'])
        self.tkHPImage = ImageTk.PhotoImage(Image.open(strImageLoc))
        self.lblHPImgLogo = Label(self.frmHPLogo, image=self.tkHPImage)
        #lblLogo.bind('<Button>',cmd_lightUp)
        self.lblHPImgLogo.pack(side = "bottom", fill = "both", expand = "yes")
        self.lblHPImgLogo.place(x=0,y=0)

        #Set up restart button
        self.btnHPRestart = Button(self.frmHPLogo,
                                    text="RESTART",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.restart_GUI)
        #btnRestart.bind('<Button>',cmd_lightUp)
        lngHPFreeSapce = dictInstructions['General_Inputs']['Logo_width'] - 160 #Logo width
        lngHPRestartWidth = lngHPFreeSapce / 3
        self.btnHPRestart.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngHPRestartWidth - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngHPRestartWidth)

        self.btnHPQuit = Button(self.frmHPLogo,
                                    text="QUIT",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.quit_GUI)
        #self.btnSolarQuit.bind('<Button>',cmd_lightUp)
        self.btnHPQuit.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngHPRestartWidth * 2 - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngHPRestartWidth)

       # Sensor & SYS section relative measurements
        self.lstHPSensOrderByID = dictInstructions['HP_Inputs']['GUI_Sections'][0]
        self.lstHPSysOrderByID = dictInstructions['HP_Inputs']['GUI_Sections'][1]
        self.frmHPSensorHeight = dictInstructions['HP_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height']
        self.frmHPSensorsWidth = dictInstructions['HP_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width']
        self.frmHPSYSWidth = dictInstructions['HP_Inputs']['GUI_params']['System_Section']['SYSFm_width']
        self.frmHPSYSHeight = dictInstructions['HP_Inputs']['GUI_params']['System_Section']['SYSFm_height']

        SensCounter = 0
        SysCounter = 0
        for key in dictInstructions['HP_Inputs']['GUI_Information']:
            for i in range(0, len(self.lstHPSensOrderByID)):
                if dictInstructions['HP_Inputs']['GUI_Information'][key]['ID'] == self.lstHPSensOrderByID[i]:
                    if dictInstructions['HP_Inputs']['GUI_Information'][key]['Include?'] == True:
                        SensCounter += 1
            for i in range(0, len(self.lstHPSysOrderByID)):
                if dictInstructions['HP_Inputs']['GUI_Information'][key]['ID'] == self.lstHPSysOrderByID[i]:
                    if dictInstructions['HP_Inputs']['GUI_Information'][key]['Include?'] == True:
                        SysCounter += 1

        self.dblHPSensHeight = int((self.frmHPSensorHeight-10) / SensCounter)
        self.dblHPSensWidthLBL = int((self.frmHPSensorsWidth-10) * 2/3)
        self.dblHPSensWidthVal = int((self.frmHPSensorsWidth-10) * 1/3)
        self.dblHPSYSWidthLBL = int((self.frmHPSYSWidth-10) * 1.5/3)
        self.dblHPSYSWidthVal = int((self.frmHPSYSWidth-10) * 0.8/3)
        self.dblHPSYSWidthCmd = int((self.frmHPSYSWidth-10) * 0.7/3)
        self.dblHPSYSHeight = int((self.frmHPSYSHeight-10) / SysCounter)

        SensCounter = 0
        # Create sensor section labels and outputs and update global dictionary
        for i in range(0, len(self.lstHPSensOrderByID)): #Loop through all of the global library lists as calibrated within System_Initialize
            boolContinue = False
            for key in dictInstructions['HP_Inputs']['GUI_Information']:
                if boolContinue == True:
                    continue
                if dictInstructions['HP_Inputs']['GUI_Information'][key]['ID'] == self.lstHPSensOrderByID[i]: #if the ID of the library item
                    if dictInstructions['HP_Inputs']['GUI_Information'][key]['Include?'] == True:
                        lblTitle = Label(self.frmHPSensors,
                                        text=dictInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Label'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        anchor=W) #This is the label that provides the description to the value
                        #lblTitle.bind('<Button>', cmd_lightUp)
                        lblTitle.place(y=(self.dblHPSensHeight * SensCounter),
                                        x=5,
                                        height=self.dblHPSensHeight,
                                        width=self.dblHPSensWidthLBL)
                        lblVal = Label(self.frmHPSensors,
                                        text=dictInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Default'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        relief=SUNKEN)
                        #lblVal.bind('<Button>', cmd_lightUp)
                        lblVal.place(y=(self.dblHPSensHeight * SensCounter),
                                        x=self.dblHPSensWidthLBL,
                                        height=self.dblHPSensHeight,
                                        width = self.dblHPSensWidthVal)
                        dictInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Local level insturctions
                        dictGlobalInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Module level instructions
                        boolContinue = True
                        SensCounter += 1
                        continue

        if dictInstructions['User_Inputs']['Heat_Pump_Control'] == True:
            SysCounter = 0
            # Create SYS section labels and outputs and update global dictionary
            for i in range(0, len(self.lstHPSysOrderByID)): #Loop through each library within the respective list
                boolContinue = False
                for key in dictInstructions['HP_Inputs']['GUI_Information']: #The system_initialize allows the GUI to be calibrated as required
                    if dictInstructions['HP_Inputs']['GUI_Information'][key]['ID'] == self.lstHPSysOrderByID[i]: #if the ID of the library item
                        if dictInstructions['HP_Inputs']['GUI_Information'][key]['Include?'] == True:
                            lblTitle = Label(self.frmHPSYS,
                                            text=dictInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Label'],
                                            font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                            anchor=W) #This is the label that provides the description to the value
                            lblTitle.place(y=(self.dblHPSYSHeight * SysCounter),
                                                x=5,
                                                height=self.dblHPSYSHeight,
                                                width=self.dblHPSYSWidthLBL)
                            #lblTitle.bind('<Button>', cmd_lightUp)
                            lblVal = Label(self.frmHPSYS,
                                            text=dictInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Default'],
                                            font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                            relief=SUNKEN)
                            #lblVal.bind('<Button>', cmd_lightUp)
                            lblVal.place(y=(self.dblHPSYSHeight * SysCounter),
                                x=self.dblHPSYSWidthLBL,
                                height=self.dblHPSYSHeight,
                                width = self.dblHPSYSWidthVal)
                            dictInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Local level insturctions
                            dictGlobalInstructions['HP_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Module level instructions
                            cmdCnt = dictInstructions['HP_Inputs']['GUI_Information'][key]['cmd_count']
                            widthTemp = int(self.dblHPSYSWidthCmd / cmdCnt)
                            if cmdCnt == 1:
                                txtCmd0 = "CHANGE"
                                lstTxt = [txtCmd0]
                            else:
                                txtCmd0 = "\N{black medium up-pointing triangle}" #Up symbol
                                txtCmd1 = "\N{black medium down-pointing triangle}" #down subol
                                lstTxt = [txtCmd0, txtCmd1]
                            for j in range(0,cmdCnt):
                                lblCmd = Button(self.frmHPSYS,
                                                text=lstTxt[j],
                                                font=(dictInstructions['General_Inputs']['Font'],
                                                    dictInstructions['General_Inputs']['Font_size']),
                                                command=dictInstructions['HP_Inputs']['GUI_Information'][key]['cmd_def' + str(j+1)])
                                lblCmd.place(y=(self.dblHPSYSHeight * SysCounter),
                                                x=self.dblHPSYSWidthLBL+self.dblHPSYSWidthVal+widthTemp*j,
                                                height=self.dblHPSYSHeight, width=widthTemp)
                                dictInstructions['HP_Inputs']['GUI_Information'][key]['cmd_Val' + str(j+1)] = lblCmd
                            boolContinue = True
                            SysCounter += 1
                            continue

            #Update_Commands in global instructions
            dictGlobalInstructions['HP_Inputs']['GUI_Information']['HP_On_Off']['cmd_def1'] = HP_on_off #global dictionary update

        #Insert HP Graph and gauge
        self.HP_Graph = cht_plt.GUI_graph(dictInstructions['HP_Inputs']['Graph_params'], self.frmHPGraph)
        self.HP_Gauge = cht_plt.GUI_gauge(dictInstructions['HP_Inputs']['Gauge_params'], self.frmHPGauge)

        if dictInstructions['User_Inputs']['Heat_Pump_Control'] == True:
            #Loop through all system buttons per list lstHPSysOrderByID defined in System_Initialize
            for i in range(0,len(self.lstHPSysOrderByID)): #The system_initialize allows the GUI to be calibrated as required
                for key in dictGlobalInstructions['HP_Inputs']['GUI_Information']: #Loop through each solar GUI dictionary
                    if dictInstructions['HP_Inputs']['GUI_Information'][key]['Include?'] == True: #If the user has selected a non-pressurised system or no immersion heater in the tank then this adjusts for that
                        if dictGlobalInstructions['HP_Inputs']['GUI_Information'][key]['ID'] == self.lstHPSysOrderByID[i]: #if the ID of the library item
                            cmdCnt = dictGlobalInstructions['HP_Inputs']['GUI_Information'][key]['cmd_count']
                            for j in range(0,cmdCnt):
                                lbl = dictGlobalInstructions['HP_Inputs']['GUI_Information'][key]['cmd_Val'+ str(1+j)]
                                lbl.config(command=dictGlobalInstructions['HP_Inputs']['GUI_Information'][key]['cmd_def' + str(1+j)])

    def populate_PV_tab(self, dictInstructions):
        #CREATE KEY FORMS WITHIN TAB
        self.frmPVLogo = Frame(self.PV_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #self.frmPVLogo.bind('<Button>', cmd_lightUp)
        self.frmPVLogo.pack()
        self.frmPVLogo.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_x'],
                                    height=dictInstructions['General_Inputs']['Logo_height'],
                                    width=dictInstructions['General_Inputs']['Logo_width'])

        self.frmPVSensors = Frame(self.PV_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmPVSensors.bind('<Button>', cmd_lightUp)
        self.frmPVSensors.pack()
        self.frmPVSensors.place(y=dictInstructions['PV_Inputs']['GUI_params']['Sensor_Section']['Sensor_y'],
                                    x=dictInstructions['PV_Inputs']['GUI_params']['Sensor_Section']['Sensor_x'],
                                    height=dictInstructions['PV_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height'],
                                    width = dictInstructions['PV_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width'])

        self.frmPVGraph = Frame(self.PV_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSolarGraph.bind('<Button>',cmd_lightUp)
        self.frmPVGraph.pack()
        self.frmPVGraph.place(y=dictInstructions['PV_Inputs']['GUI_params']['Graph_Section']['Graph_y'],
                                    x=dictInstructions['PV_Inputs']['GUI_params']['Graph_Section']['Graph_x'],
                                    height=dictInstructions['PV_Inputs']['GUI_params']['Graph_Section']['GraphFm_height'],
                                    width = dictInstructions['PV_Inputs']['GUI_params']['Graph_Section']['GraphFm_width'])

        self.frmPVGauge = Frame(self.PV_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSolarGraph.bind('<Button>',cmd_lightUp)
        self.frmPVGauge.pack()
        self.frmPVGauge.place(y=dictInstructions['PV_Inputs']['GUI_params']['Gauge_Section']['Gauge_y'],
                                    x=dictInstructions['PV_Inputs']['GUI_params']['Gauge_Section']['Gauge_x'],
                                    height=dictInstructions['PV_Inputs']['GUI_params']['Gauge_Section']['Fm_height'],
                                    width = dictInstructions['PV_Inputs']['GUI_params']['Gauge_Section']['Fm_width'])

        # Place HeatSet Logo
        strImageLoc = str(dictInstructions['PV_Inputs']['Defaults']['Logo'])
        self.tkPVImage = ImageTk.PhotoImage(Image.open(strImageLoc))
        self.lblPVImgLogo = Label(self.frmPVLogo, image=self.tkPVImage)
        #lblLogo.bind('<Button>',cmd_lightUp)
        self.lblPVImgLogo.pack(side = "bottom", fill = "both", expand = "yes")
        self.lblPVImgLogo.place(x=0,y=0)

        #Set up restart button
        self.btnPVRestart = Button(self.frmPVLogo,
                                    text="RESTART",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.restart_GUI)
        #btnRestart.bind('<Button>',cmd_lightUp)
        lngPVFreeSapce = dictInstructions['General_Inputs']['Logo_width'] - 160 #Logo width
        lngPVRestartWidth = lngPVFreeSapce / 3
        self.btnPVRestart.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngPVRestartWidth - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngPVRestartWidth)

        self.btnPVQuit = Button(self.frmPVLogo,
                                    text="QUIT",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.quit_GUI)
        #self.btnSolarQuit.bind('<Button>',cmd_lightUp)
        self.btnPVQuit.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngPVRestartWidth * 2 - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngPVRestartWidth)

       # Sensor  section relative measurements
        self.lstPVSensOrderByID = dictInstructions['PV_Inputs']['GUI_Sections'][0]
        self.frmPVSensorHeight = dictInstructions['PV_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height']
        self.frmPVSensorsWidth = dictInstructions['PV_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width']

        SensCounter = 0
        for key in dictInstructions['PV_Inputs']['GUI_Information']:
            for i in range(0, len(self.lstPVSensOrderByID)):
                if dictInstructions['PV_Inputs']['GUI_Information'][key]['ID'] == self.lstPVSensOrderByID[i]:
                    if dictInstructions['PV_Inputs']['GUI_Information'][key]['Include?'] == True:
                        SensCounter += 1

        self.dblPVSensHeight = int((self.frmPVSensorHeight-10) / SensCounter)
        self.dblPVSensWidthLBL = int((self.frmPVSensorsWidth-10) * 2/3)
        self.dblPVSensWidthVal = int((self.frmPVSensorsWidth-10) * 1/3)

        SensCounter = 0
        # Create sensor section labels and outputs and update global dictionary
        for i in range(0, len(self.lstPVSensOrderByID)): #Loop through all of the global library lists as calibrated within System_Initialize
            boolContinue = False
            for key in dictInstructions['PV_Inputs']['GUI_Information']:
                if boolContinue == True:
                    continue
                if dictInstructions['PV_Inputs']['GUI_Information'][key]['ID'] == self.lstPVSensOrderByID[i]: #if the ID of the library item
                    if dictInstructions['PV_Inputs']['GUI_Information'][key]['Include?'] == True:
                        lblTitle = Label(self.frmPVSensors,
                                        text=dictInstructions['PV_Inputs']['GUI_Information'][key]['GUI_Label'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        anchor=W) #This is the label that provides the description to the value
                        #lblTitle.bind('<Button>', cmd_lightUp)
                        lblTitle.place(y=(self.dblPVSensHeight * SensCounter),
                                        x=5,
                                        height=self.dblPVSensHeight,
                                        width=self.dblPVSensWidthLBL)
                        lblVal = Label(self.frmPVSensors,
                                        text=dictInstructions['PV_Inputs']['GUI_Information'][key]['GUI_Default'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        relief=SUNKEN)
                        #lblVal.bind('<Button>', cmd_lightUp)
                        lblVal.place(y=(self.dblPVSensHeight * SensCounter),
                                        x=self.dblPVSensWidthLBL,
                                        height=self.dblPVSensHeight,
                                        width = self.dblPVSensWidthVal)
                        dictInstructions['PV_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Local level insturctions
                        dictGlobalInstructions['PV_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Module level instructions
                        boolContinue = True
                        SensCounter += 1
                        continue

        #Insert PV Graph and gauge
        self.PV_Graph = cht_plt.GUI_graph(dictInstructions['PV_Inputs']['Graph_params'], self.frmPVGraph)
        self.PV_Gauge = cht_plt.GUI_gauge(dictInstructions['PV_Inputs']['Gauge_params'], self.frmPVGauge)

    def populate_BAT_tab(self, dictInstructions):
        #CREATE KEY FORMS WITHIN TAB
        self.frmBATLogo = Frame(self.BAT_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #self.frmBATLogo.bind('<Button>', cmd_lightUp)
        self.frmBATLogo.pack()
        self.frmBATLogo.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_x'],
                                    height=dictInstructions['General_Inputs']['Logo_height'],
                                    width=dictInstructions['General_Inputs']['Logo_width'])

        self.frmBATSensors = Frame(self.BAT_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmBATSensors.bind('<Button>', cmd_lightUp)
        self.frmBATSensors.pack()
        self.frmBATSensors.place(y=dictInstructions['BAT_Inputs']['GUI_params']['Sensor_Section']['Sensor_y'],
                                    x=dictInstructions['BAT_Inputs']['GUI_params']['Sensor_Section']['Sensor_x'],
                                    height=dictInstructions['BAT_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height'],
                                    width = dictInstructions['BAT_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width'])

        self.frmBATGraph = Frame(self.BAT_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSolarGraph.bind('<Button>',cmd_lightUp)
        self.frmBATGraph.pack()
        self.frmBATGraph.place(y=dictInstructions['BAT_Inputs']['GUI_params']['Graph_Section']['Graph_y'],
                                    x=dictInstructions['BAT_Inputs']['GUI_params']['Graph_Section']['Graph_x'],
                                    height=dictInstructions['BAT_Inputs']['GUI_params']['Graph_Section']['GraphFm_height'],
                                    width = dictInstructions['BAT_Inputs']['GUI_params']['Graph_Section']['GraphFm_width'])

        self.frmBATGauge = Frame(self.BAT_Tab, pady=5, padx=5, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        #frmSolarGraph.bind('<Button>',cmd_lightUp)
        self.frmBATGauge.pack()
        self.frmBATGauge.place(y=dictInstructions['BAT_Inputs']['GUI_params']['Gauge_Section']['Gauge_y'],
                                    x=dictInstructions['BAT_Inputs']['GUI_params']['Gauge_Section']['Gauge_x'],
                                    height=dictInstructions['BAT_Inputs']['GUI_params']['Gauge_Section']['Fm_height'],
                                    width = dictInstructions['BAT_Inputs']['GUI_params']['Gauge_Section']['Fm_width'])

        # Place HeatSet Logo
        strImageLoc = str(dictInstructions['BAT_Inputs']['Defaults']['Logo'])
        self.tkBATImage = ImageTk.PhotoImage(Image.open(strImageLoc))
        self.lblBATImgLogo = Label(self.frmBATLogo, image=self.tkBATImage)
        #lblLogo.bind('<Button>',cmd_lightUp)
        self.lblBATImgLogo.pack(side = "bottom", fill = "both", expand = "yes")
        self.lblBATImgLogo.place(x=0,y=0)

        #Set up restart button
        self.btnBATRestart = Button(self.frmBATLogo,
                                    text="RESTART",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.restart_GUI)
        #btnRestart.bind('<Button>',cmd_lightUp)
        lngBATFreeSapce = dictInstructions['General_Inputs']['Logo_width'] - 160 #Logo width
        lngBATRestartWidth = lngBATFreeSapce / 3
        self.btnBATRestart.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngBATRestartWidth - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngBATRestartWidth)

        self.btnBATQuit = Button(self.frmBATLogo,
                                    text="QUIT",
                                    font=(dictInstructions['General_Inputs']['Font'],
                                            dictInstructions['General_Inputs']['Font_size']),
                                    command=self.quit_GUI)
        #self.btnSolarQuit.bind('<Button>',cmd_lightUp)
        self.btnBATQuit.place(y=dictInstructions['General_Inputs']['Logo_y'],
                                    x=dictInstructions['General_Inputs']['Logo_width'] - lngBATRestartWidth * 2 - 10,
                                    height = 40 * dictInstructions['General_Inputs']['Height_ADJ'],
                                    width = lngBATRestartWidth)

       # Sensor  section relative measurements
        self.lstBATSensOrderByID = dictInstructions['BAT_Inputs']['GUI_Sections'][0]
        self.frmBATSensorHeight = dictInstructions['BAT_Inputs']['GUI_params']['Sensor_Section']['SensorFm_height']
        self.frmBATSensorsWidth = dictInstructions['BAT_Inputs']['GUI_params']['Sensor_Section']['SensorFm_width']

        SensCounter = 0
        for key in dictInstructions['BAT_Inputs']['GUI_Information']:
            for i in range(0, len(self.lstBATSensOrderByID)):
                if dictInstructions['BAT_Inputs']['GUI_Information'][key]['ID'] == self.lstBATSensOrderByID[i]:
                    if dictInstructions['BAT_Inputs']['GUI_Information'][key]['Include?'] == True:
                        SensCounter += 1

        self.dblBATSensHeight = int((self.frmBATSensorHeight-10) / SensCounter)
        self.dblBATSensWidthLBL = int((self.frmBATSensorsWidth-10) * 2/3)
        self.dblBATSensWidthVal = int((self.frmBATSensorsWidth-10) * 1/3)

        SensCounter = 0
        # Create sensor section labels and outputs and update global dictionary
        for i in range(0, len(self.lstBATSensOrderByID)): #Loop through all of the global library lists as calibrated within System_Initialize
            boolContinue = False
            for key in dictInstructions['BAT_Inputs']['GUI_Information']:
                if boolContinue == True:
                    continue
                if dictInstructions['BAT_Inputs']['GUI_Information'][key]['ID'] == self.lstBATSensOrderByID[i]: #if the ID of the library item
                    if dictInstructions['BAT_Inputs']['GUI_Information'][key]['Include?'] == True:
                        lblTitle = Label(self.frmBATSensors,
                                        text=dictInstructions['BAT_Inputs']['GUI_Information'][key]['GUI_Label'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        anchor=W) #This is the label that provides the description to the value
                        #lblTitle.bind('<Button>', cmd_lightUp)
                        lblTitle.place(y=(self.dblBATSensHeight * SensCounter),
                                        x=5,
                                        height=self.dblBATSensHeight,
                                        width=self.dblBATSensWidthLBL)
                        lblVal = Label(self.frmBATSensors,
                                        text=dictInstructions['BAT_Inputs']['GUI_Information'][key]['GUI_Default'],
                                        font=(dictInstructions['General_Inputs']['Font'],
                                                dictInstructions['General_Inputs']['Font_size']),
                                        relief=SUNKEN)
                        #lblVal.bind('<Button>', cmd_lightUp)
                        lblVal.place(y=(self.dblBATSensHeight * SensCounter),
                                        x=self.dblBATSensWidthLBL,
                                        height=self.dblBATSensHeight,
                                        width = self.dblBATSensWidthVal)
                        dictInstructions['BAT_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Local level insturctions
                        dictGlobalInstructions['BAT_Inputs']['GUI_Information'][key]['GUI_Val'] = lblVal # Module level instructions
                        boolContinue = True
                        SensCounter += 1
                        continue

        #Insert BAT Graph and gauge
        self.BAT_Graph = cht_plt.GUI_graph(dictInstructions['BAT_Inputs']['Graph_params'], self.frmBATGraph)
        self.BAT_Gauge = cht_plt.GUI_gauge(dictInstructions['BAT_Inputs']['Gauge_params'], self.frmBATGauge)

    def solar_pump_thread(self):
        if self.created_self == True:
            self.solar_pump = pump.manage_solar_pump(dictGlobalInstructions, HeatSet_DB)
            while self.solar_pump.quit_sys == False and self.quit_sys == False:
                solar_pump.pump_on_off_decision(dictGlobalInstructions, HeatSet_DB)
                time.sleep(1) #Wait one second

    def sensors_thread(self):
        if self.created_self == True:
            while self.quit_sys == False:
                sensors.run_sensors(dictGlobalInstructions)
                time.sleep(1)

    def derived_values_thread(self):
        if self.created_self == True:
            time.sleep(10)
            while self.quit_sys == False:
                derived.run_derived_values(dictGlobalInstructions)
                time.sleep(1)

    def gauge_update_thread(self):
        if self.created_self == True:
            while self.quit_sys == False:
                #if dictGlobalInstructions['User_Inputs']['Solar_Thermal'] == True:
                    #Managed through D_Database routine Solar_Gauage

                #if dictGlobalInstructions['User_Inputs']['Heat_Pump'] == True:
                    #GUI Gauge Line manged through D_Database routine 'heat_xchange_thread'

                #if dictGlobalInstructions['User_Inputs']['PV'] == True:
                    #GUI Gauge Line manged through D_Database routine 'heat_xchange_thread

                if dictGlobalInstructions['User_Inputs']['Battery'] == True:
                    GUI_BATTChargeVal = dictGlobalInstructions['BAT_Inputs']['GUI_Information']['Charge_Supply']['GUI_Val']
                    if GUI_BATTChargeVal.cget("text") != "None":
                        fltCharge = float(GUI_BATTChargeVal.cget("text"))
                        GUI_DisChargeVal = dictGlobalInstructions['BAT_Inputs']['GUI_Information']['Discharge_Supply']['GUI_Val']
                        if GUI_DisChargeVal.cget("text") != "None":
                            fltDisCharge = float(GUI_DisChargeVal.cget("text"))
                            if fltCharge > fltDisCharge:
                                fltGauge = (fltCharge - fltDisCharge) / fltCharge * 100
                                self.BAT_Gauge.add_gauge_line(fltGauge)
                            elif fltDisCharge > fltCharge:
                                fltGauge = (fltDisCharge - fltCharge) / fltDisCharge * (-100)
                                self.BAT_Gauge.add_gauge_line(fltGauge)
                time.sleep(60)

    def day_plot_reset_thread(self):
        if self.created_self == True:
            BMS_thread_lock = dictGlobalInstructions['Threads']['BMS_thread_lock']
            lstInclude = ['Solar_Thermal', 'Heat_Pump', 'PV', 'Battery']
            lstTech = ['Solar_Inputs', 'HP_Inputs', 'PV_Inputs', 'BAT_Inputs']

            while self.quit_sys == False:
                current_minute = chk_time.return_abs_minute_in_day()
                if current_minute == 90: #At 1.30am
                    #Reset Graph plots
                    for i in range(0,len(lstTech)):
                        if dictGlobalInstructions['User_Inputs'][lstInclude[i]] == True:
                            for key in dictGlobalInstructions[lstTech[i]]['GUI_Information']:
                                if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Include?'] == True:
                                    if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Plot_Values?'] == True:
                                        BMS_thread_lock.acquire(True)
                                        dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Plot_Value_List'] = []
                                        BMS_thread_lock.release()

                    #Update Graph Titles
                    if dictGlobalInstructions['User_Inputs']['Solar_Thermal'] == True:
                        self.Solar_Graph.update_graph_title('Solar tank & collector temperatures: ' + strftime("%d/%m/%Y", gmtime()))
                    if dictGlobalInstructions['User_Inputs']['Heat_Pump'] == True:
                        self.HP_Graph.update_graph_title('Thermal output and electrical input: ' + strftime("%d/%m/%Y", gmtime()))
                    if dictGlobalInstructions['User_Inputs']['PV'] == True:
                        self.PV_Graph.update_graph_title('Electrical output (Wh/min): ' + strftime("%d/%m/%Y", gmtime()))
                    if dictGlobalInstructions['User_Inputs']['Battery'] == True:
                        self.BAT_Graph.update_graph_title('Charge/Discharge (Wh/min): ' + strftime("%d/%m/%Y", gmtime()))

                time.sleep(20)

    def monitor_list_thread(self):
        while self.quit_sys == False:
            print('solar pulse readings')
            lstSolar = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Flow_Rate']['Pulse_Minute_Readings']
            print(lstSolar)

            print('HP external unit pulse readings')
            lstHPExt = dictGlobalInstructions['HP_Inputs']['GUI_Information']['External_Unit_Elec_Wh']['Pulse_Minute_Readings']
            print(lstHPExt)

            print('HP internal unit pulse readings')
            lstInt = dictGlobalInstructions['HP_Inputs']['GUI_Information']['Internal_Unit_Elec_Wh']['Pulse_Minute_Readings']
            print(lstInt)

            print('PV generation')
            lstPV = dictGlobalInstructions['PV_Inputs']['GUI_Information']['Generation']['Pulse_Minute_Readings']
            print(lstPV)

            time.sleep(1)

    def pulse_thread(self):
        pulse.pulse_check(dictGlobalInstructions)

    def initiate_pump_thread(self):
        if dictGlobalInstructions['User_Inputs']['Solar_Control'] == True:
            pump_thread = threading.Thread(target=self.solar_pump_thread).start()
            dictGlobalInstructions['Threads']['Pump_Thread'] = pump_thread

    def initiate_sensors_thread(self):
        sensor_thread = threading.Thread(target=self.sensors_thread).start()
        dictGlobalInstructions['Threads']['Sensors_Thread'] = sensor_thread

    def initiate_DB_Graph_update_thread(self):
        DB_graph_thread = threading.Thread(target=db.DB_extract_graph_update_thread, args=(dictGlobalInstructions,)).start()
        dictGlobalInstructions['Threads']['DB_Graph_Thread'] = DB_graph_thread

    def initiate_derived_values_thread(self):
        derived_value_thread = threading.Thread(target=self.derived_values_thread).start()
        dictGlobalInstructions['Threads']['Derived_Values_Thread'] = derived_value_thread

    def initiate_gauge_thread(self):
        gauge_thread = threading.Thread(target=self.gauge_update_thread).start()
        dictGlobalInstructions['Threads']['Gauge_Thread'] = gauge_thread

    def initiate_plot_day_reset_thread(self):
        plot_reset_thread = threading.Thread(target=self.day_plot_reset_thread).start()
        dictGlobalInstructions['Threads']['Plot_reset_thread'] = plot_reset_thread

    def initiate_pulse_thread(self):
        create_pulse_thread = threading.Thread(target=self.pulse_thread).start()
        dictGlobalInstructions['Threads']['Flow_threads'] = create_pulse_thread

    def initiate_list_review_thread(self):
        list_review_thread = threading.Thread(target=self.monitor_list_thread).start()

    def initiate_all_threads(self):
        if self.created_self == True:
            BMS_thread_lock = threading.Lock()
            dictGlobalInstructions['Threads']['BMS_thread_lock'] = BMS_thread_lock
            self.initiate_pump_thread()
            self.initiate_sensors_thread()
            self.initiate_pulse_thread()
            self.initiate_DB_Graph_update_thread()
            self.initiate_derived_values_thread()
            self.initiate_gauge_thread()
            self.initiate_plot_day_reset_thread()
            #self.initiate_list_review_thread()

### MAIN RUN ###
strDir = dictGlobalInstructions['User_Inputs']['Code_Location']
strCode = strDir + './ObemsPulseServer'
obems = subprocess.Popen([strCode])
dictGlobalInstructions['Threads']['Obems_Execute'] = obems
BMS_GUI = build_GUI(dictGlobalInstructions)
dictGlobalInstructions['General_Inputs']['GUI_BMS'] = BMS_GUI
BMS_GUI.created_self = True
BMS_GUI.initiate_all_threads()
BMS_GUI.RootWin.mainloop()