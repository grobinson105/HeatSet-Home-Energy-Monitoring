import math
import time
import datetime as dt
from time import gmtime, strftime
import G_Check_Time as chk_time

def ethelyne_glycol_heat_capacity(percent_glycol):
    #https://www.engineeringtoolbox.com/ethylene-glycol-d_146.html
    #Heat capacity (KJ/KG K) at 20DegC ambient on the basis that the solar thermal system will primarily be operating in summer
    #[% Glycol mix, heat capacity of mix of glycol and water]
    lstGlycolHeatCapacity = [[0, 4.189],
                            [10, 4.087],
                            [20, 3.951],
                            [30, 3.807],
                            [40, 3.647],    #A 40% mix should allow for -20DegC which should be sufficient for UK
                            [50, 3.473],
                            [60, 3.284],
                            [70, 3.08],
                            [80, 2.862],
                            [90, 2.628],
                            [100, 2.38]]

    for i in range(0, len(lstGlycolHeatCapacity)):
        if percent_glycol >= lstGlycolHeatCapacity[i][0]:
            if percent_glycol < lstGlycolHeatCapacity[i+1][0]:
                fltLower = float(lstGlycolHeatCapacity[i][0])
                fltLowerCapacity = float(lstGlycolHeatCapacity[i][1])
                fltUpper = float(lstGlycolHeatCapacity[i+1][0])
                fltUpperCapacity = float(lstGlycolHeatCapacity[i+1][1])
                fltInterpolatedCapacity = fltLowerCapacity + (((percent_glycol - fltLower) / (fltUpper - fltLower)) * (fltUpperCapacity - fltLowerCapacity))
                return fltInterpolatedCapacity

def thermal_capacity_of_pipe(heat_capacity_of_liquid_KJ_KG, PipeID, DeltaT):
    thermal_capacity_W = (math.pi * ((PipeID/2)**2)) * 1000 * heat_capacity_of_liquid_KJ_KG * DeltaT #Internal area of pipe (PiR^2) * water density * heat capacity of liquid flowing through pipe (KJ/kW K) * the difference in temperature between the flow and return temperatures
    return thermal_capacity_W

def heat_load(flow_rate_LS, time_elapsed_s, heat_capacity_of_liquid_KJ_KG, DeltaT):
    L_water = flow_rate_LS * time_elapsed_s
    heat_load_Kjoules_s = (heat_capacity_of_liquid_KJ_KG * L_water *  (DeltaT/time_elapsed_s)) #heat capacity of the liquid used to transfer heat (KJ/kW K) * Litres of water * the difference in temperature between the flow and return / time taken to achieve DeltaT
    heat_load_joules_s = heat_load_Kjoules_s * (10**3)
    heat_load_Wh = (heat_load_joules_s / (60**2))
    return heat_load_Wh

def tech_heat_capacity_from_pipe(lstArgs):
    glycol_mix = float(lstArgs[0])
    PipeID = float(lstArgs[1]) / 1000 #Convert to meters
    strTech = lstArgs[2]
    strHotSideKey = lstArgs[3]
    strColdSideKey = lstArgs[4]
    dictInstructions = lstArgs[5]

    #print(strTech + ": " + strHotSideKey)
    specific_heat = ethelyne_glycol_heat_capacity(glycol_mix)
    lstHotTemp = dictInstructions[strTech]['GUI_Information'][strHotSideKey]['Minute_Average']
    latest_hot_reading = float(lstHotTemp[len(lstHotTemp)-1])
    lstCoolTemp = dictInstructions[strTech]['GUI_Information'][strColdSideKey]['Minute_Average']
    latest_cool_reading = float(lstCoolTemp[len(lstCoolTemp)-1])
    Delta_T = latest_hot_reading - latest_cool_reading
    if Delta_T < 0:
        Delta_T = 0
    heat_capacity_W = specific_heat * 10 * Delta_T / 60 #Specific heat capacity of the glycol mix * 10 litres (10kg) * current delta T / 60 seconds (assumes a 10L/min flow rate)
    return heat_capacity_W

