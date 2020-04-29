from datetime import datetime


def testGetNumCircuits(bmr):
    assert bmr.getNumCircuits() == 16


def testLoadCircuit(bmr):
    assert bmr.loadCircuit(0) == {
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


def testLoadSchedules(bmr):
    assert bmr.loadSchedules() == [
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


def testLoadSchedule(bmr):
    assert bmr.loadSchedule(0) == {
        "id": 0,
        "name": "1 Byt",
        "timetable": [
            {"time": "00:00", "temperature": 21},
            {"time": "06:00", "temperature": 21},
            {"time": "12:00", "temperature": 21},
            {"time": "21:00", "temperature": 21},
        ],
    }


def testSaveSchedule(bmr):
    assert bmr.saveSchedule(
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


def testLoadSummerModeAssignments(bmr):
    assert bmr.loadSummerModeAssignments() == [
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


def testSaveSummerModeAssignments(bmr):
    assert bmr.saveSummerModeAssignments([0, 1, 2, 3], False)


def testGetLowMode(bmr):
    assert bmr.getLowMode() == {"enabled": False, "temperature": 18}


def testSetLowMode(bmr):
    assert bmr.setLowMode(True, 18, datetime(2020, 4, 30, 18, 0, 0), datetime(2020, 9, 30, 18, 0, 0))


def testLoadLowModeAssignments(bmr):
    assert bmr.loadLowModeAssignments() == [
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


def testSaveLowModeAssignments(bmr):
    assert bmr.saveLowModeAssignments([0, 1, 2, 3], False)


def testLoadCircuitSchedules(bmr):
    assert bmr.loadCircuitSchedules(0) == {"current_day": 1, "day_schedules": [8], "starting_day": 1}


def testSaveCircuitSchedules(bmr):
    assert bmr.saveCircuitSchedules(0, [1, 8, 9], 1)


def testLoadHDO(bmr):
    assert not bmr.loadHDO()
