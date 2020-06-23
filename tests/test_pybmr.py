from datetime import datetime


def testGetNumCircuits(bmr):
    assert bmr.getNumCircuits() == 16


def testGetCircuitNames(bmr):
    assert bmr.getCircuitNames() == [
        "F01 Byt",
        "F02 Pokoj",
        "F03 Loznice",
        "F04 Koupelna",
        "F05 Det pokoj",
        "F06 Chodba",
        "F07 Kuchyne",
        "F08 Obyvak",
        "R01 Byt",
        "R02 Pokoj",
        "R03 Loznice",
        "R04 Koupelna",
        "R05 Det pokoj",
        "R06 Chodba",
        "R07 Kuchyne",
        "R08 Obyvak",
    ]


def testGetUniqueId(bmr):
    assert bmr.getUniqueId() == "3ca28a9b"


def testGetCircuit(bmr):
    assert bmr.getCircuit(0) == {
        "id": 0,
        "enabled": True,
        "name": "F01 Byt",
        "temperature": 17.5,
        "target_temperature": 32,
        "user_offset": 0.0,
        "max_offset": 5.0,
        "heating": False,
        "warning": 0,
        "cooling": False,
        "low_mode": False,
        "summer_mode": False,
    }


def testGetSchedules(bmr):
    assert bmr.getSchedules() == [
        "1 Byt",
        "2 Pokoj",
        "3 Loznice",
        "4 Koupelna",
        "5 Det pokoj",
        "6 Chodba",
        "7 Kuchyn",
        "8 Obyvak",
        "Podlahy",
        "Rezim 10",
        "Rezim 11",
        "Rezim 12",
        "Rezim 13",
        "Rezim 14",
        "Rezim 15",
        "Rezim 16",
        "Rezim 17",
        "Rezim 18",
        "Rezim 19",
        "Rezim 20",
        "Rezim 21",
        "Rezim 22",
        "Rezim 23",
        "Rezim 24",
        "Rezim 25",
        "Rezim 26",
        "Rezim 27",
        "Rezim 28",
        "Rezim 29",
        "Rezim 30",
        "Rezim 31",
    ]


def testGetSchedule(bmr):
    assert bmr.getSchedule(0) == {
        "id": 0,
        "name": "1 Byt",
        "timetable": [
            {"time": "00:00", "temperature": 21},
            {"time": "06:00", "temperature": 21},
            {"time": "12:00", "temperature": 21},
            {"time": "21:00", "temperature": 21},
        ],
    }


def testSetSchedule(bmr):
    assert bmr.setSchedule(
        0,
        "Schedule 1",
        [
            {"time": "00:00", "temperature": 21},
            {"time": "06:00", "temperature": 23},
            {"time": "21:00", "temperature": 21},
        ],
    )


def testDeleteSchedule(bmr):
    assert bmr.deleteSchedule(0)


def testGetSummerMode(bmr):
    assert not bmr.getSummerMode()


def testSetSummerMode(bmr):
    assert bmr.setSummerMode(True)


def testGetSummerModeAssignments(bmr):
    assert bmr.getSummerModeAssignments() == [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    ]


def testSetSummerModeAssignments(bmr):
    assert bmr.setSummerModeAssignments([0, 1, 2, 3], False)


def testGetLowMode(bmr):
    assert bmr.getLowMode() == {"enabled": False, "temperature": 18}


def testSetLowMode(bmr):
    assert bmr.setLowMode(True, 18, datetime(2020, 4, 30, 18, 0, 0), datetime(2020, 9, 30, 18, 0, 0))


def testGetLowModeAssignments(bmr):
    assert bmr.getLowModeAssignments() == [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    ]


def testSetLowModeAssignments(bmr):
    assert bmr.setLowModeAssignments([0, 1, 2, 3], False)


def testGetCircuitSchedules(bmr):
    assert bmr.getCircuitSchedules(0) == {"current_day": 1, "day_schedules": [8], "starting_day": 1}


def testSetCircuitSchedules(bmr):
    assert bmr.setCircuitSchedules(0, [1, 8, 9], 1)


def testGetHDO(bmr):
    assert not bmr.getHDO()
