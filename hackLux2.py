# -*- coding: utf-8 -*-
import serial
import time
import datetime
import os
import requests
import logging
import pdb

#oauth access to the new dataset
url = "https://iotmmsa2618100a.hana.ondemand.com/com.sap.iotservices.mms/v1/api/http/data/fb6e9682-d60b-492a-8a09-aadbea847117"
headers = {
        'Authorization': "Bearer f55197ba5cfd788f4454ab8c95ca64c",
        'Cache-Control': "no-cache",
        }

#get timestamp
ts = time.time()
timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

#init button
buttonStatus = "stop"

#converting hexa data in readable data         
def hexShow(argv):  
        result = ''  
        hLen = len(argv)  
        for i in xrange(hLen):  
                hvol = ord(argv[i])  
                hhex = '%02x'%hvol  
                result += hhex+' '  
        #print 'hexShow:',result  

t = serial.Serial('/dev/ttyUSB1',9600)

def get_present_gps():
                ser=serial.Serial('/dev/ttyUSB0',9600)          #open serial communication
                
                f=open('/home/pi/Desktop/gps','w')
                data=ser.read(512) #read 1024 bytes

                f.write(data)                                   #write data into file
                f.flush()                                       #flush from buffer into os buffer
                                                                #ensure to write from os buffers(internal) into disk
                f=open('/home/pi/Desktop/gps','r')             #fetch the required file


                for line in f.read().split('\n'):        #GPS parsing
                        if line.startswith('$GPGGA'):
                                lat, _, lon= line.split(',')[2:5]
                                try:
                                                lat_aux= str(lat)
                                                lat_dd=float(lat_aux[:2])
                                                lat_mm=float(lat_aux[2:])/60
                                                lat = str(lat_dd + lat_mm)                                                
                                                print lat                                               

                                                lon_aux= str(lon)
                                                lon_dd=float(lon_aux[:3])
                                                lon_mm=float(lon_aux[3:])/60
                                                lon = str(lon_dd + lon_mm)
                                                print lon
                                                                
                                                a=[lat,lon]
                                                #print lat, lon
                                                
                                                return a
                                except:
                                                pass

while True:
        time.sleep(5)
        #get request
        response = requests.request("GET", url, headers=headers).json()
        print "first get"
        print response
        if response != []:        
                data = response[0]["messages"]

                buttonStatus = data[0]["trigger"]
                tripId = data[0]["tripid"]


        #post request
        while (buttonStatus == "start"):                
                print "start collecting data"

                response = requests.request("GET", url, headers=headers).json()
                print "second get and changing start into stop ?"
                print response
                
                if response != []:
                        data = response[0]["messages"]
                        buttonStatus = data[0]["trigger"]
                        tripId = data[0]["tripid"] + 1

                t.flushInput()  
                position = get_present_gps()    
                retstr = t.read(10)
        
                hexShow(retstr)
                #print hexShow(retstr)
        
                if len(retstr)==10:
                        if(retstr[0]==b"\xaa" and retstr[1]==b'\xc0'):
                                checksum=0
                                #pdb.setTrace()
                                for i in range(6):
                                    checksum=checksum+ord(retstr[2+i])
                                if checksum%256 == ord(retstr[8]):
                                    pm25_aux=ord(retstr[2])+ord(retstr[3])*256
                                    pm25=str(pm25_aux/10.0)
                                    pm10_aux=ord(retstr[4])+ord(retstr[5])*256
                                    pm10=str(pm10_aux/10.0)
                                    #print pm25 , pm10

                #post request
                headers = {
                'Content-Type':"application/json",
                'Authorization': "Bearer f55197ba5cfd788f4454ab8c95ca64c",
                'Cache-Control': "no-cache",
                }
        
                payload = "{\"mode\":\"sync\",\"messageType\":\"d225176ae8fb5d12880e\",\"messages\":[{\"timestamp\":"+ str(int(ts)) +", \"tripid\":"+str(tripId)+",\"pm2\":\""+pm25+"\", \"pm10\":\""+pm10+"\", \"lat\": \""+ str(position[0]) +"\" , \"long\":\""+str(position[1])+"\"}]}"
                logging.info(payload)
                response_post = requests.request("POST", url, data=payload, headers=headers)

                print(response_post.text)

        print "stop collecting data"
                

