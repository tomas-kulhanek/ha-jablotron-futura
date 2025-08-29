from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator


class FuturaFlapCover(FuturaEntity, CoverEntity):
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
    )

    def __init__(self, coordinator: FuturaCoordinator, name: str, key: str, address: int) -> None:
        super().__init__(coordinator, name, f"cover_{key}")
        self.key = key
        self.address = address

    @property
    def is_closed(self) -> bool | None:
        return int(self.coordinator.data.get(self.key, 0) or 0) == 0

    async def async_open_cover(self, **kwargs) -> None:
        await self.coordinator._write_u16(self.address, 1)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs) -> None:
        await self.coordinator._write_u16(self.address, 0)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coord: FuturaCoordinator = hass.data["jablotron_futura"][entry.entry_id]

    if not coord.data.get("has_vario_breeze") or not coord.data.get("flaps_present"):
        return

    entities = [
        FuturaFlapCover(coord, "Klapka přívodu", "flap_supply_raw", 18),
        FuturaFlapCover(coord, "Klapka odtahu", "flap_extract_raw", 19),
    ]

    async_add_entities(entities, True)
