#!/usr/bin/env python

import paho.mqtt.client as mqtt

import requests
import json

import numericalunits as nu
nu.reset_units()

from decimal import *
getcontext().prec = 1  # Set precision of Decimal numbers to 1

url = 'http://wow.metoffice.gov.uk/automaticreading?'

payload = {'siteid': '917806001',
           'siteAuthenticationKey': '123456'
           }


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :

  print("Connected with result code "+str(rc))

  # Subscribing in on_connect() means that if the connection is lost
  # the subscriptions will be renewed when reconnecting.

  # system topics
  #client.subscribe("$SYS/#")

  # general topics
  client.subscribe("all/contoller/dst")

  # weather station topics
  #client.subscribe("weather/status/#")
  client.subscribe("weather/measurement/#")
  #client.subscribe("weather/sunairplus/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :

	print(msg.topic+" "+str(msg.payload))

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

  # need to gather all information before sending report
  # http://wow.metoffice.gov.uk/automaticreading?siteid=123456&siteAuthenticationKey=654321&dateutc=2011-02-02+10%3A32%3A55&winddir=230&windspeedmph=12&windgustmph=12& windgustdir=25&humidity=90&dewptf=68.2&tempf=70&rainin=0&dailyrainin=5&baromin=29.1&soiltempf=25&soilmoisture=25&visibility=25&softwaretype=weathersoftware1.0

	report = {}

  # temperature data
	if msg.topic is "weather/measurement/SHT15_temp" :
  	# in degrees Celcius
   	# convert to degrees Fahrenheit
   		getcontext().prec = 3
		report['tempf'] = Decimal( Decimal(msg.payload) * Decimal(9/5.0) + Decimal(32) )
	if ( msg.topic is "weather/measurement/SHT15_humidity" ) :
  	# as a per centage
		report['humidity'] = msg.payload
	if ( msg.topic is "weather/measurement/BMP085_pressure" ) :
  	# in milliPascals
  	# convert to inches
		report['baromin'] = msg.payload
	if ( msg.topic is "weather/measurement/wind_spd" ) :
  	# in metres per second
  	# convert to miles per hour
		report['windspeedmph'] = msg.payload
	if ( msg.topic is "weather/measurement/wind_dir" ) :
  	# in degrees
		report['winddir'] = msg.payload
	if ( msg.topic is "weather/measurement/rain" ) :
  	# in millimetres
  	# convert to inches
  	# need to zero at midnight
		report['dailyrainin'] = msg.payload

	print("report: {0}".format(report))

	# add report to payload
	payload.update(report)

	print("payload to be sent: {0}".format(payload))

  # POST with form-encoded data
#  r = requests.post(url, data=payload)

  # All requests will return a status code.
  # A success is indicated by 200.
  # Anything else is a failure.
  # A human readable error message will accompany all errors in JSON format.
#  print("POST request status code: {0}".format(r.json))



# Processing begins here ...

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

#client_ip = "192.168.1.55"
client_ip = "localhost"
client.connect(client_ip, 1883, 60) # address of broker, broker port,

client.loop_forever()
