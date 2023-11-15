"""
Support for Nespresso Connected mmachine.
https://www.nespresso.com

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.Nespresso/
"""
import logging
from datetime import timedelta, datetime

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (ATTR_DEVICE_CLASS, ATTR_ICON, CONF_ADDRESS,
                                 CONF_NAME, CONF_RESOURCE, CONF_SCAN_INTERVAL,
                                 CONF_UNIT_SYSTEM, DEVICE_CLASS_TIMESTAMP,
                                 EVENT_HOMEASSISTANT_STOP, STATE_UNKNOWN,
                                 CONF_TOKEN)
from homeassistant.components.binary_sensor import (PLATFORM_SCHEMA, BinarySensorEntity,
                                                   DEVICE_CLASS_MOTION, DEVICE_CLASS_DOOR)
from homeassistant.helpers.entity import Entity
from homeassistant.components.bluetooth import async_ble_device_from_address

from .nespresso import NespressoClient
from .machines import Temprature, BrewType
from bleak import BleakClient
from bleak_retry_connector import establish_connection

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=120)

DEVICE_CLASS_CAPS='caps'
CAPS_UNITS = 'caps'

from .const import DOMAIN

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ADDRESS, default=''): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
})


class Sensor:
    def __init__(self, unit, unit_scale, device_class, icon):
        self.unit = unit
        self.unit_scale = unit_scale
        self.device_class = device_class
        self.icon = icon

    def set_unit_scale(self, unit, unit_scale):
        self.unit = unit
        self.unit_scale = unit_scale

    def get_extra_attributes(self, data):
        return {}


DEVICE_SENSOR_SPECIFICS = { "state":Sensor(None, None, None, None),
                            "water_is_empty":Sensor(None, None, None, 'mdi:water-off'),
                            "descaling_needed":Sensor(None, None, None, 'mdi:silverware-clean'),
                            "capsule_mechanism_jammed":Sensor(None, None, None, None),
                            "always_1":Sensor(None, None, None, 'mdi:numeric-1'),
                            "water_temp_low":Sensor(None, None, None, 'mdi:snowflake-alert'),
                            "awake":Sensor(None, None, None, 'mdi:sleep-off'),
                            "water_engadged":Sensor(None, None, None, None),
                            "sleeping":Sensor(None, None, None, 'mdi:sleep'),
                            "tray_sensor_during_brewing":Sensor(None, None, None, None),
                            "tray_open_tray_sensor_full":Sensor(None, None, None, 'mdi:coffee-off-outline'),
                            "capsule_engaged":Sensor(None, None, None, None),
                            "Fault":Sensor(None, None, None, 'mdi:alert-circle-outline'),
                            "descaling_counter":Sensor(None, None, None, 'mdi:silverware-clean'),
                            "water_hardness":Sensor(None, None, None, 'mdi:water-percent'),
                            "slider":Sensor(None, None, DEVICE_CLASS_DOOR, 'mdi:gate-and'),
                            "caps_number": Sensor(CAPS_UNITS, None, DEVICE_CLASS_CAPS, 'mdi:counter'),
                           }


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info=None) -> None:
    """Set up the Nespresso sensor."""
    scan_interval = SCAN_INTERVAL
    mac = config.data.get(CONF_ADDRESS)
    auth = config.data.get(CONF_TOKEN)

    _LOGGER.debug("Searching for Nespresso sensors...")
    try:
        Nespressodetect = NespressoClient(scan_interval, auth, mac)
        ble_device = async_ble_device_from_address(hass, mac)
        await Nespressodetect.connect(ble_device)
    except UnboundLocalError:
        raise ConfigEntryNotReady()
    try:
        _LOGGER.debug("Getting info about device(s)")
        devices_info = await Nespressodetect.get_info()
        for mac, dev in devices_info.items():
            _LOGGER.info("{}: {}".format(mac, dev))

        _LOGGER.debug("Getting sensors")
        devices_sensors = await Nespressodetect.get_sensors()
        for mac, sensors in devices_sensors.items():
            for sensor in sensors:
                _LOGGER.debug("{}: Found sensor UUID: {}".format(mac, sensor))

        _LOGGER.debug("Get initial sensor data to populate HA entities")
        ha_entities = []
        sensordata = await Nespressodetect.get_sensor_data()
        for mac, data in sensordata.items():
            for name, val in data.items():
                _LOGGER.debug("{}: {}: {}".format(mac, name, val))
                ha_entities.append(NespressoSensor(mac, auth, name, Nespressodetect, devices_info[mac].manufacturer,
                                                   DEVICE_SENSOR_SPECIFICS[name]))
        
        await Nespressodetect.disconnect()
    except:
        _LOGGER.exception("Failed intial setup.")
        return

    async_add_entities(ha_entities, True)
    
    async def brew(call):
        """Send a command command."""
        try:
            brewType = BrewType[call.data.get('brew_type').upper()] if call.data.get('brew_type') else None
            temprature = Temprature[call.data.get('brew_temp').upper()] if call.data.get('brew_temp') else Temprature.MEDIUM
            coffee_ml = call.data.get('coffee_ml')
            water_ml = call.data.get('water_ml')
        except KeyError:
            brewType = None
            _LOGGER.debug(f"Brew Failed - Recepie: {brewType}, Temp: {temprature} ")
        
        try:
            ble_device = async_ble_device_from_address(hass, mac)
            conn_status = await Nespressodetect.connect(ble_device)
            if conn_status:
                if coffee_ml and water_ml:
                    response =  await Nespressodetect.brew_custom(coffee_ml=coffee_ml, water_ml=water_ml, temp=temprature)
                else:
                    response =  await Nespressodetect.brew_predefined(brew=brewType, temp=temprature)
                await Nespressodetect.disconnect()
                return response
            _LOGGER.error(f"Connection failed with {ble_device.name}")
            return None
        except:
            _LOGGER.debug(f"Brew Failed - Recepie: {brewType}, Temp: {temprature} ")

        return None

    hass.services.async_register(DOMAIN, "coffee", brew)    
    
