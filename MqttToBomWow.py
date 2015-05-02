#!/usr/bin/env python

import paho.mqtt.client as mqtt

import requests
import json

import numericalunits as nu
nu.reset_units()

import datetime

import schedule
import time


# sends a report to the BoM WOW in format

#  Weather Data (from http://wow.metoffice.gov.uk/support/dataformats)

# The following is a list of items of weather data that can be uploaded to WOW.
# Provide each piece of information as a key/value pair, e.g. winddir=225.5 or tempf=32.2.
# Note that values should not be quoted or escaped.
# Key	          Value	                                                             Unit
# winddir	      Instantaneous Wind Direction	                                     Degrees (0-360)
# windspeedmph	Instantaneous Wind Speed                                           Miles per Hour
# windgustdir	  Current Wind Gust Direction (using software specific time period)	 0-360 degrees
# windgustmph	  Current Wind Gust (using software specific time period)            Miles per Hour
# humidity	    Outdoor Humidity                                                   0-100 %
# dewptf	      Outdoor Dewpoint                                                   Fahrenheit
# tempf	        Outdoor Temperature                                                Fahrenheit
# rainin	      Accumulated rainfall in the past 60 minutes                        Inches
# dailyrainin	  Inches of rain so far today                                        Inches
# baromin	      Barometric Pressure (see note)                                     Inches
# soiltempf	    Soil Temperature                                                   Fahrenheit
# soilmoisture	% Moisture                                                         0-100 %
# visibility	  Visibility                                                         Nautical Miles


# http://wow.metoffice.gov.uk/automaticreading?siteid=123456&siteAuthenticationKey=654321&dateutc=2011-02-02+10%3A32%3A55&winddir=230&windspeedmph=12&windgustmph=12& windgustdir=25&humidity=90&dewptf=68.2&tempf=70&rainin=0&dailyrainin=5&baromin=29.1&soiltempf=25&soilmoisture=25&visibility=25&softwaretype=weathersoftware1.0


url = 'http://wow.metoffice.gov.uk/automaticreading?'

msg_arrival_time_local = datetime.datetime.min()          # keep track of the time corresponding to the first data for a new report
msg_arrival_time_utc   = datetime.datetime.min()
sentreportwithtime     = datetime.datetime.now()	# keep track of the time a report was last sent

# define global variables for keeping track of daily data (midnight to midnight)
tempc_daily_max = -100
tempc_daily_min = 100
rainfall_daily = 0
# define global variables for keeping track of day/night data (9am to 9am)
tempc_to9_max = -100
tempc_to9_min = 100
rainfall_to9 = 0
rainmm = 0
dailyrainmm = 0

# not sure it an ordereddict is required

#import collections

#payload = collections.OrderedDict()
#payload['siteid'] = '917806001'
#payload['siteAuthenticationKey'] = '123456'

payload = {'siteid': '917806001', 'siteAuthenticationKey': '123456'}


def zero_data_on_hour() :
	print("data reset on hour")
	global rainmm
	rainmm = 0

def zero_data_at_9() :
	print("data reset at 9:00")
	global rainfall_to9
	rainfall_to9 = 0

def zero_data_at_midnight() :
	print("data reset at midnight")
	global dailyrainmm
	dailyrainmm = 0

schedule.every().hour.do(zero_data_on_hour)
schedule.every().day.at("9:00").do(zero_data_at_9)
schedule.every().day.at("0:00").do(zero_data_at_midnight)


