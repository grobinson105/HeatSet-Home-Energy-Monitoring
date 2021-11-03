import threading
import time
import datetime as dt
import socket               # Import socket module
import G_Check_Time as chk_time
from H_Derived_Values import tech_heat_load

def record_pulse(lstArgs):
    GPIO_read = lstArgs[0]
    Pulse_Val = lstArgs[1]
    strTech = lstArgs[2]
    strPulseMeter = lstArgs[3]
    dictInstructions = lstArgs[4]
    dtReadTime = lstArgs[5]

    BMS_GUI = dictInstructions['General_Inputs']['GUI_BMS']
    BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']

    BMS_thread_lock.acquire(True)
    lstLastMinute = dictInstructions[strTech]['GUI_Information'][strPulseMeter]['Pulse_Minute_Readings']
    lstTimes = dictInstructions[strTech]['GUI_Information'][strPulseMeter]['Pulse_reading_times']
    BMS_thread_lock.release()

    if lstLastMinute[0] == True: #The first 'bit' of the list is set by D_Database as to whether the minute's data has or has not been taken
        lstReadingVal = 0 #Set the last reading value to 0 (we are interested in the time it was taken but don't want to double count
        lstLastMinute = [False, lstReadingVal, Pulse_Val] #Transfer the last reading to the current minute's list and add the new reading
        lstReadingTime = lstTimes[len(lstTimes)-1] #Take the last reading's time from the previous minute
        lstTimes = [False, lstReadingTime, dtReadTime] #Transfer the last reading time to the current minute's list and add the new reading's time
    else:
        lstLastMinute.append(Pulse_Val)
        lstTimes.append(dtReadTime)

    BMS_thread_lock.acquire(True)
    dictInstructions[strTech]['GUI_Information'][strPulseMeter]['Pulse_Minute_Readings'] = lstLastMinute
    dictInstructions[strTech]['GUI_Information'][strPulseMeter]['Pulse_reading_times'] = lstTimes
    BMS_thread_lock.release()

def pulse_check(dictGlobalInstructions):

    time.sleep(10) #Give the sensors a few seconds to have logged some readings
    BMS_GUI = dictGlobalInstructions['General_Inputs']['GUI_BMS']
    BMS_thread_lock = dictGlobalInstructions['Threads']['BMS_thread_lock']
    db_BMS = dictGlobalInstructions['Database']

    dtReadTime = dt.datetime.now()
    tmNextPulseForecast = dtReadTime

    host = socket.gethostname() # Get local machine name
    port = 9801   # Reserve a port for OBEMS service.
    lstOBEMS = dictGlobalInstructions['User_Inputs']['OBEMS'] #Map for OBEMS channels to HeatSet PCBs for pulse meters
    lstPulseCount = []
    lstArgs = []

    for i in range(0, len(lstOBEMS)):
        lstPulseCount.append(0) #Create a zero pulse count against each channel to be read
        strType = lstOBEMS[i][0]
        for key in dictGlobalInstructions[strType]['GUI_Information']:
            if dictGlobalInstructions[strType]['GUI_Information'][key]['ID'] == lstOBEMS[i][1]:
                BMS_thread_lock.acquire(True)
                dictGlobalInstructions[strType]['GUI_Information'][key]['Pulse_Minute_Readings'] = [False, 0, 0]
                dictGlobalInstructions[strType]['GUI_Information'][key]['Pulse_reading_times'] = [False, BMS_GUI.time_created, dtReadTime]
                BMS_thread_lock.release()

    while BMS_GUI.quit_sys == False:
        dtReadTime = dt.datetime.now()

        for i in range(0, len(lstOBEMS)):
            strType = lstOBEMS[i][0]
            ID_num = lstOBEMS[i][1]
            strCH = lstOBEMS[i][2]      #Determine the channel to read

            #print(strType + ";" + str(ID_num) + ";" + strCH)

            s = socket.socket()         # Create a socket object
            s.connect((host, port))     #Connect to the OBEMS server
            s.send( strCH.encode() )    #Send the channel read request
            strRec  = s.recv(1024)      #Read the port
            intPulseCountTotal = int(strRec[-9:]) #The last nine values of the string are the maximum number of pulses - convert to a channel
            intTotalPulses = lstPulseCount[i]
            lstPulseCount[i] = intPulseCountTotal #Update the locally stored total number of pulses to date
            s.close()

            #print(lstPulseCount)

            for key in dictGlobalInstructions[strType]['GUI_Information']:
                #print(strType)
                #print(key)
                if dictGlobalInstructions[strType]['GUI_Information'][key]['ID'] == ID_num:
                    #print(True)
                    #print(intTotalPulses)
                    #print(key)
                    boolFlow = dictGlobalInstructions[strType]['GUI_Information'][key]['Pulse_calc_flow']
                    #print(intTotalPulses)
                    #print(intPulseCountTotal)
                    if intPulseCountTotal > intTotalPulses: #If the server cumulative pulses is greater than what was previously read then there have been 1 or more pulses
                        intPulseCount = intPulseCountTotal - intTotalPulses #Establish the total number of pulses since the last read
                        Pulse_Val = dictGlobalInstructions[strType]['GUI_Information'][key]['Pulse_Value'] #User defined single pulse value (e.g. 0.25L for hot water flow meter or 1Wh for electricity sub-meter)
                        Pulse_Val_mult = Pulse_Val * intPulseCount #The value of the pulses read
                        #print(Pulse_Val_mult)
                        GPIO_read = dictGlobalInstructions[strType]['GUI_Information'][key]['Pulse_GPIO'] #Which GPIO is used to monitor the pulse?
                        lstArgs = [GPIO_read, Pulse_Val_mult, strType, key, dictGlobalInstructions, dtReadTime]
                        #print(strType)
                        #print(key)
                        #print(intPulseCount)
                        record_pulse(lstArgs) #record kWh (electrical) or litres in pulse meter section
        time.sleep(10)