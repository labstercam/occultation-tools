# *******************************************************************************************
# 
# SharpCap script "Calibration_LED_2024-09-29.py"
# 2024/09/29 Jean-Francois
#
# Version: 3.2.1:   Correction of small bugs and simplification of the "framehandler"
# Version: 3.2.0:   Update of the legends from OxyPlot library (for 4.1.11757 and after).
# Version: 3.1.0:   Automatic position of the analysis rectangle.
# Version: 3.0.1:   Small modification for disable the "Show graphics" at the start.
# Version: 3.0:     Version for SharpCap 4.1 and above. Show calibration graphics.
# Version: 2.1.2:   Modification of the colour of the button during the process
# Version: 2.1.1:   Very small changes
#
# The script works only with a PRO version of SharpCap.
#
#
# The script has to be started from the IronPython Console:
#
# The QHY-174-GPS camera has to be connected before starting the script.
# The GPS does not need to be activated.
#
# Note: the test of the script can be performed without the GPS.
# The LED calibration is independent from the GPS connection.
#
#
# In SharpCap, please follow these actions:
#
# - Copy the script somewhere on the computer
# - Start SharpCap
# - Connect the QHY-174-GPS camera
# - In "File" - "SharpCap Settings" - "Startup Scripts" - select the script green > button
# - Start the LED calibration
# - After the end of the calibration, show the graphics
# - Close the script by clicking "Exit" button
#
# The script moves the analysis rectangle to the region with the highest LED illumination.
# With the image full size: the script changes the size and the position of the analysis rectangle.
# With the image ROI: the script moves the ROI and the analysis rectangle over the full detector surface.
# The script replaces the ROI at the starting position after the LED calibration.
# The ROI position does not modify the Start and End values.
#
# Note: the LED calibration can be performed with stars visible on the image.
# As long as no bright stars are at the rim of the selection rectangle (and move in/out between different exposure).
#
# The script switch-on the LED automatically during the calibration process, if not activated.
# The script switch-off the LED automatically, if it was not activated before the start of the script.
#
# *******************************************************************************************


import time
import math
import clr
clr.AddReference("Oxyplot")
clr.AddReference("OxyPlot.WindowsForms ")
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")

import OxyPlot
import System.Drawing
import System.Windows.Forms

from System.Drawing import *
from System.Windows.Forms import *
from System.Threading import Thread, ApartmentState, ParameterizedThreadStart


#def framehandler(sender, args):
#    if (dumpdata):
#        global Mean
#        cutout = args.Frame.CutROI(SharpCap.Transforms.SelectionRect)
#        Stat = cutout.GetStats()
#        Mean = Stat.Item1
#        cutout.Release()

#def evthandler(sender, args):
#    if (SharpCap.SelectedCamera != None):
#        SharpCap.SelectedCamera.FrameCaptured -= framehandler

#def monitorFrames():
#    SharpCap.SelectedCamera.FrameCaptured += framehandler

#def Search_Weight_L(Y):
#    for i in range(1, len(Y)):
#        if (Y[i] < 0.0):
#            n = i
#            break
#    Weight = []
#    for k in range(0, len(Y)):
#        Weight.append(0.0)
#    Weight[n-1] = 1.0
#    Weight[n] = 1.0
#    return Weight

#def Search_Weight_R(Y):
#    for i in range(1, len(Y)):
#        if (Y[i] > 0.0):
#            n = i
#            break
#    Weight = []
#    for k in range(0, len(Y)):
#        Weight.append(0.0)
#    Weight[n-1] = 1.0
#    Weight[n] = 1.0
#    return Weight

# *****************************************************************************

