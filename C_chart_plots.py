import tkinter as tk
from tkinter import *
import math

class GUI_graph:
    def __init__(self, dictInstructions, frmRoot):
        self.create(dictInstructions, frmRoot)

    def create(self, dictInstructions, frmRoot):
        self.series_count = 0

        frm_width = dictInstructions['Dimensions']['frm_width']
        frm_height = dictInstructions['Dimensions']['frm_height']
        frm_bd = dictInstructions['Dimensions']['frm_bd']
        self.graph_frame = Frame(frmRoot, width=frm_width, height=frm_height, bd=frm_bd)
        self.graph_frame.pack()

        self.box_width = dictInstructions['Dimensions']['bx_width']
        self.box_height = dictInstructions['Dimensions']['bx_height']
        self.graph_canvas = Canvas(self.graph_frame, width=self.box_width, height=self.box_height, highlightthickness=0)
        self.graph_canvas.pack()
        self.bx_x0 = dictInstructions['Dimensions']['bx_x0']
        self.bx_y0 = dictInstructions['Dimensions']['bx_y0']
        self.graph_canvas.place(y=self.bx_y0, x=self.bx_x0)

        frm_head = dictInstructions['Values']['frm_title']
        self.graph_title = self.graph_canvas.create_text(self.box_width/2, 10,text=frm_head)

        self.graph_offset = 35
        self.graph_width = self.box_width - (self.graph_offset*2)
        self.graph_height = self.box_height - (self.graph_offset*2)

        self.graph_canvas.create_line(self.graph_offset,
                                        self.graph_offset,
                                        self.graph_offset,
                                        self.graph_offset + self.graph_height,
                                        width=2,
                                        fill='blue') #y-axis
        self.strYTitle = dictInstructions['Values']['graph_y_title']
        self.graph_canvas.create_text(5, self.graph_height/2 + self.graph_offset, text=self.strYTitle, angle=90)
        self.graph_canvas.create_line(self.graph_offset, self.graph_offset + self.graph_height, self.graph_offset + self.graph_width, self.graph_offset + self.graph_height, width=2, fill='blue') #x-axis
        self.strXTitle = dictInstructions['Values']['graph_x_title']
        self.graph_canvas.create_text(self.graph_width/2 + self.graph_offset, self.graph_offset*2 + self.graph_height - 5, text=self.strXTitle)

        #Tickmarks
        tick_mark_min = dictInstructions['Values']['tm_length']
        tick_mark_maj = dictInstructions['Values']['tm_major_length']
        boolGrid = dictInstructions['Values']['include_grid']

        ##X-Axis-tickmarks
        graph_x_freq = dictInstructions['Values']['tm_x_count']
        self.dblMaxValX = dictInstructions['Values']['graph_x_max']
        self.dblMinValX = dictInstructions['Values']['graph_x_min']
        tick_mark_maj_marker = dictInstructions['Values']['tm_x_major']

        for i in range(1,graph_x_freq+1):
            x = self.graph_offset + self.graph_width * i/graph_x_freq
            if i % tick_mark_maj_marker == 0: #It's on a major tick mark
                tick_mark = tick_mark_maj
                ln_width = 2
                text_y = self.graph_offset + self.graph_height + tick_mark + 5
                text_val = (self.dblMaxValX - self.dblMinValX) * i / graph_x_freq + self.dblMinValX
                self.graph_canvas.create_text(x,text_y,text=str("%.0f"%round(text_val,0)),font=("Arial",8))
            else:
                tick_mark = tick_mark_min
                ln_width = 1

            if boolGrid == False:
                y0 = self.graph_offset + self.graph_height
                y1 = y0 + tick_mark
                self.graph_canvas.create_line(x,y0,x,y1,width=ln_width)
            else:
                y0 = self.graph_offset
                y1 = y0 + self.graph_height + tick_mark
                self.graph_canvas.create_line(x,y0,x,y1,width=ln_width,fill='dark grey')

        ##y-Axis-tickmarks
        graph_y_freq = dictInstructions['Values']['tm_y_count']
        self.dblMaxValY = dictInstructions['Values']['graph_y_max']
        self.dblMinValY = dictInstructions['Values']['graph_y_min']
        tick_mark_maj_marker = dictInstructions['Values']['tm_y_major']

        for i in range(0,graph_y_freq):
            y = self.graph_offset + self.graph_height * i/graph_y_freq
            if i % tick_mark_maj_marker == 0: #It's on a major tick mark
                tick_mark = tick_mark_maj
                ln_width = 2
                text_x = self.graph_offset - tick_mark - 5
                text_val = (self.dblMaxValY - self.dblMinValY) * (graph_y_freq - i) / graph_y_freq + self.dblMinValY
                self.graph_canvas.create_text(text_x,y,text=str("%.0f"%round(text_val,0)),font=("Arial",8))
            else:
                tick_mark = tick_mark_min
                ln_width = 1

            if boolGrid == False:
                x1 = self.graph_offset
                x0 = x1 - tick_mark
                self.graph_canvas.create_line(x0,y,x1,y,width=ln_width)
            else:
                x1 = self.graph_offset + self.graph_width
                x0 = self.graph_offset - tick_mark
                self.graph_canvas.create_line(x0,y,x1,y,width=ln_width,fill='dark grey')
        self.lstSeries = [] #[series #, series name]
        self.series_rectangle = self.graph_canvas.create_rectangle(0,0,0,0, fill="", outline="black")

    def update_graph_title(self, strNewTitle):
        self.graph_canvas.itemconfigure(self.graph_title, text=strNewTitle)

    def plot_chart(self, lstXY, strColour, bytSeries, strSeriesName): #lstXY needs to be in the form lstXY[i][x,y]
        boolFound = False
        for i in range(0, len(self.lstSeries)):
            if self.lstSeries[i]['Series_Num'] == bytSeries: #If the series number can be found
                boolFound = True
                series_ID = i
                continue

        if boolFound == False: #A new series has been provided
            series_ID = len(self.lstSeries)
            text_length = 30
            text_height = 10
            text_x = self.box_width - self.graph_offset - text_length
            text_y = (text_height * (series_ID+1)) + self.graph_offset
            self.graph_canvas.coords(self.series_rectangle,
                                        text_x - 30,
                                        self.graph_offset,
                                        text_x + text_length,
                                        text_y + text_height * (len(self.lstSeries)) + 5)
            self.graph_canvas.itemconfig(self.series_rectangle, fill='light grey')
            lblVal = self.graph_canvas.create_text(text_x,text_y,text=strSeriesName,font=("Arial",8), fill=strColour)
            dictSeries = {'Series_Num': bytSeries,
                            'Series_Name': strSeriesName,
                            'Series_Label': lblVal,
                            'Series_Plots': None}
            self.lstSeries.append(dictSeries)
        else: #An existing series is being updated so clear the existing plots for that series before making the new plot
            for plot_item in self.lstSeries[series_ID]['Series_Plots']:
                self.graph_canvas.delete(plot_item)

        plot_size = 4
        lstOvalPlots = []
        for i in range(0, len(lstXY)):
            plot_x = lstXY[i][0]
            plot_y = lstXY[i][1]
            position_x = self.graph_offset + ((plot_x - self.dblMinValX) / (self.dblMaxValX - self.dblMinValX) * self.graph_width)
            position_y = self.graph_offset + self.graph_height -((plot_y - self.dblMinValY) / (self.dblMaxValY - self.dblMinValY) * self.graph_height) #The plot starts from the top not the bottom of the y-axis plot which is why the the full length of the plot is used
            ovalPlot = self.graph_canvas.create_oval(position_x - plot_size/2,
                                            position_y - plot_size/2,
                                            position_x + plot_size/2,
                                            position_y + plot_size/2,
                                            fill=strColour,
                                            outline="")
            lstOvalPlots.append(ovalPlot)
        self.lstSeries[series_ID]['Series_Plots'] = lstOvalPlots

