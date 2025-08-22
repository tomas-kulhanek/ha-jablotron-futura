from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .coordinator import FuturaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    coordinator = FuturaCoordinator(hass, entry.data)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(f"Initial connection failed: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_set_away(call):
        begin = call.data.get("begin")
        end = call.data.get("end")
        await coordinator.async_set_away(begin, end)

    async def handle_clear_away(call):
        await coordinator.async_clear_away()

    hass.services.async_register(DOMAIN, "set_away", handle_set_away)
    hass.services.async_register(DOMAIN, "clear_away", handle_clear_away)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    coordinator: FuturaCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_close()
    return unload_ok