def tech_heat_capacity_from_volume(lstArgs):
    glycol_mix = float(lstArgs[0])
    water_volume = float(lstArgs[1])
    strTech = lstArgs[2]
    strHotSideKey = lstArgs[3]
    strColdSideKey = lstArgs[4]
    dictInstructions = lstArgs[5]

    #print(strTech + ": " + strHotSideKey)
    specific_heat = ethelyne_glycol_heat_capacity(glycol_mix)
    lstHotTemp = dictInstructions[strTech]['GUI_Information'][strHotSideKey]['Minute_Average']
    latest_hot_reading = float(lstHotTemp[len(lstHotTemp)-1])
    lstCoolTemp = dictInstructions[strTech]['GUI_Information'][strColdSideKey]['Minute_Average']
    latest_cool_reading = float(lstCoolTemp[len(lstCoolTemp)-1])
    Delta_T = latest_hot_reading - latest_cool_reading
    if Delta_T < 0:
        Delta_T = 0
    heat_capacity_W = specific_heat * water_volume * Delta_T * (10**3) / 3600 #Specific heat capacity of the glycol mix * volume litres * current delta T
    return heat_capacity_W

def tech_heat_load(lstArgs):
    strTech = lstArgs[0]
    glycol_mix = float(lstArgs[1])
    strHotSideKey = lstArgs[2]
    strCoolTempKey = lstArgs[3]
    fltPulseLitres = lstArgs[4]
    fltSecondsElapsed = lstArgs[5]
    dtTimeofPulse = lstArgs[6]
    dictInstructions = lstArgs[7]

    BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']
    dtTimeStart = dtTimeofPulse - dt.timedelta(seconds=(fltSecondsElapsed + 30)) #Add half a minute in case there is a very quick series of pulses (unlikely but just in case)

    BMS_thread_lock.acquire(True)
    lstHotTemp = dictInstructions[strTech]['GUI_Information'][strHotSideKey]['Minute_Average']
    lstHotTempTimes = dictInstructions[strTech]['GUI_Information'][strHotSideKey]['Sensor_Read_Times']
    lstCoolTemp = dictInstructions[strTech]['GUI_Information'][strCoolTempKey]['Minute_Average']
    lstCoolTempTimes = dictInstructions[strTech]['GUI_Information'][strCoolTempKey]['Sensor_Read_Times']
    BMS_thread_lock.release()

    fltHotTempExtract = 0
    count_hits = 0
    for i in range(1,len(lstHotTempTimes)): #The first slot in the time list is TRUE/FALSE so is skipped here
        if lstHotTempTimes[i] >= dtTimeStart and lstHotTempTimes[i] <= dtTimeofPulse:
            fltHotTempExtract = fltHotTempExtract + lstHotTemp[i]
            count_hits = count_hits + 1
    if count_hits >0:
        avHotTempExtract = fltHotTempExtract / count_hits
    else:
        avHotTempExtract = 0
        print('Tech_Heat_Load: no hot flow water temperature values despite pulse logged: ' + str(dt.datetime.now()))

    fltCoolTempExtract = 0
    count_hits = 0
    for i in range(1,len(lstCoolTempTimes)): #The first slot in the time list is TRUE/FALSE so is skipped here
        if lstCoolTempTimes[i] >= dtTimeStart and lstCoolTempTimes[i] <= dtTimeofPulse:
            fltCoolTempExtract = fltCoolTempExtract + lstCoolTemp[i]
            count_hits = count_hits + 1
    if count_hits > 0:
        avCoolTempExtract = fltCoolTempExtract / (len(lstCoolTempTimes)-1)
    else:
        avCoolTempExtract = 0
        print('Tech_Heat_Load: no return water temperature values despite pulse logged: ' + str(dt.datetime.now()))

    heat_capacity = ethelyne_glycol_heat_capacity(glycol_mix)
    heat_load_Wh = heat_capacity * fltPulseLitres * (avHotTempExtract - avCoolTempExtract) * 1000 / (60**2)

    #print('heat capacity: ' + str(heat_capacity) + ', Pulse (L): ' + str(fltPulseLitres) + ', DeltaT: ' + str(avHotTempExtract - avCoolTempExtract))
    return heat_load_Wh

