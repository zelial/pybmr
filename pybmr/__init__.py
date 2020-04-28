# Author: Honza Slesinger
# Tested with:
#    BMR HC64 v2013

from datetime import date

import requests


class Bmr:
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

    def getNumCircuits(self):
        """ Get the number of heating circuits.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/numOfRooms".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": "+"}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return int(response.text)

    def loadCircuit(self, circuit_id):
        """ Get circuit status.

            Raw data returned from server:

              1Pokoj 202 v  021.7+12012.0000.000.0000000000

            Byte offsets of:
              POS_ENABLED = 0
              POS_NAME = 1
              POS_ACTUALTEMP = 14
              POS_REQUIRED = 19
              POS_REQUIREDALL = 22
              POS_USEROFFSET = 27
              POS_MAXOFFSET = 32
              POS_S_TOPI = 36
              POS_S_OKNO = 37
              POS_S_KARTA = 38
              POS_VALIDATE = 39
              POS_LOW = 42
              POS_LETO = 43
              POS_S_CHLADI = 44
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/wholeRoom".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": circuit_id}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))

        match = re.match(
            r"""
                (?P<enabled>.{1})                  # Whether the circuit is enabled
                (?P<name>.{13})                    # Name of the circuit
                (?P<temperature>.{5})              # Current temperature
                (?P<target_temperature_str>.{3})   # Target temperature (string)
                (?P<target_temperature>.{5})       # Target temperature (float)
                (?P<user_offset>.{5})              # Current temperature offset set by user
                (?P<max_offset>.{4})               # Max temperature offset
                (?P<heating>.{1})                  # Whether the circuit is currently heating
                (?P<window_heating>.{1})
                (?P<card>.{1})
                (?P<warning>.{3})                  # Warning code
                (?P<low_mode>.{1})                 # Whether the circuit is assigned to low mode and low mode is active
                (?P<summer_mode>.{1})              # Whether the circuit is assigned to summer mode and summer mode
                                                   # is active
                (?P<cooling>.{1})                  # Whether the circuit is cooling (only water-based circuits)
                """,
            response.text,
            re.VERBOSE,
        )
        if not match:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))
        room_status = match.groupdict()

        # Sometimes some of the values are malformed, i.e. "00\x00\x00\x00" or "-1-1-"
        result = {
            "id": circuit_id,
            "enabled": bool(int(room_status["enabled"])),
            "name": room_status["name"].rstrip(),
            "temperature": None,
            "target_temperature": None,
            "user_offset": None,
            "max_offset": None,
            "heating": bool(int(room_status["heating"])),
            "warning": int(room_status["warning"]),
            "cooling": bool(int(room_status["cooling"])),
            "low_mode": bool(int(room_status["low_mode"])),
            "summer_mode": bool(int(room_status["summer_mode"])),
        }

        try:
            result["temperature"] = float(room_status["temperature"])
        except ValueError:
            pass

        try:
            result["target_temperature"] = float(room_status["target_temperature"])
        except ValueError:
            pass

        try:
            result["user_offset"] = float(room_status["user_offset"])
        except ValueError:
            pass

        try:
            result["max_offset"] = float(room_status["max_offset"])
        except ValueError:
            pass

        return result

    def auth(self):
        payload = {
            "loginName": loginFunction(self.user),
            "passwd": loginFunction(self.password),
        }
        response = requests.post("http://" + self.ip + "/menu.html", data=payload)
        if "res_error_title" in response.content.decode("utf-8"):
            return False
        return True

    def setTargetTemperature(self, temperature, mode_order_number, mode_name):
        self.auth()

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        payloadstr = (
            "modeSettings="
            + str(mode_order_number).zfill(2)
            + mode_name.ljust(13, "+")
            + "00%3A00"
            + str(int(temperature)).zfill(3)
        )
        response = requests.post(
            "http://" + self.ip + "/saveMode", headers=headers, data=payloadstr
        )
        if response.status_code == 200:
            if response.content == "true":
                return True
            else:
                return False

    # Summer
    def loadSummerMode(self):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(
            "http://" + self.ip + "/loadSummerMode", headers=headers, data="param=+"
        )
        if response.status_code == 200:
            content = response.content.decode("ascii")
            if content == "1":
                return False
            if content == "0":
                return True
        return None

    def saveSummerMode(self, mode_bool):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        payload = {"summerMode": "1" if mode_bool == False else "0"}
        response = requests.post(
            "http://" + self.ip + "/saveSummerMode", headers=headers, data=payload
        )
        if response.status_code == 200:
            if response.content[0] == 0:  # fail if authorization fails
                return None

    # val to be  '0' or '1'
    def letoSaveRooms(self, circuits, val):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        # Read current values for all circuits
        response = requests.post(
            "http://" + self.ip + "/letoLoadRooms", headers=headers, data="param=+"
        )
        if not (response.status_code == 200 and response.content[0] in ["0", "1"]):
            pass
        values = response.content.decode("ascii")

        # Set values
        for circuit_id in circuits:
            values = values[:circuit_id] + val + values[circuit_id + 1 :]

        # Write values to BMR
        payload = {"value": values}
        response = requests.post(
            "http://" + self.ip + "/letoSaveRooms", headers=headers, data=payload
        )
        if response.status_code == 200:
            if response.content == "true":
                return True
            else:
                return False

    def include_to_summer(self, circuits):
        self.letoSaveRooms(circuits, "1")

    def exclude_from_summer(self, circuits):
        self.letoSaveRooms(circuits, "0")

    def loadLows(self):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(
            "http://" + self.ip + "/loadLows", headers=headers, data="param=+"
        )
        if response.status_code == 200:
            resp = response.content.decode("ascii")
            if resp[3] == "2":
                return True
            else:
                return False
        return None

    # 015 - low temperature
    # date from
    # date to
    def lowSave(self, mode_bool):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        if mode_bool == True:
            payload = "lowData=0152019-10-1020%3A392025-12-3123%3A59"
        else:
            payload = "lowData=015++++++++++++++++++++++++++++++"
        response = requests.post(
            "http://" + self.ip + "/lowSave", headers=headers, data=payload
        )
        if response.status_code == 200:
            if response.content[0] == 0:  # fail if authorization fails
                return None

    def lowSaveRooms(self, circuits, val):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        # Read current values for all circuits
        response = requests.post(
            "http://" + self.ip + "/lowLoadRooms", headers=headers, data="param=+"
        )
        if not (response.status_code == 200 and response.content[0] in ["0", "1"]):
            pass
        values = response.content.decode("ascii")

        # Set values
        for circuit_id in circuits:
            values = values[:circuit_id] + val + values[circuit_id + 1 :]

        # Write values to BMR
        payload = {"value": values}
        response = requests.post(
            "http://" + self.ip + "/lowSaveRooms", headers=headers, data=payload
        )
        if response.status_code == 200:
            if response.content == "true":
                return True
            else:
                return False

    def include_to_low(self, circuits):
        self.lowSaveRooms(circuits, "1")

    def exclude_from_low(self, circuits):
        self.lowSaveRooms(circuits, "0")

    def get_mode_id(self, circuit_id):
        if circuit_id == None:
            return None

        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        payload = {"roomID": circuit_id}
        response = requests.post(
            "http://" + self.ip + "/roomSettings", headers=headers, data=payload
        )
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
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        payload = {
            "roomSettings": str(circuit_id).zfill(2)
            + "01"
            + str(mode_id).zfill(2)
            + "-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1"
        }
        response = requests.post(
            "http://" + self.ip + "/saveAssignmentModes", headers=headers, data=payload
        )
        if response.status_code == 200:
            if response.content == "true":
                return True
            else:
                return False

    def loadHDO(self):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(
            "http://" + self.ip + "/loadHDO", headers=headers, data="param=+"
        )
        if response.status_code == 200:
            if response.content.decode("ascii") == "1":
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
