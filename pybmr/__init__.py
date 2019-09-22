# Author: Honza Slesinger
# Tested with:
#    BMR HC64 v2013

import requests
from datetime import date

class Bmr:
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

    def getNumCircuits(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = requests.post('http://'+self.ip+'/numOfRooms', headers=headers, data='param=+')
        if(response.status_code == 200):
            if response.content[0] == 0: # Not authorized, because  of a new day. Authorize and try again
                self.auth()
                response = requests.post('http://'+self.ip+'/numOfRooms', headers=headers, data='param=+')

            cnt = int(response.content) # read number of sensors
            return cnt
        else:
            return None


    '''1Pokoj 202 v  021.7+12012.0000.000.0000000000
        , POS_ACTUALTEMP = 14
        , POS_REQUIRED = 19
        , POS_REQUIREDALL = 22
        , POS_USEROFFSET = 27
        , POS_MAXOFFSET = 32
        , POS_S_TOPI = 36
        , POS_S_OKNO = 37
        , POS_S_KARTA = 38
        , POS_VALIDATE = 39
        , POS_LOW = 42
        , POS_LETO = 43
        , POS_S_CHLADI = 44
    '''
    def getStatus(self, id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        payload = {'param': id}
        response = requests.post('http://'+self.ip+'/wholeRoom', headers=headers, data=payload)
        if(response.status_code == 200):
            if response.content[0] == 0: # Not authorized, because  of a new day. Authorize and try again
                self.auth()
                response = requests.post('http://'+self.ip+'/wholeRoom', headers=headers, data=payload)
            if response.content[0] == 0: # fail if authorization fails
                return None

            r = response.content
            room = {}
            room['name'] = r[1:14].strip().decode("utf-8")
            room['id'] = id
            room['enabled'] = int(r[0:1]) == 1
            room['heating'] = int(r[36:37]) == 1
            room['cooling'] = int(r[44:45]) == 1
            room['summer'] =  int(r[43:44]) == 1
            room['required_temp'] = float(r[22:27])
            room['current_temp'] = float(r[14:19])
            room['warning'] = int(r[39:42])
            return room
        else:
            return None

    def auth(self):
        payload = {'loginName': loginFunction(self.user), 'passwd': loginFunction(self.password)}
        response = requests.post('http://'+self.ip+'/menu.html', data=payload)
        if("res_error_title" in response.content.decode("utf-8") ):
            return False
        return True


    def setTargetTemperature(self, temperature, circuit_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        payload = {'manualTemp': str(circuit_id).zfill(2) + '0000'}
        response = requests.post('http://'+self.ip+'/saveManualTemp', headers=headers, data=payload)
        if(response.status_code == 200):
            if response.content == 'true':
                return True
            else
                return False


def loginFunction(input):
    output = ""
    day = date.today().day
    for c in input:
        tmp = ord(c) ^ (day << 2)
        output = output + hex(tmp)[2:].zfill(2)
    return output.upper()


