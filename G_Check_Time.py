from time import strftime, gmtime
import datetime as dt
from datetime import timezone

def Check_Time_4_Store(bytLoop, bytPrevMin): #Provided in minutes with maximum of hourly (i.e. 60)
    current_tm = dt.datetime.now()
    intMin = current_tm.minute

    if intMin != bytPrevMin:
        bytLoop = 0

    bytPrevMin = intMin
    if bytLoop == 0:
        bytLoop += 1
        return [True, bytLoop, bytPrevMin]
    else:
        return [False, bytLoop, bytPrevMin]

def Check_Time_4_Graph(bytLoop, bytPrevMin): #Provided in minutes with maximum of hourly (i.e. 60)
    current_tm = dt.datetime.now()
    intMin = current_tm.minute
    lstGraphUpdateMins = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
	
    if intMin != bytPrevMin:
        bytLoop = 0

    bytPrevMin = intMin
    if bytLoop == 0:
        for i in range(0,len(lstGraphUpdateMins)):
            if lstGraphUpdateMins[i] == intMin:
                bytLoop = bytLoop + 1
                return [True, bytLoop, intMin]

    return [False, bytLoop, intMin]

def Check_Time_4_heat_xchange(): #Provided in minutes with maximum of hourly (i.e. 60)
    current_tm = dt.datetime.now(tz=timezone.utc)
    intMin = current_tm.minute
    lstGraphUpdateMins = [4,9,14,19,24,29,35,39,44,49,54]
    bytListMin = len(lstGraphUpdateMins) + 1

    for i in range(0,len(lstGraphUpdateMins)):
        if lstGraphUpdateMins[i] == intMin:
            bytListMin = i

    if bytListMin == len(lstGraphUpdateMins) + 1:
        return [False] #Not a current minute

    bytMinVar = 60
    for i in range(0,len(lstGraphUpdateMins)):
        if lstGraphUpdateMins[i] != intMin:
            bytVar = intMin - lstGraphUpdateMins[i]
            if bytVar > 0: #i.e. the previous minute is prior to the current minute
                if bytVar < bytMinVar:
                    bytMinVar = bytVar
                    bytListPrevMin = i

    boolLastHR = False
    if bytMinVar == 60: #the current minute is the smallest in the list and hence nothing was found
        boolLastHR = True
        bytMaxVar = 0
        for i in range(0,len(lstGraphUpdateMins)):
            if lstGraphUpdateMins[i] != intMin:
                bytVar = lstGraphUpdateMins[i] - intMin
                if bytVar > 0: #i.e. the previous minute is after to the current minute but in the previous hour
                    if bytVar > bytMaxVar:
                        bytMaxVar = bytVar
                        bytListPrevMin = i

    intPrevMin = lstGraphUpdateMins[bytListPrevMin]

    if boolLastHR == True:
        fltMinDelta = (60 - intPrevMin + intMin)
    else:
        fltMinDelta = intMin - intPrevMin

    strHours = Return_Time_Deltas(current_tm, fltMinDelta)
    return [True, strHours]