def tech_heat_load_duration(lstArgs):
    strTech = lstArgs[0]
    glycol_mix = float(lstArgs[1])
    strHotSideKey = lstArgs[2]
    strCoolTempKey = lstArgs[3]
    strHeatLoadKey = lstArgs[4]
    fltPHEx = lstArgs[5]
    dictInstructions = lstArgs[6]

    BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']

    BMS_thread_lock.acquire(True)
    lstHotTemp = dictInstructions[strTech]['GUI_Information'][strHotSideKey]['Minute_Average']
    lstCoolTemp = dictInstructions[strTech]['GUI_Information'][strCoolTempKey]['Minute_Average']
    lstReadTimes = dictInstructions[strTech]['GUI_Information'][strHeatLoadKey]['Derived_read_times']
    BMS_thread_lock.release()

    if lstReadTimes == None:
        return 0

    #print('Hot Temp:' + str(lstHotTemp))
    #print('Cool Temp:' + str(lstCoolTemp))
    #print('Derived values time:' + str(lstReadTimes))

    dtReadTime = lstReadTimes[len(lstReadTimes)-1]
    dtLastReadTime = lstReadTimes[len(lstReadTimes)-2]
    seconds_elapsed = chk_time.time_elase_between_times_s(dtLastReadTime, dtReadTime)

    #print(lstReadTimes[len(lstReadTimes)-1])
    #print('Last Read Time:' + str(dtLastReadTime))
    #print('Current Read Time:' + str(dtReadTime))
    #print('Seconds elapsed:' + str(seconds_elapsed))

    fltHotTempExtract = lstHotTemp[len(lstHotTemp)-1]
    fltCoolTempExtract = lstCoolTemp[len(lstCoolTemp)-1]

    heat_capacity = ethelyne_glycol_heat_capacity(glycol_mix)
    heat_load_Wh = heat_capacity * fltPHEx * (fltHotTempExtract - fltCoolTempExtract) * 1000 * seconds_elapsed / (60**2)

    #print('Average hot:' + str(fltHotTempExtract))
    #print('Average cool:' + str(fltCoolTempExtract))
    #print('heat capacity: ' + str(heat_capacity) + ', Pulse (L): ' + str(fltPHEx) + ', DeltaT: ' + str(fltHotTempExtract - fltCoolTempExtract))
    #print('heat load: ' + str(heat_load_Wh))
    return heat_load_Wh

def tech_heat_load_W(lstArgs):
    strTech = lstArgs[0]
    glycol_mix = float(lstArgs[1])
    strHotSideKey = lstArgs[2]
    strCoolTempKey = lstArgs[3]
    fltPHEx = lstArgs[4]
    dictInstructions = lstArgs[5]

    BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']

    BMS_thread_lock.acquire(True)
    lstHotTemp = dictInstructions[strTech]['GUI_Information'][strHotSideKey]['Minute_Average']
    lstCoolTemp = dictInstructions[strTech]['GUI_Information'][strCoolTempKey]['Minute_Average']
    BMS_thread_lock.release()

    fltHotTempExtract = lstHotTemp[len(lstHotTemp)-1]
    fltCoolTempExtract = lstCoolTemp[len(lstCoolTemp)-1]

    heat_capacity = ethelyne_glycol_heat_capacity(glycol_mix)
    heat_load_W = heat_capacity * fltPHEx * (fltHotTempExtract - fltCoolTempExtract) * (10**3) / 3600
    #print('heat capacity: ' + str(heat_capacity) + ', Pulse (L): ' + str(fltPHEx) + ', DeltaT: ' + str(fltHotTempExtract - fltCoolTempExtract))
    #print(str(heat_load_W))
    return heat_load_W

def Watts_from_Wh(lstArgs):
    strConsumptionKey = lstArgs[0]
    strTech = lstArgs[1]
    strConsumption = lstArgs[2]
    strConsumptionTime = lstArgs[3]
    dictInstructions = lstArgs[4]

    BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']
    BMS_thread_lock.acquire(True)
    lstConsumption = dictInstructions[strTech]['GUI_Information'][strConsumptionKey][strConsumption]
    lstReadTimes = dictInstructions[strTech]['GUI_Information'][strConsumptionKey][strConsumptionTime]
    BMS_thread_lock.release()

    if lstConsumption == None or lstReadTimes == None:
        return 0

    Wh_consumption = lstConsumption[len(lstConsumption)-1]
    start_time = lstReadTimes[len(lstReadTimes)-2]
    end_time = lstReadTimes[len(lstReadTimes)-1]
    boolInCurrentMinute = chk_time.DB_Check_Time_in_min(end_time)
    if boolInCurrentMinute == True: #If the last read was not in the current minute then there is no power
        time_taken_s = chk_time.time_elase_between_times_s(start_time, end_time)
        time_hr = time_taken_s / (60 * 60)
        Watts = Wh_consumption  / time_hr
    else:
        Watts = 0
    return Watts