def LED_Calibration(self):
    global dumpdata
    global Pos_start, Pos_end, LED_start, LED_end, Cal_Start_Pos, Cal_End_Pos
    global m_start, k_start, m_end, k_end
    global offset_start, offset_end, h_start, h_end

    def framehandler(sender, args):
        if (dumpdata):
            global Mean
            cutout = args.Frame.CutROI(SharpCap.Transforms.SelectionRect)
            Stat = cutout.GetStats()
            Mean = Stat.Item1
            cutout.Release()

    def Search_Weight_L(Y):
        for i in range(1, len(Y)):
            if (Y[i] < 0.0):
                n = i
                break
        Weight = []
        for k in range(0, len(Y)):
            Weight.append(0.0)
        Weight[n-1] = 1.0
        Weight[n] = 1.0
        return Weight

    def Search_Weight_R(Y):
        for i in range(1, len(Y)):
            if (Y[i] > 0.0):
                n = i
                break
        Weight = []
        for k in range(0, len(Y)):
            Weight.append(0.0)
        Weight[n-1] = 1.0
        Weight[n] = 1.0
        return Weight

    power_threshold = 3             # (10**power_threshold) digit

    if (SharpCap.SelectedCamera.SerialNumber == '544a3c4eba8fc6e52'):
        x_c = 1750      # LED area centre for QHY174GPS #2
    elif (SharpCap.SelectedCamera.SerialNumber == 'xyz'):
        x_c = 1650      # LED area centre for QHY174GPS #1
    else:
        x_c = 1650      # LED area centre   

    r_width  = 200   # LED rectangle width
    r_heigth = 600  # LED rectangle heigth

    Cal_End_Pos   = SharpCap.SelectedCamera.Controls.FindByName("Calibration End Pos Adjust").Value
    Cal_Start_Pos = SharpCap.SelectedCamera.Controls.FindByName("Calibration Start Pos Adjust").Value
    LED_status    = SharpCap.SelectedCamera.Controls.FindByName("GPS Calibration LED").Value
    expos_ms      = SharpCap.SelectedCamera.Controls.Exposure.ExposureMs

    self.Cal_LED.Text = "Calibration running"
    self.Cal_LED.BackColor = Color.Red
    self.Cal_LED.Enabled = False
    self.button_Exit.Enabled = False

    SharpCap.Transforms.SelectTransform("ROI Selection")                # Show Selection Rectangle

    B, H = SharpCap.SelectedCamera.Controls.Resolution.AvailableValues[0].split("x")
    B = int(B)
    H = int(H)

    x, y = SharpCap.SelectedCamera.Controls.Resolution.Value.split("x")
    x = int(x)
    y = int(y)
    if (r_heigth >= y):
        r_heigth = y - 20

    Pan_start = SharpCap.SelectedCamera.Controls.Pan.Value
    Tilt_start = SharpCap.SelectedCamera.Controls.Tilt.Value
    Rect_start = SharpCap.Transforms.SelectionRect

    Pan_max = B - x
    Tilt_max = H - y
    Pan_cal = int(x_c - x/2)
    Tilt_cal = int(H/2 - y/2)

    if (Pan_cal > Pan_max):
        Pan_cal = Pan_max
    if (Tilt_cal > Tilt_max):
        Tilt_cal = Tilt_max

    SharpCap.SelectedCamera.Controls.Pan.Value = Pan_cal
    SharpCap.SelectedCamera.Controls.Tilt.Value = Tilt_cal

    x_rect = int(x_c - Pan_cal - r_width/2)
    y_rect = int(H/2 - Tilt_cal - r_heigth/2)

    SharpCap.Transforms.SelectionRect = Rectangle(x_rect, y_rect, r_width, r_heigth)


    dumpdata = True
    SharpCap.SelectedCamera.FrameCaptured += framehandler
#    SharpCap.CaptureEvent += evthandler
#    monitorFrames()

    if (LED_status == "Off"):
        SharpCap.SelectedCamera.Controls.FindByName("GPS Calibration LED").Value = "On"

    expos_ms = SharpCap.SelectedCamera.Controls.Exposure.ExposureMs
    wait_time = 2.1 *(expos_ms / 1000.0) + 0.1
    print("Waiting Time: %5.3f" % (wait_time))