class NespressoSensor(Entity):
    """General Representation of an Nespresso sensor."""
    def __init__(self, mac, auth, name, device, device_info, sensor_specifics):
        """Initialize a sensor."""
        self.device = device
        self._mac = mac
        self.auth = auth
        self._name = '{}-{}'.format(device_info, name)
        _LOGGER.debug("Added sensor entity {}".format(self._name))
        self._sensor_name = name

        self._device_class = sensor_specifics.device_class
        self._state = STATE_UNKNOWN
        self._sensor_specifics = sensor_specifics

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._sensor_specifics.icon

    @property
    def device_class(self):
        """Return the icon of the sensor."""
        return self._sensor_specifics.device_class

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._sensor_specifics.unit

    @property
    def unique_id(self):
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = self._sensor_specifics.get_extra_attributes(self._state)
        return attributes

    async def async_update(self) -> None:
        """Fetch new state data for the sensor asynchronously.
        This is the only method that should fetch new data for Home Assistant.
        """
        now = datetime.now()
        if self.device.data_last_updated is None or now - self.device.data_last_updated > SCAN_INTERVAL:
            async with self.device.data_update_lock:
                if self.device.data_last_updated is None or now - self.device.data_last_updated > SCAN_INTERVAL:
                    try:
                        ble_device = async_ble_device_from_address(self.hass, self._mac)
                        conn_status = await self.device.connect(ble_device)
                    except UnboundLocalError:
                        raise ConfigEntryNotReady()

                    await self.device.get_sensor_data()
                    await self.device.disconnect()
        value = self.device.sensordata[self._mac][self._sensor_name]

        if self._sensor_specifics.unit_scale is None:
            self._state = value
        else:
            self._state = round(float(value * self._sensor_specifics.unit_scale), 2)

        _LOGGER.debug("State {} {}".format(self._name, self._state))
    