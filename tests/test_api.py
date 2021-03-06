import os
import unittest
from datetime import datetime

import requests_mock
from dateutil.tz import tzutc

from august.api import API_GET_DOORBELLS_URL, Api, API_GET_LOCKS_URL, \
    API_GET_LOCK_STATUS_URL, API_LOCK_URL, API_UNLOCK_URL, API_GET_LOCK_URL, \
    API_GET_DOORBELL_URL, API_GET_PINS_URL
from august.lock import LockStatus, LockDoorStatus

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), 'fixtures', filename)
    with open(path) as fptr:
        return fptr.read()


def utc_of(year, month, day, hour, minute, second, microsecond):
    return datetime(year, month, day, hour, minute, second, microsecond,
                    tzinfo=tzutc())


class TestApi(unittest.TestCase):
    @requests_mock.Mocker()
    def test_get_doorbells(self, mock):
        mock.register_uri(
            "get",
            API_GET_DOORBELLS_URL,
            text=load_fixture("get_doorbells.json"))

        api = Api()
        doorbells = sorted(api.get_doorbells(ACCESS_TOKEN),
                           key=lambda d: d.device_id)

        self.assertEqual(2, len(doorbells))

        first = doorbells[0]
        self.assertEqual("1KDAbJH89XYZ", first.device_id)
        self.assertEqual("aaaaR08888", first.serial_number)
        self.assertEqual("Back Door", first.device_name)
        self.assertEqual("doorbell_call_status_offline", first.status)
        self.assertEqual(False, first.has_subscription)
        self.assertEqual(None, first.image_url)
        self.assertEqual("3dd2accadddd", first.house_id)

        second = doorbells[1]
        self.assertEqual("K98GiDT45GUL", second.device_id)
        self.assertEqual("tBXZR0Z35E", second.serial_number)
        self.assertEqual("Front Door", second.device_name)
        self.assertEqual("doorbell_call_status_online", second.status)
        self.assertEqual(True, second.has_subscription)
        self.assertEqual("https://image.com/vmk16naaaa7ibuey7sar.jpg",
                         second.image_url)
        self.assertEqual("3dd2accaea08", second.house_id)

    @requests_mock.Mocker()
    def test_get_doorbell_detail(self, mock):
        mock.register_uri(
            "get",
            API_GET_DOORBELL_URL.format(doorbell_id="K98GiDT45GUL"),
            text=load_fixture("get_doorbell.json"))

        api = Api()
        doorbell = api.get_doorbell_detail(ACCESS_TOKEN, "K98GiDT45GUL")

        self.assertEqual("K98GiDT45GUL", doorbell.device_id)
        self.assertEqual("Front Door", doorbell.device_name)
        self.assertEqual("3dd2accaea08", doorbell.house_id)
        self.assertEqual("tBXZR0Z35E", doorbell.serial_number)
        self.assertEqual("2.3.0-RC153+201711151527", doorbell.firmware_version)
        self.assertEqual("doorbell_call_status_online", doorbell.status)
        self.assertEqual(True, doorbell.is_online)
        self.assertEqual(True, doorbell.has_subscription)
        self.assertEqual("https://image.com/vmk16naaaa7ibuey7sar.jpg",
                         doorbell.image_url)

    @requests_mock.Mocker()
    def test_get_locks(self, mock):
        mock.register_uri(
            "get",
            API_GET_LOCKS_URL,
            text=load_fixture("get_locks.json"))

        api = Api()
        locks = sorted(api.get_locks(ACCESS_TOKEN), key=lambda d: d.device_id)

        self.assertEqual(2, len(locks))

        first = locks[0]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.device_id)
        self.assertEqual("Front Door Lock", first.device_name)
        self.assertEqual("000000000000", first.house_id)
        self.assertEqual(True, first.is_operable)

        second = locks[1]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF9999", second.device_id)
        self.assertEqual("Back Door Lock", second.device_name)
        self.assertEqual("000000000011", second.house_id)
        self.assertEqual(False, second.is_operable)

    @requests_mock.Mocker()
    def test_get_operable_locks(self, mock):
        mock.register_uri(
            "get",
            API_GET_LOCKS_URL,
            text=load_fixture("get_locks.json"))

        api = Api()
        locks = api.get_operable_locks(ACCESS_TOKEN)

        self.assertEqual(1, len(locks))

        first = locks[0]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.device_id)
        self.assertEqual("Front Door Lock", first.device_name)
        self.assertEqual("000000000000", first.house_id)
        self.assertEqual(True, first.is_operable)

    @requests_mock.Mocker()
    def test_get_lock_detail(self, mock):
        mock.register_uri(
            "get",
            API_GET_LOCK_URL.format(
                lock_id="A6697750D607098BAE8D6BAA11EF8063"),
            text=load_fixture("get_lock.json"))

        api = Api()
        lock = api.get_lock_detail(ACCESS_TOKEN,
                                   "A6697750D607098BAE8D6BAA11EF8063")

        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", lock.device_id)
        self.assertEqual("Front Door Lock", lock.device_name)
        self.assertEqual("000000000000", lock.house_id)
        self.assertEqual("X2FSW05DGA", lock.serial_number)
        self.assertEqual("109717e9-3.0.44-3.0.30", lock.firmware_version)
        self.assertEqual(88, lock.battery_level)
        self.assertEqual("Medium", lock.keypad.battery_level)
        self.assertEqual("5bc65c24e6ef2a263e1450a8", lock.keypad.device_id)

    @requests_mock.Mocker()
    def test_get_lock_status_with_locked_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"kAugLockState_Locked\"}")

        api = Api()
        status = api.get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.LOCKED, status)

    @requests_mock.Mocker()
    def test_get_lock_and_door_status_with_locked_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"kAugLockState_Locked\""
                 ",\"doorState\": \"kAugLockDoorState_Closed\"}")

        api = Api()
        status, door_status = api.get_lock_status(ACCESS_TOKEN, lock_id, True)

        self.assertEqual(LockStatus.LOCKED, status)
        self.assertEqual(LockDoorStatus.CLOSED, door_status)

    @requests_mock.Mocker()
    def test_get_lock_status_with_unlocked_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"kAugLockState_Unlocked\"}")

        api = Api()
        status = api.get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLOCKED, status)

    @requests_mock.Mocker()
    def test_get_lock_status_with_unknown_status_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"not_advertising\"}")

        api = Api()
        status = api.get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNKNOWN, status)

    @requests_mock.Mocker()
    def test_get_lock_door_status_with_closed_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"doorState\": \"kAugLockDoorState_Closed\"}")

        api = Api()
        door_status = api.get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.CLOSED, door_status)

    @requests_mock.Mocker()
    def test_get_lock_door_status_with_open_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"doorState\": \"kAugLockDoorState_Open\"}")

        api = Api()
        door_status = api.get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.OPEN, door_status)

    @requests_mock.Mocker()
    def test_get_lock_and_door_status_with_open_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"status\": \"kAugLockState_Unlocked\""
                 ",\"doorState\": \"kAugLockDoorState_Open\"}")

        api = Api()
        door_status, status = api.get_lock_door_status(ACCESS_TOKEN, lock_id,
                                                       True)

        self.assertEqual(LockDoorStatus.OPEN, door_status)
        self.assertEqual(LockStatus.UNLOCKED, status)

    @requests_mock.Mocker()
    def test_get_lock_door_status_with_unknown_response(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            text="{\"doorState\": \"not_advertising\"}")

        api = Api()
        door_status = api.get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.UNKNOWN, door_status)

    @requests_mock.Mocker()
    def test_lock(self, mock):
        lock_id = 1234
        mock.register_uri(
            "put",
            API_LOCK_URL.format(lock_id=lock_id),
            text="{\"status\":\"locked\","
                 "\"dateTime\":\"2017-12-10T07:43:39.056Z\","
                 "\"isLockStatusChanged\":false,"
                 "\"valid\":true}")

        api = Api()
        status = api.lock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.LOCKED, status)

    @requests_mock.Mocker()
    def test_unlock(self, mock):
        lock_id = 1234
        mock.register_uri(
            "put",
            API_UNLOCK_URL.format(lock_id=lock_id),
            text="{\"status\": \"unlocked\"}")

        api = Api()
        status = api.unlock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLOCKED, status)

    @requests_mock.Mocker()
    def test_get_pins(self, mock):
        lock_id = 1234
        mock.register_uri(
            "get",
            API_GET_PINS_URL.format(lock_id=lock_id),
            text=load_fixture("get_pins.json"))

        api = Api()
        pins = api.get_pins(ACCESS_TOKEN, lock_id)

        self.assertEqual(1, len(pins))

        first = pins[0]
        self.assertEqual("epoZ87XSPqxlFdsaYyJiRRVR", first.pin_id)
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.lock_id)
        self.assertEqual("c3b3a94f-473z-61a3-a8d1-a6e99482787a", first.user_id)
        self.assertEqual("in-use", first.state)
        self.assertEqual("123456", first.pin)
        self.assertEqual(646545456465161, first.slot)
        self.assertEqual("one-time", first.access_type)
        self.assertEqual("John", first.first_name)
        self.assertEqual("Doe", first.last_name)
        self.assertEqual(True, first.unverified)
        self.assertEqual(utc_of(2016, 11, 26, 22, 27, 11, 176000),
                         first.created_at)
        self.assertEqual(utc_of(2017, 11, 23, 00, 42, 19, 470000),
                         first.updated_at)
        self.assertEqual(utc_of(2017, 12, 10, 3, 12, 55, 563000),
                         first.loaded_date)
        self.assertEqual(utc_of(2018, 1, 1, 1, 1, 1, 563000),
                         first.access_start_time)
        self.assertEqual(utc_of(2018, 12, 1, 1, 1, 1, 563000),
                         first.access_end_time)
        self.assertEqual(utc_of(2018, 11, 5, 10, 2, 41, 684000),
                         first.access_times)
