"""Config flow for nespresso integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfo,
    async_discovered_service_info,
    async_process_advertisements,
    async_ble_device_from_address
)

from .machines import supported
from .nespresso import NespressoClient
from bleak import BleakClient
from bleak_retry_connector import establish_connection

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(data["host"])

    if not await hub.authenticate(data["username"], data["password"]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for nespresso."""
    _discovered_devices: dict = {}

    VERSION = 1

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        device = NespressoClient(mac=discovery_info.address)
        ble_device = async_ble_device_from_address(self.hass, discovery_info.address)
        await device.connect(ble_device)
        await device.load_model()
        await device.disconnect()
        if not supported(discovery_info.name):
            return self.async_abort(reason="not_supported")
        self._discovery = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        assert self._discovery is not None

        if user_input is not None:
            if not isPairing(self._discovery):
                return await self.async_step_wait_for_pairing_mode()

            return self._create_snooz_entry(self._discovery)

        self._set_confirm_only()
        assert self._discovery.name
        placeholders = {"name": self._discovery.name}
        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders=placeholders
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            name = user_input[CONF_NAME]

            discovered = self._discovered_devices[name]

            assert discovered is not None

            self._discovery = discovered

            try:
                device = NespressoClient(mac=discovered.address)
                ble_device = async_ble_device_from_address(self.hass, discovered.address)
                await device.connect(ble_device)
                await device.load_model()
                await device.disconnect()
            except Exception as e:
                _LOGGER.error(f"Failed to connect to device: {e}")
                return self.async_show_form(
                    step_id="user",
                    errors={"base": "cannot_connect"}
                )

            address = discovered.address
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self._create_nespresso_entry(device)

        configured_addresses = self._async_current_ids()

        for info in async_discovered_service_info(self.hass):
            address = info.address
            if address in configured_addresses:
                continue
            if supported(info.name):
                assert info.name
                self._discovered_devices[info.name] = info

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): vol.In(
                        [
                            d.name
                            for d in self._discovered_devices.values()
                        ]
                    )
                }
            ),
        )
    
    def _create_nespresso_entry(self, device) -> FlowResult:
        assert self._discovery.name
        return self.async_create_entry(
            title=self._discovery.name,
            data={
                CONF_ADDRESS: device.address,
                CONF_TOKEN: device.auth_code,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
