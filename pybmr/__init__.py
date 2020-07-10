# Author: Honza Slesinger
# Tested with:
#    BMR HC64 v2013

from datetime import datetime, date
from functools import wraps
from hashlib import sha256
import re

from cachetools.func import ttl_cache, lru_cache

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests_toolbelt import sessions


HTTP_DEFAULT_TIMEOUT = 10  # seconds
HTTP_DEFAULT_MAX_RETRIES = 10
CACHE_DEFAULT_MAXSIZE = 128
CACHE_DEFAULT_TTL = 10


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = HTTP_DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def authenticated(func):
    """ Decorator for ensuring we are logged-in before calling any BMR API
        endpoints.
    """

    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if not self._authenticate():
            raise Exception("Authentication failed, check username/password")
        return func(self, *args, **kwargs)

    return wrapped


class Bmr:
    def __init__(
        self,
        base_url,
        user,
        password,
        timeout=HTTP_DEFAULT_TIMEOUT,
        max_retries=HTTP_DEFAULT_MAX_RETRIES,
        cache_maxsize=CACHE_DEFAULT_MAXSIZE,
        cache_ttl=CACHE_DEFAULT_TTL,
    ):
        self._user = user
        self._password = password

        self._http = sessions.BaseUrlSession(base_url=base_url)
        self._cache_maxsize = cache_maxsize
        self._cache_ttl = cache_ttl

        # Retry strategy for http requests
        retries = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=1,  # this will do `sleep({backoff factor} * (2 ** ({number of retries} - 1)))`
        )

        # Include timeout for http requests
        adapter = TimeoutHTTPAdapter(timeout=timeout, max_retries=retries)

        self._http.mount("https://", adapter)
        self._http.mount("http://", adapter)

    def _authenticate(self):
        """ Login to BMR controller. Note that BMR controller is using a kinda
            weird and insecure authentication mechanism - it looks like it's
            just remembering the username and IP address of the logged-in user.
        """

        def bmr_hash(value):
            output = ""
            day = date.today().day
            for c in value:
                tmp = ord(c) ^ (day << 2)
                output = output + hex(tmp)[2:].zfill(2)
            return output.upper()

        data = {"loginName": bmr_hash(self._user), "passwd": bmr_hash(self._password)}
        response = self._http.post("/menu.html", data=data)
        if "res_error_title" in response.text:
            return False
        return True

    @lru_cache(maxsize=1)
    @authenticated
    def getUniqueId(self):
        """ Return unique ID of the entity.

            The BMR HC64 API doesn't provide anything that could be used as a
            unique ID, such as serial number. Therefore we have to generate it
            from something that doesn't usually change - such as circuit names.

            Note that this is more like a unique ID for the whole HC64
            controller, not a unique ID of a circuit.
        """
        return sha256(b"\0".join([name.encode("utf-8") for name in self.getCircuitNames()])).hexdigest()[:8]

    @lru_cache(maxsize=1)
    @authenticated
    def getNumCircuits(self):
        """ Get the number of heating circuits.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": "+"}
        response = self._http.post("/numOfRooms", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return int(response.text)

    @lru_cache(maxsize=1)
    @authenticated
    def getCircuitNames(self):
        """ Get the names of all heating circuits.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": "+"}
        response = self._http.post("/listOfRooms", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        # Example: F01 Byt      F02 Pokoj    F03 Loznice  F04 Koupelna F05 Det pokojF06 Chodba   F07 Kuchyne  F08 Obyvak   R01 Byt      R02 Pokoj    R03 Loznice  R04 Koupelna R05 Det pokojR06 Chodba   R07 Kuchyne  R08 Obyvak  # noqa
        return [response.text[i : i + 13].strip() for i in range(0, len(response.text), 13)]

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getCircuit(self, circuit_id):
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
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": circuit_id}
        response = self._http.post("/wholeRoom", headers=headers, data=data)
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

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getSchedules(self):
        """Load schedules.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": "+"}
        response = self._http.post("/listOfModes", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return [x.rstrip() for x in re.findall(r".{13}", response.text)]

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getSchedule(self, schedule_id):
        """ Load schedule settings.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"modeID": "{:02d}".format(schedule_id)}
        response = self._http.post("/loadMode", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))

        # Example: 1 Byt        00:0002106:0002112:0002121:00021
        match = re.match(
            r"""
                (?P<name>.{13})                          # schedule name
                (?P<timetable>(\d{2}:\d{2}\d{3}){1,8})?  # time and target temperature
            """,
            response.text,
            re.VERBOSE,
        )
        if not match:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))
        schedule = match.groupdict()
        timetable = None
        if schedule["timetable"]:
            timetable = [
                {"time": x[0], "temperature": int(x[1])}
                for x in re.findall(r"(\d{2}:\d{2})(\d{3})", schedule["timetable"])
            ]

        return {"id": schedule_id, "name": schedule["name"].rstrip(), "timetable": timetable}

    @authenticated
    def setSchedule(self, schedule_id, name, timetable):
        """ Save schedule settings. Name is the new schedule name. Timetable is
            a list of tuples of time and target temperature. When the schedule is
            associated with a circuit BMR heating controller will use the
            schedule timetable to set the target temperature at the specified
            time. Note that the first entry in the timetable must be always for
            time "00:00".
        """
        if timetable[0]["time"] != "00:00":
            raise Exception("First timetable entry must be for time 00:00")

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        data = {
            "modeSettings": "{:02d}{:13.13}{}".format(
                schedule_id,
                name[:13],
                "".join(["{}{:03d}".format(item["time"], int(item["temperature"])) for item in timetable]),
            )
        }
        response = self._http.post("/saveMode", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    @authenticated
    def deleteSchedule(self, schedule_id):
        """ Delete schedule.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        data = {"modeID": "{:02d}".format(schedule_id)}
        response = self._http.post("/deleteMode", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getSummerMode(self):
        """ Return True if summer mode is currently activated.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = self._http.post("/loadSummerMode", headers=headers, data="param=+")
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return response.text == "0"

    @authenticated
    def setSummerMode(self, value):
        """ Enable or disable summer mode.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"summerMode": "0" if value else "1"}
        response = self._http.post("/saveSummerMode", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getSummerModeAssignments(self):
        """ Load circuit summer mode assignments, i.e. which circuits will be
            affected by summer mode when it is turned on.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = self._http.post("/letoLoadRooms", headers=headers, data={"param": "+"})
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        try:
            return [bool(int(x)) for x in list(response.text)]
        except ValueError:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))

    @authenticated
    def setSummerModeAssignments(self, circuits, value):
        """ Assign or remove specified circuits to/from summer mode. Leave
            other circuits as they are.
        """
        assignments = self.getSummerModeAssignments()

        for circuit_id in circuits:
            assignments[circuit_id] = value

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"value": "".join([str(int(x)) for x in assignments])}
        response = self._http.post("/letoSaveRooms", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getLowMode(self):
        """ Get status of the LOW mode.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = self._http.post("/loadLows", headers=headers, data={"param": "+"})
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        # The response is formatted as "<temperature><start_datetime><end_datetime>", let's parse it
        match = re.match(
            r"""
            (?P<temperature>\d{3})
            (?P<start_datetime>\d{4}-\d{2}-\d{2}\d{2}:\d{2})?
            (?P<end_datetime>\d{4}-\d{2}-\d{2}\d{2}:\d{2})?
            """,
            response.text,
            re.VERBOSE,
        )
        if not match:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))
        low_mode = match.groupdict()
        result = {"enabled": low_mode["start_datetime"] is not None, "temperature": int(low_mode["temperature"])}
        if low_mode["start_datetime"]:
            result["start_date"] = datetime.strptime(low_mode["start_datetime"], "%Y-%m-%d%H:%M")
        if low_mode["end_datetime"]:
            result["end_date"] = datetime.strptime(low_mode["end_datetime"], "%Y-%m-%d%H:%M")
        return result

    @authenticated
    def setLowMode(self, enabled, temperature=None, start_datetime=None, end_datetime=None):
        """ Enable or disable LOW mode. Temperature specified the desired
            temperature for the LOW mode.

            - If start_date is provided enable LOW mode indefiniitely.
            - If also end_date is provided end the LOW mode at this specified date/time.
            - If neither start_date nor end_date is provided disable LOW mode.
        """
        if start_datetime is None:
            start_datetime = datetime.now()

        if temperature is None:
            temperature = self.getLowMode()["temperature"]

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {
            "lowData": "{:03d}{}{}".format(
                int(temperature),
                start_datetime.strftime("%Y-%m-%d%H:%M") if enabled and start_datetime else " " * 15,
                end_datetime.strftime("%Y-%m-%d%H:%M") if enabled and end_datetime else " " * 15,
            )
        }
        response = self._http.post("/lowSave", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getLowModeAssignments(self):
        """ Load circuit LOW mode assignments, i.e. which circuits will be
            affected by LOW mode when it is turned on.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = self._http.post("/lowLoadRooms", headers=headers, data={"param": "+"})
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return [bool(int(x)) for x in list(response.text)]

    @authenticated
    def setLowModeAssignments(self, circuits, value):
        """ Assign or remove specified circuits to/from LOW mode. Leave
            other circuits as they are.
        """
        assignments = self.getLowModeAssignments()

        for circuit_id in circuits:
            assignments[circuit_id] = value

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"value": "".join([str(int(x)) for x in assignments])}
        response = self._http.post("/lowSaveRooms", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    @ttl_cache(maxsize=CACHE_DEFAULT_MAXSIZE, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getCircuitSchedules(self, circuit_id):
        """ Load circuit schedule assignments, i.e. which schedule is assigned
            to what day. It is possible to set different schedule for up 21
            days.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        data = {"roomID": "{:02d}".format(circuit_id)}
        response = self._http.post("/roomSettings", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))

        # Example: 0140-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
        match = re.match(
            r"""
                (?P<starting_day>\d{2})        # Which schedule should be the
                                               # first to start with. Can be either
                                               # "01", "08" or "15". Note that
                                               # there can't be any unconfigured
                                               # gaps (missing schedules) in any
                                               # days between day 1 and the
                                               # starting day.
                (?P<day_schedules>([-\d]{2}){21})  # schedule IDs + indicator of the
                                               # currently active schedule
                """,
            response.text,
            re.VERBOSE,
        )
        if not match:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))
        circuit_schedules = match.groupdict()
        result = {"starting_day": int(circuit_schedules["starting_day"]), "current_day": None, "day_schedules": []}
        for idx, schedule_id in enumerate(re.findall(r"[-\d]{2}", circuit_schedules["day_schedules"])):
            schedule_id = int(schedule_id)
            if schedule_id == -1:
                # The list of schedules must be continuous, there aren't
                # allowed any "gaps". So this is the last entry, following items
                # have to be are "-1" as well.
                break
            else:
                result["day_schedules"].append(schedule_id & 0b00011111)  # schedule ID is in the lower 5 bits
                if (
                    schedule_id & 0b00100000 == 0b00100000
                ):  # 6th rightmost bit is indicator of currently active schedule
                    result["current_day"] = idx + 1
        return result

    @authenticated
    def setCircuitSchedules(self, circuit_id, day_schedules, starting_day=1):
        """ Assign circuits schedules. It is possible to have a different
            schedule for up to 21 days.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        # Make sure that day_schedules is list with length 21, if not append None's at the end
        day_schedules += [None for _ in range(21 - len(day_schedules))]

        # Make sure there are no undefined gaps
        for idx in range(len(day_schedules) - 1):
            if day_schedules[idx] is None and day_schedules[idx + 1] is not None:
                raise Exception("Circuit schedules can't have any undefined gaps.")

        # Example: 000108-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
        data = {
            "roomSettings": "{:02d}{:02d}{}".format(
                circuit_id, starting_day, "".join(["{:02d}".format(x if x is not None else -1) for x in day_schedules])
            )
        }
        response = self._http.post("/saveAssignmentModes", headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    @ttl_cache(maxsize=1, ttl=CACHE_DEFAULT_TTL)
    @authenticated
    def getHDO(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = self._http.post("/loadHDO", headers=headers, data="param=+")
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return response.text == "1"
