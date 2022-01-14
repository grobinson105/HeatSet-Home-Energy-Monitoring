import sqlite3
from time import gmtime, strftime
from urllib.request import pathname2url
import csv
import threading
import time
import datetime as dt
from datetime import timezone
import C_chart_plots
import G_Check_Time as chk_time
import H_Derived_Values as derived

def create_table_string(dictInstructions, strTech):
    strTable = dictInstructions[strTech]['Defaults']['Database_Table_Name']
    lstFields = ['ID', 'Time_Stamp']
    lstAtt = ['INTEGER PRIMARY KEY AUTOINCREMENT', 'DEFAULT CURRENT_TIMESTAMP']
    for key in dictInstructions[strTech]['GUI_Information']:
        lstFields.append(dictInstructions[strTech]['GUI_Information'][key]['SQL_Title'])
        lstAtt.append('TEXT')

    listLength = len(lstFields) #Determine the number of fields to be created
    for i in range(0,listLength): #For the variable i from 0 to the number of fields
        if i == 0:
            strCreateTable = 'CREATE TABLE ' + strTable + '(' + lstFields[i] + ' ' + lstAtt[i] #SQL create table with the first field item and its attribute
        if i > 0 and i <listLength - 1:
            strCreateTable = strCreateTable + ', ' + lstFields[i] + ' ' + lstAtt[i] #Adding the next field with attribute
        if i == listLength - 1:
            strCreateTable = strCreateTable + ', ' + lstFields[i] + ' ' + lstAtt[i] + ');' #Final field and attribute with closing punctuation

    lstReturn = [strCreateTable, lstFields]
    return lstReturn

