HEAT_SET_BMS SOFTWARE SET UP USER GUIDE
There is a separate userguide for the PCB set up


STEP 1: Set up the SPI and VNC on the pi

	The temperature sensors and pressure sensor provide analogue data that is processed by an analogue to
	digital chip (MCP3008). Part of the wiring to the MCP3008 from the pi requires that the GPIO pins that 
	have SPI functionality are enabled.

	It is assumed that the user will want to interface with the pi remotely (e.g. through mobile phone and/or
	laptop). As such we need to enable VNC.

	In the Raspian desktop select:
	
	Preferences > Raspberry Pi Configuration > Interfaces

	And enable both SPI and VNC. Note if you are not using the Raspian operating system then you may have
	difficulties. I started on the Ubuntu OS for the pi but could not get it to work. On Raspian it takes
	seconds.

STEP 2: Download the code to a folder titled "Home_BMS" and move the folder to the Documents directory:

	/home/pi/Documents

	This is not essential, but just be aware that the code in A_Initialise.py contains the string variable "fileLoc" that is used in 
	various parts of the code and this presumes the folder location is:

	/home/pi/Documents/Home_BMS

	As such if you want to change either the folder location or the name of the folder that contains all of the
	scripts you will need to update the string variable "fileLoc"
	
STEP 3: Mount a USB flashdrive for data logging:

	It is my understanding that the microflash drives used by the Pi are susceptible to corruption if you have continuous
	or high frequency data being stored. As such it is probably better to use a flash drive to store the energy and
	associated data gathered by this home building monitoring system.
	
	To correctly mount a USB you should follow the instructions provided in the link below:
	
	https://www.raspberrypi-spy.co.uk/2014/05/how-to-mount-a-usb-flash-disk-on-the-raspberry-pi/
	
	Note that you need to set up the automount section of the instructions so that it will mount correctly each time the system restarts. If you do
	not know your user id (UID) or group id (GID) type "id" in the command line and you can use the numeric value instead of the written ID when
	mounting (e.g. 1000:1000 vs. pi:pi)
	
	When you have created the drive you need to update variable "dbLoc" in A_Initialise.py to the destination directory that you 
	have created. The default is: '/media/HeatSet_data/'.

STEP 4: Skip the password on boot
	
	We want the home energy monitoring system to run as soon as all other system processes have been carried out. As such we
	don't want to have a password prompt or else we may find we don't have a keyboard. To avoid this open
	the terminal and enter:

	$ sudo raspi-config

	Select Option 3: Boot Options. Then select B1: Desktop / CLI. Then select B4: Desktop Autologin. NOTE: It is
	important that the Desktop and not the Console option is selected. This is because the main python script
	uses TKinter which requires a graphical environment (i.e. desktop). Exit and reboot on prompt.

STEP 5: Create file to autostart the programme on boot

	This section needs care - I screwed up my pi and it took a bit of an effort to recover it when I got this
	wrong. The purpose is to create a command that will launch the BMS software when you turn on the
	pi.

	Open the terminal and enter the following commands:

	$ mkdir /home/pi/.config/autostart
	$ nano /home/pi/.config/autostart/HeatSet_BMS.desktop

	On entering the second comand you will have opened your new .desktop file ready to edit it. Make the following
	entries:
	
	[Desktop Entry]
	Type=Application
	Name=HeatSet_BMS_Run
	Exec=/usr/bin/python3 /home/pi/Documents/Home_BMS/B_GUI.py

	(n.b. if you have used a different directory to store this building monitoring system then amend the directory as
	required in "Exec=..." above.)
	
	Then press CTR X and then Y to save the file. What this is doing is creating a system command that will
	auto-launch on start but importantly after all of pi's other system start up routines have been run.

STEP 6: OBEMS Pulse Server.

	This BMS has been developed in collaboration with T4 Sustainability (http://www.t4sustainability.co.uk/) who have 
	separately developed their own pulse metering server in C++. The Python code creates the graphical user interface, 
	takes temperature and pressure sensor readings and records data to an SQLite3 database. However, Python is not as
	good a language as C++ for managing more system based events. I was concerned that pulse meter readings from 
	electricity meters, hot water meters and heat meters might be missed by the Python code. The C++ module (ObemsPulseServer)
	is always "on" and the Python code simply interacts with the server every 10 seconds to see how many pulses there have been.
	
	In order for the ObemsPulseServer to be launched correctly it is necessary to change the permissions of the file the 
	first time you use this BMS system. Using the terminal, navigate to the directory and change the permission with the 
	following commands which will make the file 'ObemsPulseServer' executible:
	
	$ cd /home/pi/Documents/Home_BMS/
	$ chmod 777 ObemsPulseServer
	
STEP 7:	Python libraries
	
	Some libraries used in the code may not be present. Below are the list of commands you need to run in the terminal
	to ensure necessary libraries are present:
	
	$ sudo apt-get install python3-pil.imagetk


SETP 8: Set up a daily reboot

	I feel that the code starts to slow down after several weeks of use. As such I have introduced a daily reboot of the system to 
	flush out any issues. To set this up enter the following into the consol
	$ sudo -i
	$ crontab -e
	In the crontab file navigate down to a free line and enter:
	
	0 0 * * * reboot
	
	This will reboot the machine at midnight each night.
	
	Press CTR X
	Press Y and ENTER
	
	exit the terminal

STEP 9: Set resolution
	
	I've had some problems with the VNC server not being able to display the desktop. I think this is a result of not fixing the screen resolution.
	When you use multiple devices it causes the desktop environment issues as to which resoultion to settle on, or something along those lines.
	To manage this do the following:
	A. 	Open the terminal
	B. 	enter: sudo raspi-config
	C.	Display options -> Resolution. Then select a resolution mode, one website suggested selecting 1280x720. Save and finish.
	
STEP 10: Finish

	Reboot the pi (see step 4) and the BMS software should now be running - happy home energy monitoring!