def Return_Time_Deltas(dtCurr, fltMinDelta):
    strYear = str(dtCurr.year)
    strMonth = str(dtCurr.month)
    if len(strMonth) == 1:
        strMonth = '0' + strMonth
    strDay = str(dtCurr.day)
    if len(strDay) == 1:
        strDay = '0' + strDay
    strHour = str(dtCurr.hour)
    if len(strHour) == 1:
        strHour = '0' + strHour
    strMin = str(dtCurr.minute)
    if len(strMin) == 1:
        strMin = '0' + strMin

    dtPrev = dtCurr - dt.timedelta(minutes=fltMinDelta)
    strYearPrev = str(dtPrev.year)
    strMonthPrev = str(dtPrev.month)
    if len(strMonthPrev) == 1:
        strMonthPrev = '0' + strMonthPrev
    strDayPrev = str(dtPrev.day)
    if len(strDayPrev) == 1:
        strDayPrev = '0' + strDayPrev
    strHourPrev = str(dtPrev.hour)
    if len(strHourPrev) == 1:
        strHourPrev = '0' + strHourPrev
    strMinPrev = str(dtPrev.minute)
    if len(strMinPrev) == 1:
        strMinPrev = '0' + strMinPrev

    strCurr = strYear + "-" + strMonth + "-" + strDay + " " + strHour + ":" + strMin + ":00"
    strCurrDate = strYear + "-" + strMonth + "-" + strDay
    strCurrHour = strHour + ":" + strMin + ":00"

    strPrev = strYearPrev + "-" + strMonthPrev + "-" + strDayPrev + " " + strHourPrev + ":" + strMinPrev + ":00"
    strPrevDate = strYearPrev + "-" + strMonthPrev + "-" + strDayPrev
    strPrevHour = strHourPrev + ":" + strMinPrev + ":00"

    strHours = [strPrev, strCurr, strPrevDate, strCurrDate, strPrevHour, strCurrHour, dtPrev, dtCurr]
    return strHours

def Check_Time_4_Gauge(): #Provided in minutes with maximum of hourly (i.e. 60)
    current_tm = dt.datetime.now(tz=timezone.utc)
    intMin = current_tm.minute
    lstGraphUpdateMins = [1,6,11,16,21,26,31,36,41,46,51,56]
	
    for i in range(0,len(lstGraphUpdateMins)):
        if lstGraphUpdateMins[i] == intMin:
            return True

    return False

def DB_Check_Time_in_min(dtLastReadTime):
    dtCurrent_tm = dt.datetime.now(tz=timezone.utc)
    intMinCurrent = dtCurrent_tm.minute - 1 #Minus one as the DB run time is the first second of the minute as such we are looking back one minute
    intMinLast = dtLastReadTime.minute

    if intMinCurrent == intMinLast:
        return True
    else:
        return False

def get_int_from_HR_or_min(strHRMin):
    if strHRMin[0] == "0": #If the hour/min is less than 10 then
        strHRMin = strHRMin[1] #the hour/min value is the second character only so set the string to this character
    intHRMin = int(strHRMin) #turn the string into an integer
    return intHRMin

def Check_if_in_TimeFrame(strStart, strEnd):
    strHRCurr = strftime("%H", gmtime()) #Current hour
    intHRCurr = get_int_from_HR_or_min(strHRCurr) #the hour as an integer
    strMinCurr = strftime("%M", gmtime()) #Current minute
    intMinCurr = get_int_from_HR_or_min(strMinCurr) #the minute as an integer

    strStartHR = strStart[:2]
    intStartHR = get_int_from_HR_or_min(strStartHR) #the hour as an integer
    strStartMin = strStart[(len(strStart)-2):]
    intStartMin = get_int_from_HR_or_min(strStartMin) #the minute as an integer

    strEndHR = strEnd[:2]
    intEndHR = get_int_from_HR_or_min(strEndHR) #the hour as an integer
    strEndMin = strEnd[(len(strEnd)-2):]
    intEndMin = get_int_from_HR_or_min(strEndMin) #the minute as an integer

    #1 Does the start time cross days?
    if intEndHR < intStartHR: #The start time can only be higher than the end time when assessed across two days
        boolDayCross = True
    else:
        boolDayCross = False

    #2 Assess if current time falls between start and end
    if boolDayCross == False: #If the start and end time is all within a single day then
        if intHRCurr > intStartHR: #if the current hour is greater than the start hour
            if intHRCurr < intEndHR: #and if it is also less than the end hour
                return True #then we know the current time must be within the appraisal time and don't need to look at the minutes
            if intHRCurr == intEndHR: #if the current hour is the same as the end hour then we need to look at the minutes
                if intMinCurr < intEndMin: #and if the current minute is less than the end minute then
                    return True #we know that although the hours are the same the current minute is less than the end minute of the hour
        if intHRCurr == intStartHR: #however if the start hour is the same as the current hour then
            if intHRCurr < intEndHR:
                if intMinCurr > intStartMin: #if the current minute is greater than the start minute
                    return True #then return true as we know that
            if intHRCurr == intEndHR: #This would mean that the start and end hour are both the same
                if intMinCurr > intStartMin and intMinCurr < intEndMin: #if the current minute falls between the start and end minute then
                    return True #then return true
    else: #for time settings that cross two days
        if intHRCurr > intStartHR: #if the current hour is greater than the start hour then
            return True #We know that the time spans two days. So if the current hour is greater than the start hour then it must fall within the start/end timeframe
        if intHRCurr == intStartHR: #If the current hour is the same as the start hour then
            if intMinCurr > intStartMin: #if the current minute is greater than the start minute then it must be in the start/end timeframe
                return True
        if intHRCurr < intEndHR: #if the current hour is less than the end hour then
            return True #We know that the time spans two days. So if the current hour is less than the end hour then it must fall within the start/end timeframe
        if intHRCurr == intEndHR: #If the current hour is the same as the end hour then
            if intMinCurr < intEndMin: #if the current minute is less than the end minute then it must be in the start/end timeframe
                return True

    return False #The time was not found to be within the time frame set