# *****************************************************************************
# LED Calibration Start Position Adjustment

    print()
    print("LED Calibration Start Position")
    print("***************************")

    Pos_start = [Cal_Start_Pos]

    cal_step = math.floor(math.log10(Cal_Start_Pos)) - 1
    if (cal_step > power_threshold):
        cal_step = power_threshold

    for p in range(int(cal_step), 0, -1):
        Pos_start.append(Cal_Start_Pos + 10**p)
        Pos_start.append(Cal_Start_Pos - 10**p)
    Pos_start.append(Cal_Start_Pos + 30)
    Pos_start.append(Cal_Start_Pos - 30)
    Pos_start.append(Cal_Start_Pos + 50)
    Pos_start.append(Cal_Start_Pos - 50)
    Pos_start.append(Cal_Start_Pos + 200)
    Pos_start.append(Cal_Start_Pos - 200)
    Pos_start.append(Cal_Start_Pos + 500)
    Pos_start.append(Cal_Start_Pos - 500)
    Pos_start.append(Cal_Start_Pos + 750)
    Pos_start.append(Cal_Start_Pos - 750)
    Pos_start.sort()
    print("Pos:", Pos_start)

    LED_start = []

    for L in range(0,len(Pos_start)):
        SharpCap.SelectedCamera.Controls.FindByName("Calibration Start Pos Adjust").Value = int(Pos_start[L])
        time.sleep(wait_time)
        LED_start.append(Mean)

    Y_start = []
    W_start = []

    print("LED start:", LED_start)

    d = 0.0001
    offset_start = min(LED_start) - d
    h_start = max(LED_start) - min(LED_start) + 2*d

    for i in range(0,len(LED_start)):
        Y_start.append(math.log(h_start / (LED_start[i] - offset_start) - 1.0))

    W_start = Search_Weight_L(Y_start)
    print("Weight start:", W_start)
    print("Y_start ", Y_start)

    if (sum(W_start) <= 1.0):
        SharpCap.SelectedCamera.Controls.FindByName("Calibration Start Pos Adjust").Value = int(Cal_Start_Pos)
        k_start = 0.01
        m_start = 0.0

    if (sum(W_start) >= 2.0):
        n = 0
        Sx = 0
        Sx2 = 0
        Vx = []
        for i in range(0,len(Pos_start)):
            n = n + W_start[i]
            xi = Pos_start[i] - Cal_Start_Pos
            Sx = Sx + xi * W_start[i]
            Sx2 = Sx2 + xi * xi * W_start[i]
            Vx.append(xi)

        Det = float(Sx2 * n - Sx * Sx)
        Inv = [[n/Det, -Sx/Det],[-Sx/Det, Sx2/Det]]

        a = 0
        b = 0
        for i in range(0,len(Pos_start)):
            a = a + (Inv[0][0]*Vx[i] + Inv[0][1]) * Y_start[i] * W_start[i]
            b = b + (Inv[1][0]*Vx[i] + Inv[1][1]) * Y_start[i] * W_start[i]

        k_start = -a
        m_start = -b / a
        Cal_Start_Pos = round(Cal_Start_Pos + m_start)
        SharpCap.SelectedCamera.Controls.FindByName("Calibration Start Pos Adjust").Value = int(Cal_Start_Pos)
        Cal_Start_Pos = SharpCap.SelectedCamera.Controls.FindByName("Calibration Start Pos Adjust").Value


