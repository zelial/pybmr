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
            room['cooling'] = int(r[42:43]) == 1
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

    def setTargetTemperature(self, temperature, mode_order_number, mode_name):
        self.auth()

        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        payloadstr = 'modeSettings=' + str(mode_order_number).zfill(2) + mode_name.ljust(13, '+') + '00%3A00' + str(int(temperature)).zfill(3)
        response = requests.post('http://'+self.ip+'/saveMode', headers=headers, data=payloadstr)
        if(response.status_code == 200):
            if response.content == 'true':
                return True
            else:
                return False



    # Summer
    def loadSummerMode(self):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = requests.post('http://'+self.ip+'/loadSummerMode', headers=headers, data='param=+')
        if(response.status_code == 200):
            content = response.content.decode('ascii')
            if content == '1':
                return False
            if content == '0':
                return True
        return None

    def saveSummerMode(self, mode_bool):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        payload = {'summerMode': '1' if mode_bool == False else '0'}
        response = requests.post('http://'+self.ip+'/saveSummerMode', headers=headers, data=payload)
        if(response.status_code == 200):
            if response.content[0] == 0: # fail if authorization fails
                return None

    # val to be  '0' or '1'
    def letoSaveRooms(self, circuits, val):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        # Read current values for all circuits
        response = requests.post('http://'+self.ip+'/letoLoadRooms', headers=headers, data='param=+')
        if not (response.status_code == 200 and response.content[0] in ['0','1']):
                pass
        values = response.content.decode("ascii") 

        # Set values
        for circuit_id in circuits:
            values = values[:circuit_id] + val + values[circuit_id + 1:]

        # Write values to BMR
        payload = {'value': values}
        response = requests.post('http://'+self.ip+'/letoSaveRooms', headers=headers, data=payload)
        if(response.status_code == 200):
            if response.content == 'true':
                return True
            else:
                return False

    def include_to_summer(self, circuits):
        self.letoSaveRooms(circuits, '1')

    def exclude_from_summer(self, circuits):
        self.letoSaveRooms(circuits, '0')


    def loadLows(self):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = requests.post('http://'+self.ip+'/loadLows', headers=headers, data='param=+')
        if(response.status_code == 200):
            resp  = response.content.decode('ascii')
            if resp[3] == '2':
                return True
            else:
                return False
        return None

    # 015 - low temperature
    # date from
    # date to
    def lowSave(self, mode_bool):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        if mode_bool == True:
            payload = 'lowData=0152019-10-1020%3A392025-12-3123%3A59'
        else:
            payload = 'lowData=015++++++++++++++++++++++++++++++'
        response = requests.post('http://'+self.ip+'/lowSave', headers=headers, data=payload)
        if(response.status_code == 200):
            if response.content[0] == 0: # fail if authorization fails
                return None

    def lowSaveRooms(self, circuits, val):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        # Read current values for all circuits
        response = requests.post('http://'+self.ip+'/lowLoadRooms', headers=headers, data='param=+')
        if not (response.status_code == 200 and response.content[0] in ['0','1']):
                pass
        values = response.content.decode("ascii")

        # Set values
        for circuit_id in circuits:
            values = values[:circuit_id] + val + values[circuit_id + 1:]

        # Write values to BMR
        payload = {'value': values}
        response = requests.post('http://'+self.ip+'/lowSaveRooms', headers=headers, data=payload)
        if(response.status_code == 200):
            if response.content == 'true':
                return True
            else:
                return False

    def include_to_low(self, circuits):
        self.lowSaveRooms(circuits, '1')


    def exclude_from_low(self, circuits):
        self.lowSaveRooms(circuits, '0')


    def get_mode_id(self, circuit_id):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        payload = {'roomID': circuit_id}
        response = requests.post('http://'+self.ip+'/roomSettings', headers=headers, data=payload)
        if response.status_code == 200:
            try:
                return int(response.content[2:4]) - 32
            except ValueError:
                return None

    # 230110-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
    # 230109-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
    # 23011013-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
    def set_mode_id(self, circuit_id, mode_id):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

        payload = {'roomSettings': str(circuit_id).zfill(2) + '01' + str(mode_id).zfill(2) + '-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1'}
        response = requests.post('http://'+self.ip+'/saveAssignmentModes', headers=headers, data=payload)
        if response.status_code == 200:
            if response.content == 'true':
                return True
            else:
                return False

    def loadHDO(self):
        self.auth()
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        response = requests.post('http://'+self.ip+'/loadHDO', headers=headers, data='param=+')
        if(response.status_code == 200):
            if response.content.decode('ascii') == '1':
                return True
            else:
                return False


def loginFunction(input):
    output = ""
    day = date.today().day
    for c in input:
        tmp = ord(c) ^ (day << 2)
        output = output + hex(tmp)[2:].zfill(2)
    return output.upper()