def return_abs_minute_in_day():
    #This function returns the absolute minute value
    current_tm = dt.datetime.now()
    intHRCurr = float(current_tm.hour) #the hour as an integer
    intMinCurr = float(current_tm.minute) #the minute as an integer

    intMinByHR = intHRCurr * 60
    intReturn = intMinByHR + intMinCurr
    return intReturn

def time_elapse_s(Last_Read):
    Time_Now = dt.datetime.now()
    MSeconds_elapsed = (Time_Now - Last_Read).microseconds
    Seconds_elapsed = MSeconds_elapsed / (10**6)
    return Seconds_elapsed

def time_elase_between_times_s(Previous_Read, Current_Read):
    Curr_Hour = Current_Read.hour
    Curr_Min = Current_Read.minute
    Curr_Sec = Current_Read.second

    Prev_Hour = Previous_Read.hour
    Prev_Min = Previous_Read.minute
    Prev_Sec = Previous_Read.second

    if Curr_Hour < Prev_Hour: #i.e. if next day
        Hr_Delta = Curr_Hour + 24 - Prev_Hour
    else:
        Hr_Delta = Curr_Hour - Prev_Hour

    Min_Delta = Curr_Min + (Hr_Delta * 60) - Prev_Min
    Sec_Delta = Curr_Sec + (Min_Delta * 60) - Prev_Sec
    return Sec_Delta

    return tmSeconds

def set_forecast_time(Current_Read, Add_Seconds):
    Update_Date = Current_Read + dt.timedelta(seconds=Add_Seconds)
    #print(Update_Date)
    return Update_Date

def return_abs_time_2018(strTime):
    '''Year 2000 taken to be point zero. strTime needs to be in the format "%d/%m/%Y %H:%M:%S"'''
    intDay = int(strTime[:2])
    intMonth = int(strTime[3:5])
    intYear = int(strTime[6:10])
    intHR = int(strTime[11:13])
    intMin = int(strTime[14:16])

    lstDaysByMonth = [31,28,31,30,31,30,31,31,30,31,30,31]
    intAbsYearY_1 = ((intYear-1) - 2018) * 365  * 24 * 60 #Number of minutes up to the prior year
    intAbsMonthM_1 = sum(lstDaysByMonth[:(intMonth-1)]) * 24 * 60 #Number of minutes up to the end of the prior month in the current year
    intAbsDayD_1 = (intDay - 1) * 60

    return intAbsYearY_1 + intAbsMonthM_1 + intAbsDayD_1 + intMin

#tmMin = return_abs_minute_in_day()
#print(tmMin)
#lstTimes = Return_Time_Deltas(dt.datetime.now(tz=timezone.utc),59)
#print(lstTimes)