# conversion of degrees Celcius to degrees
def degCtoF(tempc) :
	return( float(tempc) * (9/5.0) + 32 )


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

	print("Connected with result code "+str(rc))

	# Subscribing in on_connect() means that if the connection is lost
	# the subscriptions will be renewed when reconnecting.

	# weather station measurement topics
	client.subscribe("weather/measurement/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

	global msg_arrival_time_local, msg_arrival_time_utc

	msg_arrival_time_local = datetime.datetime.now()	# local time
	msg_arrival_time_utc = datetime.datetime.utcnow()

	global tempc_daily_max, tempc_daily_min, rainfall_local_9am
	global rainmm, dailyrainmm

	print(msg.topic+" "+str(msg.payload))

	report = {}

	# define as global to be able to use for dew point calculation
	tempc = -100
	humidity = -1

  # temperature data
	if msg.topic == "weather/measurement/SHT15_temp" :
  	# in degrees Celcius
   	# convert to degrees Fahrenheit
		tempc = float(msg.payload)
		report['tempf'] = degCtoF(tempc)
		payload.update(report)
		if ( tempc > tempc_daily_max ) :
			tempc_daily_max = tempc
			client.publish("weather/temperature/daily_max", str(tempc_daily_max))
			client.publish("weather/temperature/daily_max_time", str(msg_arrival_time_local))
		if ( tempc < tempc_daily_min ) :
			tempc_daily_min = tempc
			client.publish("weather/temperature/daily_min", str(tempc_daily_min))
			client.publish("weather/temperature/daily_min_time", str(msg_arrival_time_local))
	if msg.topic == "weather/measurement/SHT15_humidity" :
  	# as a percentage
		humidity = float(msg.payload)
		report['humidity'] = str(humidity)
		payload.update(report)
	# calculate dewpoint based on temperature and humidity
	if ( tempc > -100 and humidity > -1 ) :
		dewptc = 0
		report['dewptf']  = degCtoF(dewptc)
		client.publish("weather/dewpoint/dewpoint", dewptc)
	# weather station will not report measurements from pressure sensor
	# if error code generated when sensor is initialised, or
	# if error code generated when taking reading
	if msg.topic == "weather/measurement/BMP085_pressure" :
  	# in mbar
  	# convert to inches
  	# 1 millibar (or hectopascal/hPa), is equivalent to 0.02953 inches of mercury (Hg).
  	# source: http://weatherfaqs.org.uk/node/72
		report['baromin'] = float(msg.payload) * 0.02953
		payload.update(report)
	# weather station will not report measurements from the weather sensors
	# (wind and rain) if error code generated by wind direction reading
	if msg.topic == "weather/measurement/wind_dir" :
  	# in degrees
		report['winddir'] = msg.payload
		payload.update(report)
	if msg.topic == "weather/measurement/wind_spd" :
  	# in knots
  	# convert to miles per hour
		report['windspeedmph'] = float(msg.payload) * 1.15078
		payload.update(report)
	if msg.topic == "weather/measurement/rain" :
  	# in millimetres
  	# convert to inches
  	# resets automatically on hour
		rainmm += float(msg.payload)
		report['rainin'] = (rainmm*nu.mm)/nu.inch
		payload.update(report)
		# need to zero at midnight (occurs in main loop - value here will have already been reset)
		dailyrainmm += float(msg.payload)
		report['dailyrainin'] = (dailyrainmm*nu.mm)/nu.inch
		payload.update(report)
		client.publish("weather/rainfall/sincemidnight", str(dailyrainmm))
		client.publish("weather/rainfall/since9am", str(dailyrainmm))




# Processing begins here ...

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client_ip = "192.168.1.55"
#client_ip = "localhost"
client.connect(client_ip, 1883, 60) # address of broker, broker port,

client.loop_start()

# Loop continuously
while True :

	try :

		schedule.run_pending()

		# reset daily measurements if midnight local time
#		if ( datetime.datetime.now() ) :
#			reset_daily_measuremets()
		# reset day/night measurements if 9am local time
		#today9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
		# reset hourly measurements (rain)

		# get current time and if greater than wait send a report
		reportWait = 2      # time (seconds) to wait to ensure all measurements have been received
		reportInterval = 15	# interval (minutes) at which a new report is sent to BoM WOW

		assert reportInterval > 5, "reportInterval must be greater than interval between measurements: %r" % 5

#		if ( ( datetime.datetime.now() - reporttime ) > datetime.timedelta(seconds=reportWait) ) and ( ( reporttime - sentreportwithtime ) > datetime.timedelta(minutes=reportInterval) ) :
#		if ( reporttime - sentreportwithtime ) > datetime.timedelta(minutes=reportInterval) :

		# ensure the report data is more up-to-date than previously sent message
		# should prevent repots being sent if sensor is off
		if ( msg_arrival_time_local > sentreportwithtime ) :

			# only send reports every 'reportInterval' minutes
			if ( datetime.datetime.now() - sentreportwithtime ) > datetime.timedelta(minutes=reportInterval) :

				# add time to report
				# The date must be in the following format: YYYY-mm-DD HH:mm:ss,
				# where ':' is encoded as %3A, and the space is encoded as either '+' or %20.
				# An example, valid date would be: 2011-02-29+10%3A32%3A55, for the 2nd of Feb, 2011 at 10:32:55.
				# Note that the time is in 24 hour format.
				# Also note that the date must be adjusted to UTC time - equivalent to the GMT time zone.
				format = "%Y-%m-%d+%H:%M:%S"
				datestr = msg_arrival_time_utc.strftime(format)
				datestr = datestr.replace(':', '%3A')
				payload['dateutc'] = datestr

				# send report
				print("payload to be sent: {0}".format(payload))

				# POST with form-encoded data1
			#  r = requests.post(url, data=payload)

				# All requests will return a status code.
				# A success is indicated by 200.
				# Anything else is a failure.
				# A human readable error message will accompany all errors in JSON format.
			#  print("POST request status code: {0}".format(r.json))

				# reset flags
	#			newreport = True
				sentreportwithtime = msg_arrival_time_local

	except KeyboardInterrupt :      #Triggered by pressing Ctrl+C

		running = False       #Stop thread1

		# Disconnect mqtt client
		client.loop_stop()
		client.disconnect()

		print("Bye")
		break         #Exit