class GUI_gauge:
    def __init__(self, dictInstructions, frmRoot):
        self.create(dictInstructions, frmRoot) #create self

    def create(self, dictInstructions, frmRoot):
        frm_width = dictInstructions['Dimensions']['frm_width'] #get form width from instructions dictionary
        frm_height = dictInstructions['Dimensions']['frm_height'] #get form height from instructions dictionary
        frm_bd = dictInstructions['Dimensions']['frm_bd']
        self.gauge_frame = Frame(frmRoot, width=frm_width, height=frm_height, bd=frm_bd)
        self.gauge_frame.pack()

        self.box_width = dictInstructions['Dimensions']['bx_width']
        self.box_height = dictInstructions['Dimensions']['bx_height']

        self.gauge_canvas = Canvas(self.gauge_frame, width=self.box_width, height=self.box_height, highlightthickness=0)
        self.gauge_canvas.pack()
        self.bx_x0 = dictInstructions['Dimensions']['bx_x0']
        self.bx_y0 = dictInstructions['Dimensions']['bx_y0']
        self.gauge_canvas.place(y=self.bx_y0, x=self.bx_x0)

        frm_head = dictInstructions['Values']['frm_title']
        self.gauge_canvas.create_text(50, 20,text=frm_head)

        self.gauge_offset = 35
        self.gauge_width = self.box_width - (self.gauge_offset*2)
        self.gauge_height = self.box_height - (self.gauge_offset*2)
        self.gauge_x1 = self.gauge_offset + self.gauge_width
        self.gauge_y1 = self.gauge_offset + self.gauge_height
        self.gauge_arc = self.gauge_canvas.create_arc(self.gauge_offset,self.gauge_offset,self.gauge_x1,self.gauge_y1, extent=180, fill='red')
        self.radius = self.gauge_width/2
        tick_mark_min = dictInstructions['Values']['tm_length']
        tick_mark_maj = dictInstructions['Values']['tm_major_length']
        tick_mark_maj_marker = dictInstructions['Values']['tm_major']
        gauge_freq = dictInstructions['Values']['tm_count']
        thetaDegInc = 180 / gauge_freq
        self.dblMaxVal = dictInstructions['Values']['gauge_max']
        self.dblMinVal = dictInstructions['Values']['gauge_min']

        #Add tickmarks
        for i in range(0,gauge_freq+1):
            thetaDeg = thetaDegInc * i
            if i % tick_mark_maj_marker == 0: #It's on a major tick mark
                tick_mark = tick_mark_maj
                boolMaj = True
                ln_width = 2
            else:
                tick_mark = tick_mark_min
                boolMaj = False
                ln_width = 1

            if thetaDeg <= 90:
                thetaRad = thetaDeg * math.pi / 180
                opposite = self.radius * math.sin(thetaRad)
                adjacent = self.radius * math.cos(thetaRad)
                curve_point_x = self.box_width/2 - adjacent
                curve_point_y = self.box_height/2 - opposite
                outer_opposite = tick_mark * math.sin(thetaRad)
                outer_adjacent = tick_mark * math.cos(thetaRad)
                outer_point_x = curve_point_x - outer_adjacent
                outer_point_y = curve_point_y - outer_opposite
                if boolMaj == True:
                    text_dist = 10
                    text_outer_opposite = text_dist * math.sin(thetaRad)
                    text_outer_adjacent = text_dist * math.cos(thetaRad)
                    text_outer_x = outer_point_x - text_outer_adjacent
                    text_outer_y = outer_point_y - text_outer_opposite
                    text_val = (self.dblMaxVal - self.dblMinVal) * i / gauge_freq + self.dblMinVal
                    self.gauge_canvas.create_text(text_outer_x, text_outer_y,text="%.0f"%round(text_val,0))
            else:
                thetaDegADJ = 180 - thetaDeg
                thetaRad = thetaDegADJ * math.pi / 180
                opposite = self.radius * math.sin(thetaRad)
                adjacent = self.radius * math.cos(thetaRad)
                curve_point_x = self.box_width/2 + adjacent
                curve_point_y = self.box_height/2 - opposite
                outer_opposite = tick_mark * math.sin(thetaRad)
                outer_adjacent = tick_mark * math.cos(thetaRad)
                outer_point_x = curve_point_x + outer_adjacent
                outer_point_y = curve_point_y - outer_opposite
                if boolMaj == True:
                    text_dist = 10
                    text_outer_opposite = text_dist * math.sin(thetaRad)
                    text_outer_adjacent = text_dist * math.cos(thetaRad)
                    text_outer_x = outer_point_x + text_outer_adjacent
                    text_outer_y = outer_point_y - text_outer_opposite
                    text_val = (self.dblMaxVal - self.dblMinVal) * i / gauge_freq + self.dblMinVal
                    self.gauge_canvas.create_text(text_outer_x, text_outer_y,text="%.0f"%round(text_val,0))

            self.gauge_canvas.create_line(outer_point_x,outer_point_y,curve_point_x,curve_point_y, width=ln_width)

    def add_gauge_line(self, gauge_val):
        percent_complete = (gauge_val - self.dblMinVal) / (self.dblMaxVal - self.dblMinVal)
        if percent_complete > 1:
        	percent_complete = 1
        if percent_complete < 0:
        	percent_complete = 0
        thetaDeg = 180 * percent_complete
        if thetaDeg <= 90:
            thetaRad = thetaDeg * math.pi / 180
            opposite = self.radius * math.sin(thetaRad)
            adjacent = self.radius * math.cos(thetaRad)
            curve_point_x = self.box_width/2 - adjacent
            curve_point_y = self.box_height/2 - opposite
        else:
            thetaDegADJ = 180 - thetaDeg
            thetaRad = thetaDegADJ * math.pi / 180
            opposite = self.radius * math.sin(thetaRad)
            adjacent = self.radius * math.cos(thetaRad)
            curve_point_x = self.box_width/2 + adjacent
            curve_point_y = self.box_height/2 - opposite

        self.mid_gauge = self.box_width/2
        self.gauge_arc = self.gauge_canvas.create_arc(self.gauge_offset,self.gauge_offset,self.gauge_x1,self.gauge_y1, extent=180, fill='green')
        self.gauge_arc = self.gauge_canvas.create_arc(self.gauge_offset,self.gauge_offset,self.gauge_x1,self.gauge_y1, extent=180 - thetaDeg, fill='orange')
        self.gauge_canvas.create_line(curve_point_x,curve_point_y,self.mid_gauge,self.mid_gauge, fill='blue', width=2)
        dotRadius = 3
        self.guage_centre_dot = self.gauge_canvas.create_oval(self.mid_gauge + dotRadius, self.mid_gauge + dotRadius, self.mid_gauge - dotRadius, self.mid_gauge - dotRadius, fill='blue')
