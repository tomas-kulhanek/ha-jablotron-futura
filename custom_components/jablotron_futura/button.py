from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator


class FuturaBoost60(ButtonEntity, FuturaEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        FuturaEntity.__init__(self, coordinator, "Spustit Boost (60 min)", "boost_button")

    async def async_press(self) -> None:
        await self.coordinator._write_u16(1, 60 * 60)
        await self.coordinator.async_request_refresh()


class FuturaCirculation30(ButtonEntity, FuturaEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        FuturaEntity.__init__(self, coordinator, "Spustit Cirkulaci (30 min)", "circulation_button")

    async def async_press(self) -> None:
        await self.coordinator._write_u16(2, 30 * 60)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    coord: FuturaCoordinator = hass.data["jablotron_futura"][entry.entry_id]
    async_add_entities([FuturaBoost60(coord), FuturaCirculation30(coord)], True)