# END    LED Calibration Start Position Adjustment
# *****************************************************************************
# LED Calibration End Position Adjustment

    print()
    print("LED Calibration End Position")
    print("***************************")

    Pos_end = [Cal_End_Pos]

    cal_step = math.floor(math.log10(Cal_End_Pos)) - 1
    if (cal_step > power_threshold):
        cal_step = power_threshold

    for p in range(int(cal_step), 0, -1):
        Pos_end.append(Cal_End_Pos + 10**p)
        Pos_end.append(Cal_End_Pos - 10**p)
    Pos_end.append(Cal_End_Pos + 30)
    Pos_end.append(Cal_End_Pos - 30)
    Pos_end.append(Cal_End_Pos + 50)
    Pos_end.append(Cal_End_Pos - 50)
    Pos_end.append(Cal_End_Pos + 200)
    Pos_end.append(Cal_End_Pos - 200)
    Pos_end.append(Cal_End_Pos + 300)
    Pos_end.append(Cal_End_Pos - 300)
    Pos_end.append(Cal_End_Pos + 500)
    Pos_end.append(Cal_End_Pos - 500)
    Pos_end.sort()
    print("End Pos:", Pos_end)
    
    LED_end = []

    for L in range(0,len(Pos_end)):
        SharpCap.SelectedCamera.Controls.FindByName("Calibration End Pos Adjust").Value = int(Pos_end[L])
        time.sleep(wait_time)
        LED_end.append(Mean)

    Y_end = []
    W_end = []

    print("LED end:", LED_end)

    d = 0.0001
    offset_end = min(LED_end) - d
    h_end = max(LED_end) - min(LED_end) + 2*d

    for i in range(0,len(LED_end)):
        Y_end.append(math.log(h_end / (LED_end[i] - offset_end) - 1.0))

    W_end = Search_Weight_R(Y_end)
    print("Weight end:", W_end)

    print("Y_end ", Y_end)

    if (sum(W_end) <= 1.0):
        SharpCap.SelectedCamera.Controls.FindByName("Calibration End Pos Adjust").Value = int(Cal_End_Pos)
        k_end = 0.01
        m_end = 0.0

    if (sum(W_end) >= 2.0):
        n = 0
        Sx = 0
        Sx2 = 0
        Vx = []
        for i in range(0,len(Pos_end)):
            n = n + W_end[i]
            xi = Pos_end[i] - Cal_End_Pos
            Sx = Sx + xi * W_end[i]
            Sx2 = Sx2 + xi * xi * W_end[i]
            Vx.append(xi)

        Det = float(Sx2 * n - Sx * Sx)
        Inv = [[n/Det, -Sx/Det],[-Sx/Det, Sx2/Det]]

        a = 0
        b = 0
        for i in range(0,len(Pos_end)):
            a = a + (Inv[0][0]*Vx[i] + Inv[0][1]) * Y_end[i] * W_end[i]
            b = b + (Inv[1][0]*Vx[i] + Inv[1][1]) * Y_end[i] * W_end[i]

        k_end = a
        m_end = -b / a

        print()
        print("Start: k = %5.6f" % (k_start))
        print("Start: m = %5.2f" % (m_start))
        print("End  : k = %5.6f" % (k_end))
        print("End  : m = %5.2f" % (m_end))
        Cal_End_Pos = round(Cal_End_Pos + m_end)

        SharpCap.SelectedCamera.Controls.FindByName("Calibration End Pos Adjust").Value = int(Cal_End_Pos)

    time.sleep(wait_time)
    temp = SharpCap.SelectedCamera.Controls.FindByName("Calibration Start Pos Adjust").Value
    SharpCap.SelectedCamera.Controls.FindByName("Calibration Start Pos Adjust").Value = temp

# END    LED Calibration End Position Adjustment
# *****************************************************************************

    dumpdata = False
    SharpCap.SelectedCamera.FrameCaptured -= framehandler

    print()
    print("Calibration LED done")

    self.Cal_LED.Text = "Start Calibration LED"
    self.Cal_LED.BackColor = Color.Gainsboro
    self.Cal_LED.Enabled = True
    self.Cal_LED.Enabled = True
    self.button_Exit.Enabled = True
    self.checkbox_showgraphics.Enabled = True

    if (LED_status == "Off"):
        SharpCap.SelectedCamera.Controls.FindByName("GPS Calibration LED").Value = "Off"

    self.ShowOxyGraphic()

    SharpCap.SelectedCamera.Controls.Pan.Value = Pan_start
    SharpCap.SelectedCamera.Controls.Tilt.Value = Tilt_start
    SharpCap.Transforms.SelectionRect = Rect_start

    SharpCap.Transforms.SelectTransform(None)                       # Delete Selection Rectangle

    return()

# *****************************************************************************

class CalibrationLEDMenuForm(Form):
    def __init__(self):
        self.SuspendLayout()
        self.InitializeComponent()
        self.setupCheckButtons()
        #self.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        #self.AutoScaleDimensions = SizeF(6, 13)
        self.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Dpi
        self.AutoScaleDimensions = SizeF(96, 96)
        self.ResumeLayout()

    def InitializeComponent(self):
        self.Text = "LED Calibration"
        self.ClientSize = System.Drawing.Size(500, 40)
        self.MinimumSize = System.Drawing.Size(500, 100)
        self.TopMost = True

        self.plot1 = OxyPlot.WindowsForms.PlotView()
        self.plot1.Location = System.Drawing.Point(10, 50)
        self.plot1.Size = System.Drawing.Size(480, 170)

        self.plot2 = OxyPlot.WindowsForms.PlotView()
        self.plot2.Location = System.Drawing.Point(10, 230)
        self.plot2.Size = System.Drawing.Size(480, 170)

        self.Controls.Add(self.plot1)
        self.Controls.Add(self.plot2)

