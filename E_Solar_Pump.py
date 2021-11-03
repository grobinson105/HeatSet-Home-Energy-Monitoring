import time
import RPi.GPIO as GPIO
from tkinter import *
import C_chart_plots as cht_plt
import D_Database as db
'''
This module manages the operation of the solar pump and emergency flush valve
'''

class manage_solar_pump():
    def __init__(self, dictInstructions, Solar_DataBase):
        self.pump_on = False
        self.emergency_flush = False
        self.lstOnOff = dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['On_Off']
        self.lstFlushMode = dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['Flush_Status']
        self.pump_on_off_decision(dictInstructions)

    def get_sys_mode(self, dictGlobalInstructions):
        lblText = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['System_mode']['GUI_Val'].cget("text")
        lstStatus = dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['Solar_modes']
        if lblText == lstStatus[0]:
            self.run_sys = True
        else:
            self.run_sys = False

    def switch_pump_on_off(self, dictGlobalInstructions, Solar_DataBase):
        strTable =  dictGlobalInstructions['Solar_Inputs']['Defaults']['Database_Table_Name']
        arrFields = [dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['SQL_Title']]
        Solar_Pump_GPIO = dictGlobalInstructions['Solar_Inputs']['GPIOs']['Solar_Pump']
        if self.pump_on == True:
            GPIO.output(Solar_Pump_GPIO,GPIO.LOW) #Relay power to the pump
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['GUI_Val'].config(text=self.lstOnOff[0])
            arrVals = [self.lstOnOff[0]]
        else:
            GPIO.output(Solar_Pump_GPIO,GPIO.HIGH) #Don't relay power to the pump
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['GUI_Val'].config(text=self.lstOnOff[1])
            arrVals = [self.lstOnOff[1]]
        Solar_DataBase.upload_data(strTable, arrFields, arrVals)

    def manage_emergency_flush(self, dictGlobalInstructions, Solar_DataBase):
        strTable =  dictGlobalInstructions['Solar_Inputs']['Defaults']['Database_Table_Name']
        arrFields = [dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Flush_Valve']['SQL_Title']]
        Solar_Flush_Valve_GPIO = dictGlobalInstructions['Solar_Inputs']['GPIOs']['Emergency_Flush_Valve']
        if self.emergency_flush == True:
            GPIO.output(Solar_Flush_Valve_GPIO,GPIO.LOW) #Relay power to the motorised valve (the 2 port valve is open when in its actuated state)
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Flush_Valve']['GUI_Val'].config(text=self.lstFlushMode[0])
            arrVals = [self.lstFlushMode[0]]
        else:
            GPIO.output(Solar_Flush_Valve_GPIO,GPIO.HIGH) #Don't relay power to the motorised valve
            dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Flush_Valve']['GUI_Val'].config(text=self.lstFlushMode[1])
            arrVals = [self.lstFlushMode[1]]
        Solar_DataBase.upload_data(strTable, arrFields, arrVals)

    def reset_flush_valve(self, dictGlobalInstructions, Solar_Database):
        self.emergency_flush = False
        self.quit_sys = False
        self.manage_emergency_flush(dictGlobalInstructions, Solar_Database)

    def pump_on_off_decision(self, dictGlobalInstructions, Solar_DataBase):
        '''Basic concept: the pump will never run when the collector is less than the temperature
           of the tank + the target DeltaT.

           Pump is OFF:
           If it is within daylight hours (8am-5pm) then if the last pump event was over an hour ago (9am onwards) then reduce the target temperature down by one degree C
           until such point that the minimum temperature + target Delta T is reached and hold at that target temperature.

           If the collector temperature is greater than or equal to the tank temperature + DeltaT then switch the pump on.
           If the last pump ON event was less than 45 minutes ago (after 8.45am) then increase the the target temperature by 1 degree C. If it was more than
           1 hour ago then reduce the target temperature by 1 degree C.

           Pump is ON:
           If the pump has been on for more than 10 minutes then switch OFF. If the tank temperature + 20% Delta T is greater than or equal to the collector temperature
           then Switch Pump OFF. There will be losses through the flow and return pipes however well lagged they may be as such
           taking a 20% losses + failed heat transfer assumption as a starting assumption. This can be flexed through analysis.'''

        self.get_sys_mode
        if self.run_sys == False:
            return

        intCurrMin = return_abs_minute_in_day() #Get the current minute within the day (0-1440)
        intStartMin = int(dictGlobalInstructions['Solar_Inputs']['Defaults']['First_light_hr']) * 60 #Get the absolute start minute in the day per the system-initialise
        intEndMin = int(dictGlobalInstructions['Solar_Inputs']['Defaults']['Last_light_hr']) * 60 #GEt the absolute end minute in the day
        intDeltaT = int(dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_DeltaT']['GUI_Val'].cget("text"))
        intIncrement = dictGlobalInstructions['Solar_Inputs']['Defaults']['Temp_increment']
        intTargetTemp = int(dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_temperature']['GUI_Val'].cget("text"))
        intMinTemp = int(dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Min_Temp']['GUI_Val'].cget("text"))
        intMaxTemp = int(dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Max_Temp']['GUI_Val'].cget("text"))
        intAbsLastPumpMin = return_abs_time_2018(dtLastPump)
        strTimeNow = strftime("%d/%m/%Y %H:%M:%S", gmtime())
        intAbsCurrentMin = return_abs_time_2018(strTimeNow)
        dblADJ = dictGlobalInstructions['Solar_Inputs']['Defaults']['DeltaT_loss_percent'] #Of the target DeltaT it will not be possible for full heat transfer some will be lost and there will not be perfrect conduction across the heat exchange. This value sets the permissible % of the DeltaT that will dictate when the system should stop pumping - i.e. where the tank temperature plus the adjusted delta T is greater than or equal to the collector temperature

        #Get tank and collector temperatures
        fltTank = float(dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Tank_temp']['GUI_Val'].cget("text"))
        fltCollector = float(dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Collector_temp']['GUI_Val'].cget("text"))

        boolContinue = True
        #Confirm collector is within acceptable operating parameters
        if fltCollector < intMinTemp:
            self.emergency_flush == True
            self.quit_sys = True
            self.pump_on == False
            boolContinue == False
            self.manage_emergency_flush(dictGlobalInstructions, Solar_DataBase)

        #Confirm tank is within acceptable operating parameters
        if fltTank < intMinTemp or fltTank > intMaxTemp:
            self.emergency_flush == True
            self.quit_sys = True
            self.pump_on == False
            boolContinue == False
            self.manage_emergency_flush(dictGlobalInstructions, Solar_DataBase)

        if boolContinue == True:
            #Determine if pump is ON or OFF and assess what to do
            boolPumpOn = dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Solar_Pump']['GUI_Val'].cget("text")
            lstOnOff = dictGlobalInstructions['Solar_Inputs']['GUI_Commands']['On_Off']
            if boolPumpOn == lstOnOff[1]: #If the pump is OFF
                if fltTank + intDeltaT <= fltCollector: #If the tank temperature plus the target Delta T is less than or equal to the collector temperature then
                    if fltCollector >= intTargetTemp: #if the colelctor temperature is at or greater than the target temperature th
                        if intAbsCurrentMin - intAbsLastPumpMin < dictGlobalInstructions['Solar_Inputs']['Defaults']['Time_lapse_b4_temp_change']: #if the last pump time was less than the set time gap then
                            if intCurrMin > intStartMin and intCurrMin < intEndMin: #Only adjust the target temperature during daylight hours
                                intTarget = intTargetTemp + intIncrement #If the collector has achieved the target more quickly than was predicted (see System_initialize bytPumpLastOnCheckStillOff) then increase the target by the change increment
                                dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_temperature']['GUI_Default'] = intTarget
                                dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_temperature']['GUI_Val'].config(text=str(intTarget))
                        dtLastPump = strftime("%d/%m/%Y %H:%M:%S", gmtime()) #set the last pump time as now
                        self.pump_on = True
                    else:
                        #The Delta T has been achieved but the target in the collector has not been met
                        #This logic needs to be tested as it will essentially reduce the target temperature to the DeltaT + tank temperature. Better heat exchange woudl be with a higher delta T but there is a risk that it would not be achieved
                        if intTargetTemp > fltTank + intDeltaT + intIncrement: #if the current target temperature is greater than the minimum temperature plus the delta T plus the change increment then
                            if intCurrMin > intStartMin and intCurrMin < intEndMin: #Only adjust the target temperature during daylight hours
                                intTarget = fltTank + intDeltaT #set the target temperature to the tank temperature + delta T
                                dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_temperature']['GUI_Default'] = intTarget
                                dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_temperature']['GUI_Val'].config(text=str(intTarget))
                        self.pump_on = False
                else:
                    if intAbsCurrentMin - intAbsLastPumpMin > dictGlobalInstructions['Solar_Inputs']['Defaults']['Time_lapse_b4_temp_change']: #if the last pump time was greater than the set time gap then
                        if intTargetTemp > fltTank + intDeltaT + intIncrement: #if the current target temperature is greater than the minimum temperature plus the delta T plus the change increment then
                            if intCurrMin > intStartMin and intCurrMin < intEndMin: #Only adjust the target temperature during daylight hours
                                intTarget = fltTank + intDeltaT #set the target temperature to the tank temperature + delta T
                                dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_temperature']['GUI_Default'] = intTarget
                                dictGlobalInstructions['Solar_Inputs']['GUI_Information']['Target_temperature']['GUI_Val'].config(text=str(intTarget))
                    self.pump_on = False

            #If the pump is already ON
            else:
                if fltTank + (intDeltaT * dblADJ) >= fltCollector: #if the tank temperature plus the permissible heat losses are greater than the current collector temperature then
                    self.pump_on = False #switch the pump off as there has been sufficient heat transfer
                else:
                    self.pump_on = True #keep pumping as the heat exchange has not completed sufficiently