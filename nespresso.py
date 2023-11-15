import asyncio
import pprint
from bleak import BleakScanner, BleakClient, BLEDevice
from bleak_retry_connector import establish_connection
from .machines import CoffeeMachineFactory, BaseDecode, MachineType, BrewType, Temprature, get_machine_type_from_model_name
from datetime import datetime, timedelta
import binascii
import uuid
from collections import namedtuple
import logging

_LOGGER = logging.getLogger(__name__)

CHAR_UUID_DEVICE_NAME = '00002a00-0000-1000-8000-00805f9b34fb'
CHAR_UUID_MANUFACTURER_NAME = '00002a00-0000-1000-8000-00805f9b34fb'
CHAR_UUID_STATE = '06aa3a12-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_NBCAPS = '06aa3a15-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_SLIDER = '06aa3a22-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_WATER_HARDNESS = '06aa3a44-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_AUTH = '06aa3a41-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_ONBOARD_STATUS = '06aa3a51-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_PAIR = '06aa3a61-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_CMDRESP = '06aa3a52-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_SERIAL = '06aa3a31-f22a-11e3-9daa-0002a5d5c51b'
CHAR_UUID_BREW = '06aa3a42-f22a-11e3-9daa-0002a5d5c51b'

Characteristic = namedtuple('Characteristic', ['uuid', 'name', 'format'])

manufacturer_characteristics = Characteristic(CHAR_UUID_MANUFACTURER_NAME, 'manufacturer', "utf-8")
device_info_characteristics = [manufacturer_characteristics,
                               Characteristic(CHAR_UUID_DEVICE_NAME, 'device_name', "utf-8"),
                               Characteristic(CHAR_UUID_SERIAL, 'serial', "utf-8"),
                               Characteristic(CHAR_UUID_ONBOARD_STATUS, 'paired_status', "utf-8")]
sensors_characteristics = [CHAR_UUID_STATE, CHAR_UUID_NBCAPS,
                           CHAR_UUID_SLIDER, CHAR_UUID_WATER_HARDNESS]

sensor_decoders = {str(CHAR_UUID_STATE):BaseDecode(name="state", format_type='state'),
                   str(CHAR_UUID_NBCAPS):BaseDecode(name="caps_number", format_type='caps_number'),
                   str(CHAR_UUID_SLIDER):BaseDecode(name="slider", format_type='slider'),
                   str(CHAR_UUID_WATER_HARDNESS):BaseDecode(name="water_hardness", format_type='water_hardness'),
                   str(CHAR_UUID_CMDRESP):BaseDecode(name="command_response", format_type='command_response'),
                   str(CHAR_UUID_ONBOARD_STATUS):BaseDecode(name="pairing_key", format_type="paired_status")}