#        SharpCap.Transforms.SelectTransform("ROI Selection")    # Show Selection Rectangle

    def setupCheckButtons(self):
        self.Cal_LED = Button()
        self.Cal_LED.Text = "Start Calibration LED"
        self.Cal_LED.Location = Point(20, 10)
        self.Cal_LED.Click += self.calib_led
        self.Cal_LED.AutoSize = True

        self.button_Exit = Button()
        self.button_Exit.Text = "Exit"
        self.button_Exit.Location = Point(180, 10)
        self.button_Exit.Click += self.exit
        self.button_Exit.AutoSize = True

        self.checkbox_showgraphics = CheckBox()
        self.checkbox_showgraphics.Text = "Show graphics"
        self.checkbox_showgraphics.Location = Point(300, 5)
        self.checkbox_showgraphics.AutoSize = True
        self.checkbox_showgraphics.Enabled = False
        self.checkbox_showgraphics.Checked = False
        self.checkbox_showgraphics.CheckedChanged += self.CheckBoxChanged

        self.AcceptButton = self.Cal_LED
        self.CancelButton = self.button_Exit
        self.Controls.Add(self.Cal_LED)
        self.Controls.Add(self.button_Exit)
        self.Controls.Add(self.checkbox_showgraphics)

    def ShowOxyGraphic(self):
        self.plotmodel1 = OxyPlot.PlotModel()
        self.plotmodel2 = OxyPlot.PlotModel()

        if (float(SharpCap.AppName.Split("v")[1].Split(",")[0].Split(".")[2]) >= 11757):    # New OxyPlot version with SharpCap 4.1.11757 or after
            legend_start = OxyPlot.Legends.Legend()
            legend_start.LegendTitle = "LED Start"
            legend_start.LegendPosition = OxyPlot.Legends.LegendPosition.TopLeft
            legend_end = OxyPlot.Legends.Legend()
            legend_end.LegendTitle = "LED End"
            legend_end.LegendPosition = OxyPlot.Legends.LegendPosition.TopRight
            self.plotmodel1.Legends.Add(legend_start)
            self.plotmodel2.Legends.Add(legend_end)
        else:                                                                               # Old OxyPlot version with SharpCap 4.1.11711 or before
            self.plotmodel1.LegendTitle  = "LED Start  "
            self.plotmodel1.LegendMargin  = 5
            self.plotmodel1.LegendMaxHeight  = 47
            self.plotmodel1.LegendBorder = OxyPlot.OxyColors.Black
            self.plotmodel1.LegendBackground = OxyPlot.OxyColor.FromAColor(255, OxyPlot.OxyColors.White)
            self.plotmodel1.LegendPosition = OxyPlot.LegendPosition.TopLeft
            self.plotmodel2.LegendTitle  = "LED End  "
            self.plotmodel2.LegendMargin  = 5
            self.plotmodel2.LegendMaxHeight  = 47
            self.plotmodel2.LegendBorder = OxyPlot.OxyColors.Black
            self.plotmodel2.LegendBackground = OxyPlot.OxyColor.FromAColor(255, OxyPlot.OxyColors.White)
            self.plotmodel2.LegendPosition = OxyPlot.LegendPosition.LeftBottom

        self.YAxis1 = OxyPlot.Axes.LinearAxis(Position = OxyPlot.Axes.AxisPosition.Left, Minimum = 0, Maximum = 1.1 * LED_start[-1])
        self.YAxis2 = OxyPlot.Axes.LinearAxis(Position = OxyPlot.Axes.AxisPosition.Left, Minimum = 0, Maximum = 1.1 * LED_end[0])

        self.points_start = []
        for i in range(0,len(Pos_start)):
            self.points_start.Add(OxyPlot.DataPoint(Pos_start[i],LED_start[i]))

        self.points_end = []
        for i in range(0,len(Pos_end)):
            self.points_end.Add(OxyPlot.DataPoint(Pos_end[i],LED_end[i]))

        self.fermi_start = []
        for i in range(-200, 200, 2):
            temp = h_start / (math.exp(-i * k_start) + 1.0) + offset_start
            self.fermi_start.Add(OxyPlot.DataPoint(Cal_Start_Pos + i , temp))

        self.fermi_end = []
        for i in range(-200, 200, 2):
            temp = h_end / (math.exp(i * k_end) + 1.0) + offset_end
            self.fermi_end.Add(OxyPlot.DataPoint(Cal_End_Pos + i , temp))

        self.Graphic_start = []
        self.Graphic_start.Add(OxyPlot.DataPoint(Cal_Start_Pos , 0))
        self.Graphic_start.Add(OxyPlot.DataPoint(Cal_Start_Pos , LED_start[-1]))

        self.Graphic_end = []
        self.Graphic_end.Add(OxyPlot.DataPoint(Cal_End_Pos , 0))
        self.Graphic_end.Add(OxyPlot.DataPoint(Cal_End_Pos , LED_end[0]))

        self.serie_1 = OxyPlot.Series.LineSeries()
        self.serie_1.Color  = OxyPlot.OxyColors.Blue
        self.serie_1.MarkerSize = 4
        self.serie_1.MarkerType = OxyPlot.MarkerType.Circle
        self.serie_1.StrokeThickness = 1
        self.serie_1.ItemsSource = self.points_start
        self.serie_2 = OxyPlot.Series.LineSeries()
        self.serie_2.Color  = OxyPlot.OxyColors.Red
        self.serie_2.MarkerSize = 4
        self.serie_2.MarkerType = OxyPlot.MarkerType.Circle
        self.serie_2.StrokeThickness = 1
        self.serie_2.ItemsSource = self.points_end

        self.serie_3 = OxyPlot.Series.LineSeries()
        self.serie_3.Color  = OxyPlot.OxyColors.Black
        self.serie_3.StrokeThickness = 3
        self.serie_3.LineStyle = OxyPlot.LineStyle.Dash
        self.serie_3.ItemsSource = self.fermi_start
        self.serie_4 = OxyPlot.Series.LineSeries()
        self.serie_4.Color  = OxyPlot.OxyColors.Black
        self.serie_4.StrokeThickness = 3
        self.serie_4.LineStyle = OxyPlot.LineStyle.Dash
        self.serie_4.ItemsSource = self.fermi_end

        self.serie_5 = OxyPlot.Series.LineSeries()
        self.serie_5.Color  = OxyPlot.OxyColors.Green
        self.serie_5.StrokeThickness = 2
        self.serie_5.ItemsSource = self.Graphic_start
        self.serie_6 = OxyPlot.Series.LineSeries()
        self.serie_6.Color  = OxyPlot.OxyColors.Green
        self.serie_6.StrokeThickness = 2
        self.serie_6.ItemsSource = self.Graphic_end

        self.plot1.Model = self.plotmodel1
        self.plot2.Model = self.plotmodel2

        self.plotmodel1.Axes.Add(self.YAxis1)
        self.plotmodel2.Axes.Add(self.YAxis2)
        self.plotmodel1.Series.Add(self.serie_1)
        self.plotmodel2.Series.Add(self.serie_2)
        self.plotmodel1.Series.Add(self.serie_3)
        self.plotmodel2.Series.Add(self.serie_4)
        self.plotmodel1.Series.Add(self.serie_5)
        self.plotmodel2.Series.Add(self.serie_6)

    def CheckBoxChanged(self, sender, args):
        if (self.checkbox_showgraphics.Checked):
            flag_graphics = True
            self.ClientSize = System.Drawing.Size(500, 400)
            self.ShowOxyGraphic()
            self.AutoSize = True
        else:
            flag_graphics = False
            self.ClientSize = System.Drawing.Size(500, 40)
            self.AutoSize = False

    def calib_led(self, sender, event):
        if (SharpCap.SelectedCamera != None):
            th = Thread(ParameterizedThreadStart(LED_Calibration))
            th.SetApartmentState(ApartmentState.STA)
            th.Start(self)
            #self.checkbox_showgraphics.Enabled = True
        else:
            MessageText = "No camera is connected."
            MessageBox.Show(MessageText, "Camera connection error", MessageBoxButtons.OK, MessageBoxIcon.Error)

    def exit(self, sender, event):
        print("Stop LED calibration script")
        self.Close()


form_Cal_LED = CalibrationLEDMenuForm()
form_Cal_LED.StartPosition = FormStartPosition.CenterScreen
form_Cal_LED.TopMost = True
form_Cal_LED.Show()

