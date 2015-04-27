#!/usr/bin/env python

import paho.mqtt.client as mqtt

siteid = 
siteAuthenticationKey = 

import requests
import json

url = 'http://wow.metoffice.gov.uk/automaticreading?'

payload = {'key1': 'value1', 'key2': 'value2'}


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
  client.subscribe("weather/status/#")
  client.subscribe("weather/measurement/#")
  client.subscribe("weather/sunairplus/#")
  
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg) :
  # need to gather all information before sending report
  # http://wow.metoffice.gov.uk/automaticreading?siteid=123456&siteAuthenticationKey=654321&dateutc=2011-02-02+10%3A32%3A55&winddir=230&windspeedmph=12&windgustmph=12& windgustdir=25&humidity=90&dewptf=68.2&tempf=70&rainin=0&dailyrainin=5&baromin=29.1&soiltempf=25&soilmoisture=25&visibility=25&softwaretype=weathersoftware1.0
  
  # create string
  
  print(msg.topic+" "+str(msg.payload))
  
  # POST with form-encoded data
  r = requests.post(url, data=payload)
  
  # All requests will return a status code.
  # A success is indicated by 200.
  # Anything else is a failure.
  # A human readable error message will accompany all errors in JSON format.
  print r.json
  

# Code begines here  
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60) # address of broker, broker port, 

client.loop_forever()