class NespressoClient():
    def __init__(self, scan_interval=timedelta(seconds=180), AUTH_CODE=None, mac=None, device: BLEDevice = None) -> None:
        self.nespresso_devices = [] if mac is None else [mac]
        self.auth_code = AUTH_CODE
        self.sensors: dict = {}
        self.sensordata: dict = {}
        self.data_update_interval = scan_interval
        self.data_update_lock = asyncio.Lock()
        self.data_last_updated: datetime | None = None
        self.brew_response = None
        self.isOnboard = None
        self.machine: MachineType | None = None
        self.address = mac
        self._conn: None | BleakClient = None

    async def connect(self, device: BLEDevice) -> bool:
        # Return early if already connected
        if self._conn:
            if self._conn.is_connected:
                return True
        
        # Establish new connection
        client = await establish_connection(BleakClient, device, device.address)
        paired = device.details['props']['Paired']
        if not paired and client.is_connected:
            client.pair()
        
        # Try to onboard if not already
        if not self.isOnboard:
            await self.get_onboard_status(client)
            if not self.isOnboard:
                self.auth_code = self.generate_auth_key()
                await self.onboard(client)
                await self.get_onboard_status(client)
                if not self.isOnboard:
                    _LOGGER.error(f'Failed to onboard {device.name}')
                    return False

        if self.auth_code and paired and client.is_connected:
            await self.auth(client)

        try:
            # Test reading protected property to verify auth
            state = await client.read_gatt_char(CHAR_UUID_STATE, response=True)
        except Exception as e:
            _LOGGER.error(f'Failed to connect to Nespresso device: {device.name}')
            return False

        self._conn = client    
        return True


    async def disconnect(self) -> None:
        await self._conn.disconnect()
        self._conn = None

    async def scan(self):
        print("Scanning for 5 seconds, please wait...")

        devices = await BleakScanner.discover(return_adv=True)

        for device, advertisment in devices.values():
            if get_machine_type_from_model_name(device.name):
                print()
                print(device)
                print("-" * len(str(device)))
                print(advertisment)

                self.nespresso_devices.append(device.address)

        return len(self.nespresso_devices)

    async def get_info(self, tries=0):
        self.devices = {}
        try:
            device = await self.load_model()
            device.mac_address = self._conn.address
            for characteristic in device_info_characteristics:
                try:
                    data = await self._conn.read_gatt_char(characteristic.uuid)
                    setattr(device, characteristic.name, data.decode(characteristic.format))
                except Exception as e:
                    print(f'Error reading characteristic {characteristic.name}: {e}')
        except Exception as e:
            print(f'some other error: {e}')

        self.devices[device.mac_address] = device
        return self.devices
    
    async def get_sensors(self):
        self.sensors = {}
        sensor_characteristics =  []
        for uuid in sensors_characteristics:
            characteristic = self._conn.services.get_characteristic(uuid)
            if characteristic:
                sensor_characteristics.append(characteristic.uuid)
        self.sensors[self._conn.address] = sensor_characteristics
        return self.sensors

    async def get_sensor_data(self):
        now = datetime.now()
        if self.data_last_updated is None or now - self.data_last_updated > self.data_update_interval:
            self.data_last_updated = now
            for mac, characteristics in self.sensors.items():
                for characteristic in characteristics:
                    try:
                        data = await self._conn.read_gatt_char(characteristic)
                        if characteristic in sensor_decoders:
                            sensor_data = sensor_decoders[characteristic].decode_data(data)
                            if self.sensordata.get(mac) is None:
                                self.sensordata[mac] = sensor_data
                            else:
                                self.sensordata[mac].update(sensor_data)
                    except Exception as e:
                        print(f'Error: {e}')
                        return None
            return self.sensordata
    
    async def get_onboard_status(self, client: BleakClient):
        try:
            onboard = await client.read_gatt_char(CHAR_UUID_ONBOARD_STATUS) != bytearray(b'\x00')
        except Exception as e:
            _LOGGER.error('Couldn\'t read onboarding status of device. Probably BT Dongle incompatible?')
        self.isOnboard = onboard
        return self.isOnboard

    async def load_model(self):
        try:
            serial = await self._conn.read_gatt_char(CHAR_UUID_SERIAL)
            serial = serial.decode('utf-8')
            device_name = await self._conn.read_gatt_char(CHAR_UUID_DEVICE_NAME)
            device_name = device_name.decode('utf-8')

            self.machine = CoffeeMachineFactory.get_coffee_machine(device_name, serial)
            return self.machine
        except Exception as e:
            print(f'Can\'t init model: {e}')
            return None

    async def auth(self, client: BleakClient):
        await client.write_gatt_char(CHAR_UUID_AUTH, binascii.unhexlify(self.auth_code), response=True)

    async def onboard(self, client: BleakClient):
        try:
            # Write the txLevel to LOW
            await client.write_gatt_char(CHAR_UUID_PAIR, bytearray([1]), response=True)
            # Write the auth code
            await client.write_gatt_char(CHAR_UUID_AUTH, binascii.unhexlify(self.auth_code), response=True)
        except Exception as e:
            if e.dbus_error == 'org.bluez.Error.NotPermitted':
                _LOGGER.error('Onboarding not permitted. Already paired?')

    def notification_handler(self, sender, data):
        self.brew_response = sensor_decoders[CHAR_UUID_CMDRESP].decode_data(data)

    def generate_auth_key(self):
        unique_id = uuid.uuid4()
        hex_string = unique_id.hex
        return hex_string[:16]

    async def brew_predefined(self, brew: BrewType = BrewType.RISTRETTO, temp: Temprature = Temprature.MEDIUM):
        if BrewType.is_brew_applicable_for_machine(brew, self.devices[self._conn.address].model):
            try:
                self.brew_response = None
                command = "03050704" # Recepies
                command += "00000000" # Padding?

                # Temprature Selection
                command += temp.value if self.devices[self._conn.address].configurations['temprature_control'] else Temprature.MEDIUM.value

                # Brew Selection
                command += brew.value

                # Subscribe to Brew notifications
                await self._conn.start_notify(CHAR_UUID_CMDRESP, self.notification_handler)

                await self._conn.write_gatt_char(CHAR_UUID_BREW, binascii.unhexlify(command), response=True)

                for _ in range(10):  # Wait up to 10 seconds
                    if self.brew_response is not None:
                        break
                    await asyncio.sleep(1)  # Wait for 1 second before checking again

                # Unsubscribe from the Brew notifications
                await self._conn.stop_notify(CHAR_UUID_CMDRESP)

                return self.brew_response
            except Exception as e:
                print(f'Error Brewing: {e}')

