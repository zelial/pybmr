from unittest.mock import MagicMock

import pytest

from pybmr import Bmr


def fakeserver(url, headers=None, data=None):
    response = MagicMock()
    response.status_code = 200
    if url.endswith("/menu.html"):
        response.text = ""
    elif url.endswith("/numOfRooms"):
        response.text = "16"
    elif url.endswith("/listOfRooms"):
        response.text = "F01 Byt      F02 Pokoj    F03 Loznice  F04 Koupelna F05 Det pokojF06 Chodba   F07 Kuchyne  F08 Obyvak   R01 Byt      R02 Pokoj    R03 Loznice  R04 Koupelna R05 Det pokojR06 Chodba   R07 Kuchyne  R08 Obyvak  "  # noqa
    elif url.endswith("/wholeRoom"):
        response.text = "1F01 Byt      017.5+32032.0000.005.0000000000"
    elif url.endswith("/listOfModes"):
        response.text = "1 Byt        2 Pokoj      3 Loznice    4 Koupelna   5 Det pokoj  6 Chodba     7 Kuchyn     8 Obyvak     Podlahy      Rezim 10     Rezim 11     Rezim 12     Rezim 13     Rezim 14     Rezim 15     Rezim 16     Rezim 17     Rezim 18     Rezim 19     Rezim 20     Rezim 21     Rezim 22     Rezim 23     Rezim 24     Rezim 25     Rezim 26     Rezim 27     Rezim 28     Rezim 29     Rezim 30     Rezim 31     Rezim 32"  # noqa
    elif url.endswith("/loadMode"):
        response.text = "1 Byt        00:0002106:0002112:0002121:00021"
    elif url.endswith("/loadSummerMode"):
        response.text = "1"
    elif url.endswith("/letoLoadRooms"):
        response.text = "1111111111111111"
    elif url.endswith("/loadLows"):
        response.text = "018"
    elif url.endswith("/lowLoadRooms"):
        response.text = "0000000011111111"
    elif url.endswith("/roomSettings"):
        response.text = "0140-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1"
    elif url.endswith("/loadHDO"):
        response.text = "0"
    elif url.endswith("/saveMode"):
        if data["modeSettings"] == "00Schedule 1   00:0002106:0002321:00021":
            response.text = "true"
    elif url.endswith("/deleteMode"):
        if data["modeID"] == "00":
            response.text = "true"
    elif url.endswith("/saveSummerMode"):
        if data["summerMode"] in ("0", "1"):
            response.text = "true"
    elif url.endswith("/letoSaveRooms"):
        if data["value"] == "0000111111111111":
            response.text = "true"
    elif url.endswith("/lowSave"):
        if data["lowData"] == "0182020-04-3018:002020-09-3018:00":
            response.text = "true"
    elif url.endswith("/lowSaveRooms"):
        if data["value"] == "0000000011111111":
            response.text = "true"
    elif url.endswith("/saveAssignmentModes"):
        if data["roomSettings"] == "0001010809-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1":
            response.text = "true"
    return response


@pytest.fixture
def bmr():
    bmr = Bmr("0.0.0.0", "admin", "1234")
    bmr._http.post = fakeserver

    return bmr
