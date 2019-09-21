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

    def getStatus(self):
        #if self.auth() == False:
        #    return ""  # TODO proper return code
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = requests.post('http://'+self.ip+'/numOfRooms', headers=headers, data='param=+')
        if(response.status_code == 200):
            if response.content[0] == 0: # Not authorized, because  of a new day. Authorize and try again
                self.auth()
                response = requests.post('http://'+self.ip+'/numOfRooms', headers=headers, data='param=+')

            cnt = int(response.content) # read number of sensors
            if cnt == 0:
                return [] # TODO failed response

            rooms = []
            for id in range(0, cnt-1):
                room = self.getRoom(id)
                rooms.append(room)
            return rooms

        return [] # TODO proper return object


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
    def getRoom(self, id):
        room = {}
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        payload = {'param': id}
        response = requests.post('http://'+self.ip+'/wholeRoom', headers=headers, data=payload)
        r = response.content
        if(response.status_code == 200):
            room['name'] = r[1:14].strip().decode("utf-8")
            room['id'] = id
            room['enabled'] = 'on' if int(r[0:1]) == 1 else 'off'
            room['heating'] = 'on' if int(r[36:37]) == 1 else 'off'
            room['cooling'] = 'on' if int(r[44:45]) == 1 else 'off'
            room['summer'] = 'on' if int(r[43:44]) == 1 else 'off'
            room['required_temp'] = float(r[22:27])
            room['current_temp'] = float(r[14:19])
            room['warning'] = 'on' if int(r[39:42]) == 1 else 'off'
        return room

    def auth(self):
        payload = {'loginName': loginFunction(self.user), 'passwd': loginFunction(self.password)}
        response = requests.post('http://'+self.ip+'/menu.html', data=payload)
        if("res_error_title" in response.content.decode("utf-8") ):
            return False
        return True




def loginFunction(input):
    output = ""
    day = date.today().day
    for c in input:
        tmp = ord(c) ^ (day << 2)
        output = output + hex(tmp)[2:].zfill(2)
    return output.upper()