class manage_database:
    def __init__(self, dictInstructions):
        self.create(dictInstructions)

    def create(self, dictInstructions):
        #Test if DB exists
        strDBLoc = dictInstructions['User_Inputs']['DB_Location']
        strDBRootName = dictInstructions['General_Inputs']['DB_Name']
        strYear = str(strftime("%Y", gmtime()))
        self.strDBName = strDBRootName + strYear
        if strDBLoc[-1:] != "/":
            self.strPath = strDBLoc + "/" + self.strDBName
        else:
            self.strPath = strDBLoc + self.strDBName
        #print(self.strPath)
        try:
            dbExists = 'file:{}?mode=rw'.format(pathname2url(self.strPath)) #Open the DB in read mode
            test = sqlite3.connect(dbExists) #Make the connection
            boolExists = True
        except sqlite3.OperationalError: #if the conneciton fails then it means it doesn't exist
            boolExists = False

        self.DBConn = sqlite3.connect(self.strPath) #SQLite3 will create a new database if a connection cannot be made
        self.c = self.DBConn.cursor()

        #Solar Info
        lstSolar = create_table_string(dictInstructions, 'Solar_Inputs')
        strSolarTable = lstSolar[0]
        self.lstSolarFields = lstSolar[1]

        #HP Info
        lstHP = create_table_string(dictInstructions, 'HP_Inputs')
        strHPTable = lstHP[0]
        self.lstHPFields = lstHP[1]

        #PV Info
        lstPV = create_table_string(dictInstructions, 'PV_Inputs')
        strPVTable = lstPV[0]
        self.lstPVFields = lstPV[1]

        #Battery Info
        lstBat = create_table_string(dictInstructions, 'BAT_Inputs')
        strBatTable = lstBat[0]
        self.lstBatFields = lstBat[1]

        #Zone Info
        lstZone = create_table_string(dictInstructions, 'ZONE_Inputs')
        strZoneTable = lstZone[0]
        self.lstZoneFields = lstZone[1]

        if boolExists == False:
            if dictInstructions['User_Inputs']['Solar_Thermal'] == True:
                self.c.execute(strSolarTable)

            if dictInstructions['User_Inputs']['Heat_Pump'] == True:
                self.c.execute(strHPTable)

            if dictInstructions['User_Inputs']['PV'] == True:
                self.c.execute(strPVTable)

            if dictInstructions['User_Inputs']['Battery'] == True:
                self.c.execute(strBatTable)

            if dictInstructions['User_Inputs']['Zone'] == True:
                self.c.execute(strZoneTable)

    def upload_data(self, strTable, arrFields, arrVals):
        if len(arrFields) > 0:
            listLength = len(arrFields) #determine the number of values being provided (allowing for multiple readings to be entered)
            for i in range(0,listLength): #for each item in the fields provided
                self.check_field_exists(strTable, str(arrFields[i]))
                if i == 0: #for the first item
                    if listLength > 1:
                        strInsert = "INSERT INTO " + strTable + " (" + str(arrFields[i]) + "," #provide the field name but with the necessary SQL insert string
                    else:
                        strInsert = "INSERT INTO " + strTable + " (" + str(arrFields[i])

                if i > 0 and i < listLength - 1: #for intermediate fields
                    if listLength > 1:
                        strInsert = strInsert + arrFields[i] + "," #enter the field name followed by a comma
                    else:
                        strInsert = strInsert + arrFields[i]

                if i == listLength - 1: #for the final field name
                    if listLength > 1:
                        strInsert = strInsert + arrFields[i] + ") " #finish with a bracket
                    else:
                        strInsert = strInsert + ") " #If there is only one list item then no need to include arrFields[i] as this will have already been included

            for i in range(0,listLength): #for each item in the fields provided
                if i == 0: #for the first item
                    if listLength > 1:
                        strInsert = strInsert + "VALUES (?," #enter the SQL VALUES string with a question mark for the first value item to be provided
                    else:
                        strInsert = strInsert + "VALUES (?"

                if i > 0 and i < listLength - 1: #for intermediate fields enter
                    if listLength > 1:
                        strInsert = strInsert + "?," #a question mark followed by comma
                    else:
                        strInsert = strInsert + "?"

                if i == listLength - 1: #for the final field
                    if listLength > 1:
                        strInsert = strInsert + "?)" #enter a question mark follwed by a close bracket
                    else:
                        strInsert = strInsert + ")" #If there is only one list item then the '?' will have aready been included

            #print(strInsert + str(arrVals)) #optional if you want to see the string that is produced
            self.DBConn.execute(strInsert, arrVals) #connect to the database and execute the INSERT with the list arrVals
            self.DBConn.commit() #commit the insertion
            #self.DBConn.close() #close the connection to the database

    def check_table_exists(self, dictInstructions, strTable):
        strSQL = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='" + strTable + "'"
        self.c.execute(strSQL)
        TBL_Count = self.c.fetchone()[0]
        if TBL_Count == 0:
            lstDefaults = []
            lstDefaults.append(dictInstructions['Solar_Inputs']['Defaults']['Database_Table_Name'])
            lstDefaults.append(dictInstructions['HP_Inputs']['Defaults']['Database_Table_Name'])
            lstDefaults.append(dictInstructions['PV_Inputs']['Defaults']['Database_Table_Name'])
            lstDefaults.append(dictInstructions['BAT_Inputs']['Defaults']['Database_Table_Name'])
            lstDefaults.append(dictInstructions['ZONE_Inputs']['Defaults']['Database_Table_Name'])

            lstTitles = ['Solar_Inputs', 'HP_Inputs', 'PV_Inputs', 'BAT_Inputs', 'ZONE_Inputs']

            for i in range(0, len(lstDefaults)):
                if lstDefaults[i] == strTable:
                    strInfo = lstTitles[i]
                    break

            # Info
            lstInfo = create_table_string(dictInstructions, strInfo)
            strTableSQL = lstInfo[0]
            self.lstFields = lstInfo[1]
            self.c.execute(strTableSQL)

    def check_field_exists(self, strTable, strField):
        strSQL = "SELECT COUNT(*) AS CNTREC FROM pragma_table_info('" + strTable + "') WHERE name='" + strField + "'"
        self.c.execute(strSQL)
        if self.c.fetchone()[0] == 0:
            strFieldSQL = "ALTER TABLE " + strTable + " ADD COLUMN " + strField + " TEXT;"
            self.c.execute(strFieldSQL)

    def close_connection(self):
        self.DBConn.close()

    def export_CSV(self, strTable, lstFields):
        data = self.c.execute("SELECT * FROM " + strTable) #Extract all of the data from the database for the current year

        with open(self.strPath + strTable +'.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(lstFields)
            writer.writerows(data)

    def sum_data_in_current_day(self, strTable, strField, dictInstructions):
        dtCurr = dt.datetime.now()
        strCurrMonth = str(dtCurr.month)
        if len(strCurrMonth) == 1:
            strCurrMonth = '0' + strCurrMonth
        strCurrDay = str(dtCurr.day)
        if len(strCurrDay) == 1:
            strCurrDay = '0' + strCurrDay

        dtTomorrow = dtCurr + dt.timedelta(days=1)
        strTomMonth = str(dtTomorrow.month)
        if len(strTomMonth) == 1:
            strTomMonth = '0' + strTomMonth
        strTomDay = str(dtTomorrow.day)
        if len(strTomDay) == 1:
            strTomDay = '0' + strTomDay

        strDateToday = str(dtCurr.year) + "-" + strCurrMonth + "-" + strCurrDay
        strDateTomorrow = str(dtTomorrow.year) + "-" + strTomMonth + "-" + strTomDay
        strSQL = "SELECT SUM(" + strField + ") FROM " + strTable + " WHERE date(Time_Stamp) BETWEEN date('" + strDateToday + "') AND date('" + strDateTomorrow +"')"
        #print(strSQL)
        self.c.execute(strSQL)
        sum_field = self.c.fetchone()[0]
        return sum_field

    def sum_query_between_times(self,strStartDate, strEndDate, strStartTime, strEndTime, strField, strTable):
        strSQL = "SELECT SUM(" + strField + ") FROM " + strTable + " WHERE date(Time_Stamp) BETWEEN date('" + strStartDate + "') AND date('" + strEndDate +"') AND time(Time_Stamp) >= ('" + strStartTime + "') AND time(Time_Stamp) <= ('" + strEndTime +"')"
        #print(strSQL)
        self.c.execute(strSQL)
        sum_field = self.c.fetchone()[0]
        return sum_field

    def avg_query_between_times(self,strStartDate, strEndDate, strStartTime, strEndTime, strField, strTable):
        sum_0 = self.sum_query_between_times(strStartDate, strEndDate, strStartTime, strEndTime, strField, strTable)
        if sum_0 != 0:
            strSQL = "SELECT AVG(" + strField + ") FROM " + strTable + " WHERE date(Time_Stamp) BETWEEN date('" + strStartDate + "') AND date('" + strEndDate +"') AND time(Time_Stamp) >= ('" + strStartTime + "') AND time(Time_Stamp) <= ('" + strEndTime +"')"
            #print(strSQL)
            self.c.execute(strSQL)
            sum_field = self.c.fetchone()[0]
        else:
            sum_field = 0
        return sum_field

    def heat_xchange_thread(self, dictInstructions):
        lstTimes = chk_time.Check_Time_4_heat_xchange()
        boolRunXChange = lstTimes[0]
        if boolRunXChange == True:
            strHours = lstTimes[1]
            BMS_GUI = dictInstructions['General_Inputs']['GUI_BMS']
            BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']
            dtGUIStart = dictInstructions['General_Inputs']['Time_Stamp']['GUI_Default']
            dtDerivedReadTime = dt.datetime.now(tz=timezone.utc)

            if dictInstructions['User_Inputs']['Heat_Pump'] == True:
                #HEAT PUMP
                #Heat Pump Temperature
                strField = dictInstructions['HP_Inputs']['GUI_Information']['Outlet_Temperature']['SQL_Title']
                strTable = dictInstructions['HP_Inputs']['GUI_Information']['Outlet_Temperature']['SQL_Table']
                avOutletTemp = self.avg_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if avOutletTemp == None:
                    avOutletTemp = 0

                strField = dictInstructions['HP_Inputs']['GUI_Information']['Inlet_Temperature']['SQL_Title']
                strTable = dictInstructions['HP_Inputs']['GUI_Information']['Inlet_Temperature']['SQL_Table']
                avInletTemp = self.avg_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if avInletTemp == None:
                    avInletTemp = 0
                avDeltaT = avOutletTemp - avInletTemp

                #Heat Pump litres delivered
                strField = dictInstructions['HP_Inputs']['GUI_Information']['Flow_Rate']['SQL_Title']
                strTable = dictInstructions['HP_Inputs']['GUI_Information']['Flow_Rate']['SQL_Table']
                totalLitres = self.sum_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if totalLitres == None:
                    totalLitres = 0

                #Heat pump: heat transferred over hour
                glycol = dictInstructions['User_Inputs']['HP_Glycol_Mix']
                specific_heat = derived.ethelyne_glycol_heat_capacity(glycol)
                Wh_thermal = specific_heat * totalLitres * avDeltaT * (10**3) / 3600 #KJ/KG converted to J/KG by 10^3

                strLastHour = chk_time.Return_Time_Deltas(dtDerivedReadTime,60)
                fltHRLitres = self.sum_query_between_times(strLastHour[2], strLastHour[3], strLastHour[4], strLastHour[5], strField, strTable)
                dictInstructions['HP_Inputs']['GUI_Information']['Flow_Rate']['GUI_Val'].config(text=str(fltHRLitres))

                #Electricity from external unit during day
                strField = dictInstructions['HP_Inputs']['GUI_Information']['External_Unit_Elec_Wh']['SQL_Title']
                strTable = dictInstructions['HP_Inputs']['GUI_Information']['External_Unit_Elec_Wh']['SQL_Table']
                totalHourExternalUnit = self.sum_query_between_times(strLastHour[2], strLastHour[3], strLastHour[4], strLastHour[5], strField, strTable)
                if totalHourExternalUnit == None:
                    totalHourExternalUnit = 0
                totalDayExternalUnit = self.sum_data_in_current_day(strTable, strField, dictInstructions)
                if totalDayExternalUnit == None:
                    totalDayExternalUnit = 0

                #Electricity from internal unit
                strField = dictInstructions['HP_Inputs']['GUI_Information']['Internal_Unit_Elec_Wh']['SQL_Title']
                strTable = dictInstructions['HP_Inputs']['GUI_Information']['Internal_Unit_Elec_Wh']['SQL_Table']
                totalHourInternalUnit = self.sum_query_between_times(strLastHour[2], strLastHour[3], strLastHour[4], strLastHour[5], strField, strTable)
                if totalHourInternalUnit == None or dictInstructions['User_Inputs']['Include_internal_unit_in_COP'] == False:
                    totalHourInternalUnit = 0
                totalDayInternalUnit = self.sum_data_in_current_day(strTable, strField, dictInstructions)
                if totalDayInternalUnit == None or dictInstructions['User_Inputs']['Include_internal_unit_in_COP'] == False:
                    totalDayInternalUnit = 0

                totalHPDayElectricity = totalDayExternalUnit + totalDayInternalUnit
                totalHPHourElectricity = totalHourExternalUnit + totalHourInternalUnit

                #Total Heat Pump Heat in Day
                strField = dictInstructions['HP_Inputs']['GUI_Information']['Heat_load']['SQL_Title']
                strTable = dictInstructions['HP_Inputs']['GUI_Information']['Heat_load']['SQL_Table']
                totalHeat = self.sum_data_in_current_day(strTable, strField, dictInstructions)

                if totalHeat == None:
                    totalHeat = 0
                totalHeat = totalHeat + Wh_thermal

                fltHeatLastHR = self.sum_query_between_times(strLastHour[2], strLastHour[3], strLastHour[4], strLastHour[5], strField, strTable)
                if fltHeatLastHR == None:
                    fltHeatLastHR = 0
                fltHeatLastHR = fltHeatLastHR + Wh_thermal

                seconds_elapsed = chk_time.time_elase_between_times_s(strHours[6], strHours[7])
                W_Capacity = Wh_thermal * (3600 / seconds_elapsed)

                if totalHPDayElectricity != 0:
                    CoPDay = totalHeat / totalHPDayElectricity
                else:
                    CoPDay = 0
                BMS_GUI.HP_Gauge.add_gauge_line(CoPDay)

                if totalHPHourElectricity != 0:
                    CoPHour = fltHeatLastHR / totalHPHourElectricity
                else:
                    CoPHour = 0

                strOutput = str(CoPHour)
                lstGUIIncluded = dictInstructions['HP_Inputs']['GUI_Sections'][0] #If item is included on the GUI (as opposed to just being an SQL only item)
                ID = dictInstructions['HP_Inputs']['GUI_Information']['HP_CoP']['ID']
                for j in range(0,len(lstGUIIncluded)):
                    if lstGUIIncluded[j] == ID:
                        dictInstructions['HP_Inputs']['GUI_Information']['HP_CoP']['GUI_Val'].config(text=strOutput[:5])

                #Record Heat transfer derived in last period
                lstWh = [False, 0, Wh_thermal]
                lstCapacity = [False, 0, W_Capacity]
                lstReadTimes = [False, dtDerivedReadTime, dtDerivedReadTime]

                BMS_thread_lock.acquire(True)
                dictInstructions['HP_Inputs']['GUI_Information']['Heat_load']['Derived_Minute_Average'] = lstWh
                dictInstructions['HP_Inputs']['GUI_Information']['Heat_load']['Derived_read_times'] = lstReadTimes
                dictInstructions['HP_Inputs']['GUI_Information']['Thermal_Capacity']['Derived_Minute_Average'] = lstCapacity #As this is hourly calculated the kWh and kW are the same
                dictInstructions['HP_Inputs']['GUI_Information']['Thermal_Capacity']['Derived_read_times'] = lstReadTimes
                BMS_thread_lock.release()

                strOutput = str(W_Capacity)
                dictInstructions['HP_Inputs']['GUI_Information']['Thermal_Capacity']['GUI_Val'].config(text=strOutput[:5])

                lstLastMinute = [False, 0, CoPHour]
                lstReadTimes = [False, dtDerivedReadTime, dtDerivedReadTime]

                BMS_thread_lock.acquire(True)
                dictInstructions['HP_Inputs']['GUI_Information']['HP_CoP']['Derived_Minute_Average'] = lstLastMinute
                dictInstructions['HP_Inputs']['GUI_Information']['HP_CoP']['Derived_read_times'] = lstReadTimes
                BMS_thread_lock.release()

            if dictInstructions['User_Inputs']['Solar_Thermal'] == True:
                #SOLAR THERMAL
                #Solar Temperature
                strField = dictInstructions['Solar_Inputs']['GUI_Information']['Collector_temp']['SQL_Title']
                strTable = dictInstructions['Solar_Inputs']['GUI_Information']['Collector_temp']['SQL_Table']
                avFlowTemp = self.avg_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if avFlowTemp == None:
                    avFlowTemp = 0

                #print("FlowTemp: " + str(avFlowTemp))

                solar_coil_location = dictInstructions['User_Inputs']['Solar_Coil_Location']
                lstSolarCoil = ['Tank_bot_temp', 'Tank_temp', 'Tank_top_temp']
                strField = dictInstructions['Solar_Inputs']['GUI_Information'][lstSolarCoil[solar_coil_location]]['SQL_Title']
                strTable = dictInstructions['Solar_Inputs']['GUI_Information'][lstSolarCoil[solar_coil_location]]['SQL_Table']
                avReturnTemp = self.avg_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if avReturnTemp == None:
                    avReturnTemp = 0
                avDeltaT = avFlowTemp - avReturnTemp

                #print("ReturnTemp: " + str(avReturnTemp))
                #print("DeltaT: " + str(avDeltaT))

                strLastHour = chk_time.Return_Time_Deltas(dtDerivedReadTime,60)

                #Solar litres delivered
                strField = dictInstructions['Solar_Inputs']['GUI_Information']['Flow_Rate']['SQL_Title']
                strTable = dictInstructions['Solar_Inputs']['GUI_Information']['Flow_Rate']['SQL_Table']
                totalLitres = self.sum_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if totalLitres == None:
                    totalLitres = 0
                LitresInHR = self.sum_query_between_times(strLastHour[2], strLastHour[3], strLastHour[4], strLastHour[5], strField, strTable)
                dictInstructions['Solar_Inputs']['GUI_Information']['Flow_Rate']['GUI_Val'].config(text=str(LitresInHR))

                #print("TotalLitres: " + str(totalLitres))

                #Solar thermal: heat transferred over hour
                glycol = dictInstructions['User_Inputs']['Glycol_Mix']
                specific_heat = derived.ethelyne_glycol_heat_capacity(glycol)
                Wh_thermal = specific_heat * totalLitres * avDeltaT * (10**3) / 3600 #KJ/KG converted to J/KG by 10^3

                #print("SpecificHeat: " + str(specific_heat))
                #print("Wh_thermal: " + str(Wh_thermal))

                lstLastMinute = [False, 0, Wh_thermal]
                lstReadTimes = [False, dtDerivedReadTime, dtDerivedReadTime]

                BMS_thread_lock.acquire(True)
                dictInstructions['Solar_Inputs']['GUI_Information']['Heat_load']['Derived_Minute_Average'] = lstLastMinute
                dictInstructions['Solar_Inputs']['GUI_Information']['Heat_load']['Derived_read_times'] = lstReadTimes
                BMS_thread_lock.release()

            if dictInstructions['User_Inputs']['Zone'] == True:
                tm_current = dt.datetime.now(tz=timezone.utc)
                lstLastHR = chk_time.Return_Time_Deltas(tm_current, 60) #Last Hour
                Wh_solar = 0
                Wh_HP = 0
                if dictInstructions['User_Inputs']['Solar_Thermal'] == True:
                    strField = dictInstructions['Solar_Inputs']['GUI_Information']['Heat_load']['SQL_Title']
                    strTable = dictInstructions['Solar_Inputs']['GUI_Information']['Heat_load']['SQL_Table']
                    Wh_solar = self.sum_query_between_times(lstLastHR[2], lstLastHR[3], lstLastHR[4], lstLastHR[5], strField, strTable)
                if dictInstructions['User_Inputs']['Heat_Pump'] == True:
                    strField = dictInstructions['HP_Inputs']['GUI_Information']['Heat_load']['SQL_Title']
                    strTable = dictInstructions['HP_Inputs']['GUI_Information']['Heat_load']['SQL_Table']
                    Wh_HP = self.sum_query_between_times(lstLastHR[2], lstLastHR[3], lstLastHR[4], lstLastHR[5], strField, strTable)
                Wh_Combined = Wh_solar + Wh_HP #As only 1 hour has been looked back the Wh = Wth
                BMS_GUI.Zone_Gauge.add_gauge_line(Wh_Combined)

    def upload_sensors(self, dictInstructions, lstGphInfo):
        arrFields = []
        arrVals = []
        x_min = chk_time.return_abs_minute_in_day()
        flt_x_min = float(x_min)
        x_hr = flt_x_min / 60
        BMS_GUI = dictInstructions['General_Inputs']['GUI_BMS']
        BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']
        boolPlot = False
	
        lstInclude = ['Solar_Thermal', 'Heat_Pump', 'PV', 'Battery', 'Zone']
        lstTech = ['Solar_Inputs', 'HP_Inputs', 'PV_Inputs', 'BAT_Inputs', 'ZONE_Inputs']

        for i in range(0,len(lstTech)):
            #print(lstTech[i])
            if dictInstructions['User_Inputs'][lstInclude[i]] == True:
                strTable = dictInstructions[lstTech[i]]['Defaults']['Database_Table_Name']
                for key in dictInstructions[lstTech[i]]['GUI_Information']:
                    if dictInstructions[lstTech[i]]['GUI_Information'][key]['Include?'] == True:
                        avOutput = 0
                        #Sensor readings
                        if dictInstructions[lstTech[i]]['GUI_Information'][key]['Sensor'] == True:
                            if dictInstructions[lstTech[i]]['GUI_Information'][key]['Minute_Average'] != None:
                                arrFields.append(dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Title'])
                                BMS_thread_lock.acquire(True)
                                lstLastMin = dictInstructions[lstTech[i]]['GUI_Information'][key]['Minute_Average']
                                lstReadTimes = dictInstructions[lstTech[i]]['GUI_Information'][key]['Sensor_Read_Times']
                                BMS_thread_lock.release()
                                fltTotalVal = 0
                                for j in range(2,len(lstLastMin)): #The first 'bit' of lstLastMin is whether the data has been downloaded; the second 'bit' is from the previous minute
                                    if i != 4: #Not zone data
                                        fltTotalVal = fltTotalVal + lstLastMin[j]
                                    else: #For Zones - if it's been on when read then add 1 or else add zero. Av. will provide % over minute
                                        if fltTotalVal == "ON":
                                            fltTotalVal = 1 + fltTotalVal
                                        else:
                                            fltTotalVal = 0 + fltTotalVal
                                avOutput = fltTotalVal / (len(lstLastMin) - 2)
                                arrVals.append(avOutput)
                                lstLastMin[0] = True
                                lstReadTimes[0] = True
                                #print(lstLastMin)
                                BMS_thread_lock.acquire(True)
                                dictInstructions[lstTech[i]]['GUI_Information'][key]['Minute_Average'] = lstLastMin
                                dictInstructions[lstTech[i]]['GUI_Information'][key]['Sensor_Read_Times'] = lstReadTimes
                                BMS_thread_lock.release()

                        #Pulse meters
                        if dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_Meter'] == True:
                            if dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_Minute_Readings'] != None:

                                BMS_thread_lock.acquire(True)
                                lstLastMin = dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_Minute_Readings']
                                lstReadTimes = dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_reading_times']
                                BMS_thread_lock.release()
                                avOutput = 0

                                if lstLastMin[0] == False: #There has been an update since the last minute
                                    for j in range(1,len(lstLastMin)): #The first 'bit' of lstLastMin is whether the data has been downloaded
                                        avOutput = avOutput + float(lstLastMin[j]) #add all the pulse values taken in the minute

                                    lstLastMin = [True,0, 0] #When passing the array back to the global list as the pulse values have been recorded these are wiped but the times of the read are retained
                                    lstReadTimes = [True,lstReadTimes[len(lstReadTimes)-2], lstReadTimes[len(lstReadTimes)-1]]

                                    BMS_thread_lock.acquire(True)
                                    dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_Minute_Readings'] = lstLastMin
                                    dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_reading_times'] = lstReadTimes
                                    BMS_thread_lock.release()

                                    arrFields.append(dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Title'])
                                    arrVals.append(avOutput) #Extract the total value to the SQL database (if there has been no update then it will append 0

                                if dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_calc_flow'] == False: #The pulse meter is an electricity sub-meter
                                    strTable = dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Table']
                                    strField = dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Title']
                                    fltDayTotal = self.sum_data_in_current_day(strTable, strField, dictInstructions) #Get the cumulative Wh electricity consumption / generation recorded in the day
                                    if fltDayTotal == None:
                                        fltDayTotal = 0
                                    lstIncludeGUI = dictInstructions[lstTech[i]]['GUI_Sections'][0]
                                    for j in range(0,len(lstIncludeGUI)):
                                        if dictInstructions[lstTech[i]]['GUI_Information'][key]['ID'] == lstIncludeGUI[j]:
                                            dictInstructions[lstTech[i]]['GUI_Information'][key]['GUI_Val'].config(text=str(fltDayTotal)[:5])

                        #Derived Values from sensor measurements as opposed to direct sensor measured values
                        boolDerived = dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Val']
                        if boolDerived == True:
                            #print(str(lstTech[i]) + ': ' + str(key))
                            #Print the total day generation / consumption to the GUI
                            if dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_total?'] == True:
                                lstIncludeGUI = dictInstructions[lstTech[i]]['GUI_Sections'][0]
                                for j in range(0,len(lstIncludeGUI)):
                                    if dictInstructions[lstTech[i]]['GUI_Information'][key]['ID'] == lstIncludeGUI[j]:
                                        strTable = dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Table']
                                        strField = dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Title']
                                        fltDayTotal = self.sum_data_in_current_day(strTable, strField, dictInstructions)
                                        if fltDayTotal == None:
                                            fltDayTotal = 0
                                        #print(fltDayTotal)
                                        dictInstructions[lstTech[i]]['GUI_Information'][key]['GUI_Val'].config(text=str(fltDayTotal)[:5])

                            #Evaluate the in minute derived values recorded
                            if dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Minute_Average'] != None:
                                avOutput = 0

                                BMS_thread_lock.acquire(True)
                                lstLastMin = dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Minute_Average']
                                lstReadTimes = dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_read_times']
                                BMS_thread_lock.release()
                                fltTotalVal = 0

                                if lstLastMin[0] == False: #There has been a change in the last minute
                                    for j in range(1,len(lstLastMin)): #The first 'bit' of lstLastMin is whether the data has been downloaded
                                        fltTotalVal = fltTotalVal + float(lstLastMin[j])
                                    if dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_total?'] == True:
                                        avOutput = fltTotalVal
                                        #Where minute totals are taken the GUI should display the in day total generation / consumption rather than just the minute
                                    else:
                                        avOutput = fltTotalVal / (len(lstLastMin) - 2) #Minus two as the first value is 0 and the second value will be the carry forward from the previous minute

                                    lstLastMin[0] = True
                                    lstReadTimes[0] = True

                                    #if dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_DB_Total?'] == True: #DB queries occur each hour and so need to set the short term memory to 0 to avoid storing the same value each minute of the hour
                                    #    lstLastMin = [True, 0]
                                    #    lstReadTimes = [True, dt.datetime.now()]

                                    BMS_thread_lock.acquire(True)
                                    dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_Minute_Average'] = lstLastMin
                                    dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_read_times'] = lstReadTimes
                                    BMS_thread_lock.release()

                                    arrFields.append(dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Title'])
                                    arrVals.append(avOutput)

                        if dictInstructions[lstTech[i]]['GUI_Information'][key]['Plot_Values?'] == True:
                            BMS_thread_lock.acquire(True)
                            lstDayPlot = dictInstructions[lstTech[i]]['GUI_Information'][key]['Plot_Value_List']
                            BMS_thread_lock.release()

                            boolPulse = dictInstructions[lstTech[i]]['GUI_Information'][key]['Pulse_Meter']
                            boolDerivedTotal = False
                            if boolDerived == True:
                                boolDerivedTotal = dictInstructions[lstTech[i]]['GUI_Information'][key]['Derived_total?']

                            if boolPulse == True or boolDerivedTotal == True: #If what is being plotted is a pulse meter then we are interested (for graphing purposes) in the day total
                                strTable = dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Table']
                                strField = dictInstructions[lstTech[i]]['GUI_Information'][key]['SQL_Title']
                                fltDayTotal = self.sum_data_in_current_day(strTable, strField, dictInstructions)
                                if fltDayTotal == None:
                                    fltDayTotal = 0
                                lstXY = [x_hr, fltDayTotal]
                            else:
                                    lstXY = [x_hr, avOutput]

                            lstGphInfoUpdate = chk_time.Check_Time_4_Graph(lstGphInfo[0], lstGphInfo[1])
                            boolPlot = lstGphInfoUpdate[0]
                            if boolPlot == True:
                                lstDayPlot.append(lstXY)
                                #print(lstDayPlot)
                                BMS_thread_lock.acquire(True)
                                dictInstructions[lstTech[i]]['GUI_Information'][key]['Plot_Value_List'] = lstDayPlot
                                BMS_thread_lock.release()

                            strColour = dictInstructions[lstTech[i]]['GUI_Information'][key]['Plot_colour']
                            fltIndex = dictInstructions[lstTech[i]]['GUI_Information'][key]['Plot_index']
                            strTitle = dictInstructions[lstTech[i]]['GUI_Information'][key]['Plot_label']

                            if i == 0:
                                if boolPlot == True:
                                    BMS_GUI.Solar_Graph.plot_chart(lstDayPlot, strColour, fltIndex, strTitle)
                            if i == 1:
                                if boolPlot == True:
                                    BMS_GUI.HP_Graph.plot_chart(lstDayPlot, strColour, fltIndex, strTitle)
                            if i == 2:
                                if boolPlot == True:
                                    BMS_GUI.PV_Graph.plot_chart(lstDayPlot, strColour, fltIndex, strTitle)
                            if i == 3:
                                if boolPlot == True:
                                    BMS_GUI.BAT_Graph.plot_chart(lstDayPlot, strColour, fltIndex, strTitle)
                            if i == 4:
                                if boolPlot == True:
                                    BMS_GUI.Zone_Graph.plot_chart(lstDayPlot, strColour, fltIndex, strTitle)

                self.check_table_exists(dictInstructions, strTable)
                self.upload_data(strTable, arrFields, arrVals)
                arrFields = []
                arrVals = []
        #print(lstGphInfoUpdate[1:])
        return lstGphInfoUpdate[1:]

    def PV_Gauge(self, dictInstructions):
        boolUpdate = chk_time.Check_Time_4_Gauge()
        dtCurr = dt.datetime.now(tz=timezone.utc)

        if boolUpdate == True:
            if dictInstructions['User_Inputs']['PV'] == True:
                BMS_GUI = dictInstructions['General_Inputs']['GUI_BMS']
                strHours = chk_time.Return_Time_Deltas(dtCurr,60)
                strField = dictInstructions['PV_Inputs']['GUI_Information']['Generation']['SQL_Title']
                strTable = dictInstructions['PV_Inputs']['GUI_Information']['Generation']['SQL_Table']
                kWhe_last_hour = self.sum_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if kWhe_last_hour == None:
                    kWhe_last_hour = 0
                kWe_last_hour = kWhe_last_hour
                BMS_GUI.PV_Gauge.add_gauge_line(kWe_last_hour)

    def Solar_Gauge(self, dictInstructions):
        boolUpdate = chk_time.Check_Time_4_Gauge()
        dtCurr = dt.datetime.now(tz=timezone.utc)

        if boolUpdate == True:
            if dictInstructions['User_Inputs']['Solar_Thermal'] == True:
                dtDerivedReadTime = dt.datetime.now()
                BMS_GUI = dictInstructions['General_Inputs']['GUI_BMS']
                BMS_thread_lock = dictInstructions['Threads']['BMS_thread_lock']
                strHours = chk_time.Return_Time_Deltas(dtCurr,60)
                strField = dictInstructions['Solar_Inputs']['GUI_Information']['Heat_load']['SQL_Title']
                strTable = dictInstructions['Solar_Inputs']['GUI_Information']['Heat_load']['SQL_Table']
                kWhe_last_hour = self.sum_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
                if kWhe_last_hour == None:
                    kWhe_last_hour = 0
                kWe_last_hour = kWhe_last_hour
                BMS_GUI.Solar_Gauge.add_gauge_line(kWe_last_hour)

                lstLastMinute = [False, 0, kWe_last_hour]
                lstReadTimes = [False, dtDerivedReadTime, dtDerivedReadTime]

                BMS_thread_lock.acquire(True)
                dictInstructions['Solar_Inputs']['GUI_Information']['Heat_capacity']['Derived_Minute_Average'] = lstLastMinute
                dictInstructions['Solar_Inputs']['GUI_Information']['Heat_capacity']['Derived_read_times'] = lstReadTimes
                BMS_thread_lock.release()

                strOutput = str(kWe_last_hour)
                dictInstructions['Solar_Inputs']['GUI_Information']['Heat_capacity']['GUI_Val'].config(text=strOutput[:5])

def DB_extract_graph_update_thread(dictInstructions):
    #Extracts data to database and plots on BMS chart each minute on constant loop while user has not pressed quit
    HeatSet_DB = manage_database(dictInstructions)
    BMS_GUI = dictInstructions['General_Inputs']['GUI_BMS']
    dictInstructions['Database'] = HeatSet_DB
    current_tm = dt.datetime.now()

    bytCurrentLoop = 0
    current_tm = dt.datetime.now()
    intPrevMin = current_tm.minute - 1
    lstGphInfo = [bytCurrentLoop, intPrevMin]

    while BMS_GUI.quit_sys == False:
        lstLoopVals = chk_time.Check_Time_4_Store(bytCurrentLoop, intPrevMin)
        boolExtract = lstLoopVals[0]
        if boolExtract == True:
            HeatSet_DB.heat_xchange_thread(dictInstructions)
            lstGphInfo = HeatSet_DB.upload_sensors(dictInstructions, lstGphInfo)
            HeatSet_DB.PV_Gauge(dictInstructions)
            HeatSet_DB.Solar_Gauge(dictInstructions)
        bytCurrentLoop = lstLoopVals[1]
        intPrevMin = lstLoopVals[2]

        current_tm = dt.datetime.now()
        current_minute = current_tm.minute
        if current_minute == 1: #Extract CSV files every hour
            #Extract CSVs
            if dictInstructions['User_Inputs']['Solar_Thermal'] == True:
                lstSolar = HeatSet_DB.lstSolarFields
                HeatSet_DB.export_CSV('SOLAR', lstSolar)

            if dictInstructions['User_Inputs']['Heat_Pump'] == True:
                lstHP = HeatSet_DB.lstHPFields
                HeatSet_DB.export_CSV('HP', lstHP)

            if dictInstructions['User_Inputs']['PV'] == True:
                lstPV = HeatSet_DB.lstPVFields
                HeatSet_DB.export_CSV('PV', lstPV)

            if dictInstructions['User_Inputs']['Battery'] == True:
                lstBat = HeatSet_DB.lstBatFields
                HeatSet_DB.export_CSV('Battery', lstBat)

            if dictInstructions['User_Inputs']['Zone'] == True:
                lstBat = HeatSet_DB.lstZoneFields
                HeatSet_DB.export_CSV('Zone', lstBat)

        time.sleep(5)
        #print('Current Loop: ' + str(bytCurrentLoop) + ', Previous Minute: ' + str(intPrevMin))

    HeatSet_DB.close_connection()

'''
from A_Initialise import *
HeatSet_DB = manage_database(dictGlobalInstructions)
#HeatSet_DB.heat_xchange_thread(dictGlobalInstructions)
#total_heat = HeatSet_DB.sum_data_in_current_day("SOLAR", "Pressure_bar", dictGlobalInstructions)
#strHours = HeatSet_DB.Hour_Strings()
#print(strHours)
#strField = dictGlobalInstructions['HP_Inputs']['GUI_Information']['Outlet_Temperature']['SQL_Title']
#strTable = dictGlobalInstructions['HP_Inputs']['GUI_Information']['Outlet_Temperature']['SQL_Table']
#avOutletTemp = HeatSet_DB.sum_query_between_times(strHours[2], strHours[3], strHours[4], strHours[5], strField, strTable)
#print (avOutletTemp)

lstSolar = HeatSet_DB.lstSolarFields
HeatSet_DB.export_CSV('SOLAR', lstSolar)
lstHP = HeatSet_DB.lstHPFields
HeatSet_DB.export_CSV('HP', lstHP)
lstPV = HeatSet_DB.lstPVFields
HeatSet_DB.export_CSV('PV', lstPV)
lstBat = HeatSet_DB.lstBatFields
HeatSet_DB.export_CSV('Battery', lstBat)
lstZone = HeatSet_DB.lstZoneFields
HeatSet_DB.export_CSV('Zone', lstZone)

HeatSet_DB.close_connection()
'''