async def main():
    nespresso_client = NespressoClient(180, '8f2aa3c13a61ac60')

    if not nespresso_client.nespresso_devices:
        await nespresso_client.scan()

    for mac in nespresso_client.nespresso_devices:
        async with BleakClient(BLEDevice('D1:E1:03:7C:4A:9D', 'Expert&Milk_D1E1037C4A9D', details={'path': '/org/bluez/hci1/dev_D1_E1_03_7C_4A_9D', 'props': {'Address': 'D1:E1:03:7C:4A:9D', 'AddressType': 'random', 'Name': 'Expert&Milk_D1E1037C4A9D', 'Alias': 'Expert&Milk_D1E1037C4A9D', 'Paired': True, 'Bonded': False, 'Trusted': False, 'Blocked': False, 'LegacyPairing': False}}, rssi=-60)) as client:
            print(f"Connected: {client.is_connected}")
            try:
                paired = await client.pair(protection_level=2)
                print(f"Paired: {paired}")

                # Check if the machine thinks its been onboarded
                onboarded = await client.read_gatt_char(CHAR_UUID_ONBOARD_STATUS) != bytearray(b'\x00')

                print(f'Onboarded: {onboarded}')
                exit()
                if not onboarded:
                    await nespresso_client.onboard(client)

                await nespresso_client.auth(client)

                await nespresso_client.get_info(client)

                sensor_characteristics =  []
                for uuid in sensors_characteristics:
                    characteristic = client.services.get_characteristic(uuid)
                    if characteristic:
                        sensor_characteristics.append(characteristic.uuid)
                nespresso_client.sensors[mac] = sensor_characteristics

                for mac, characteristics in nespresso_client.sensors.items():
                    for characteristic in characteristics:
                        try:
                            data = await client.read_gatt_char(characteristic)
                            if characteristic in sensor_decoders:
                                sensor_data = sensor_decoders[characteristic].decode_data(data)
                                if nespresso_client.sensordata.get(mac) is None:
                                    nespresso_client.sensordata[mac] = sensor_data
                                else:
                                    nespresso_client.sensordata[mac].update(sensor_data)
                        except Exception as e:
                            print(f'Error: {e}')
            except Exception as e:
                print(f'some error: {e}')

            pp = pprint.PrettyPrinter(indent=4)

            pp.pprint(nespresso_client.sensordata[mac])

            print('Sending brew..')

            response = await nespresso_client.brew_predefined(client)

            pp.pprint(response)

            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())