def HP_External_Internal_Watts_from_Wh(lstArgs):
    strInternalConsumption = lstArgs[0]
    strExternalConsumption = lstArgs[1]
    strTech = lstArgs[2]
    strPulseReadings = lstArgs[3]
    strPulseTimes = lstArgs[4]
    dictInstructions = lstArgs[5]

    lstArgsInternal = [strInternalConsumption, strTech, strPulseReadings, strPulseTimes, dictInstructions]
    internalWatts = Watts_from_Wh(lstArgsInternal)

    lstArgsExternal = [strExternalConsumption, strTech, strPulseReadings, strPulseTimes, dictInstructions]
    externalWatts = Watts_from_Wh(lstArgsExternal)

    watts = internalWatts + externalWatts
    return(watts)

def run_derived_values(dictGlobalInstructions):
    BMS_thread_lock = dictGlobalInstructions['Threads']['BMS_thread_lock']
    lstInclude = ['Solar_Thermal', 'Heat_Pump', 'PV', 'Battery']
    lstTech = ['Solar_Inputs', 'HP_Inputs', 'PV_Inputs', 'BAT_Inputs']
    dtDerivedReadTime = dt.datetime.now()
    dtGUIStart = dictGlobalInstructions['General_Inputs']['Time_Stamp']['GUI_Default']

    for i in range(0,len(lstTech)):
        if dictGlobalInstructions['User_Inputs'][lstInclude[i]] == True:
            #print(lstTech[i])
            for key in dictGlobalInstructions[lstTech[i]]['GUI_Information']:
                if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Include?'] == True:
                    if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Val'] == True:
                        strInterfaceFunction = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Val_Function']
                        if strInterfaceFunction != None: #Heat loads are derived on each pulse in combination with a derived function - as such these are managed through I_Pulse_Meters
                            #print(strInterfaceFunction)
                            lstArgs = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Val_Function_Args']
                            #print(lstArgs)
                            lstArgs.append(dictGlobalInstructions)
                            fltOutput = globals()[strInterfaceFunction](lstArgs)
                            if fltOutput == None:
                                fltOutput = 0

                            if dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Minute_Average'] == None:
                                lstLastMinute = [False, 0, fltOutput]
                                lstReadTimes = [False, dtGUIStart, dtDerivedReadTime]
                            else:
                                BMS_thread_lock.acquire(True)
                                lstLastMinute = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Minute_Average']
                                lstReadTimes = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_read_times']
                                BMS_thread_lock.release()
                                if lstLastMinute[0] == True: #The first 'bit' of the list is set by D_Database as to whether the minute's data has or has not been taken
                                    lstLastMinute = [False, 0, fltOutput] #Record 0 for the last read time to avoid double count and include the new reading value
                                    lstReadTimes = [False, lstReadTimes[len(lstReadTimes)-1], dtDerivedReadTime] #Carry over the time of when the last reading was taken and add the new read time
                                else:
                                    lstLastMinute.append(fltOutput)
                                    lstReadTimes.append(dtDerivedReadTime)

                            BMS_thread_lock.acquire(True)
                            dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Minute_Average'] = lstLastMinute
                            dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_read_times'] = lstReadTimes
                            BMS_thread_lock.release()

                            #print(lstLastMinute)
                            #Update GUI for collector temperature
                            boolDayTotal = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['Derived_total?']
                            if boolDayTotal == False:
                                strOutput = str(fltOutput)
                                lstGUIIncluded = dictGlobalInstructions[lstTech[i]]['GUI_Sections'][0] #If item is included on the GUI (as opposed to just being an SQL only item)
                                ID = dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['ID']
                                for j in range(0,len(lstGUIIncluded)):
                                    if lstGUIIncluded[j] == ID:
                                        dictGlobalInstructions[lstTech[i]]['GUI_Information'][key]['GUI_Val'].config(text=strOutput[:5])