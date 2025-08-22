from __future__ import annotations

from homeassistant.components.number import NumberEntity

from .entity import FuturaEntity
from .coordinator import FuturaCoordinator


class FuturaTempSetNumber(FuturaEntity, NumberEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        super().__init__(coordinator, "Požadovaná teplota", "temp_set")
        self._attr_native_min_value = 15.0
        self._attr_native_max_value = 28.0
        self._attr_native_step = 0.5
        self._attr_native_unit_of_measurement = "°C"

    @property
    def native_value(self) -> float | None:
        return float(self.coordinator.data.get("temp_set_raw", 22.0))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator._write_u16(10, int(round(value * 10)))
        await self.coordinator.async_request_refresh()


class FuturaBoostMinutes(FuturaEntity, NumberEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        super().__init__(coordinator, "Boost – minuty", "boost_minutes")
        self._attr_native_min_value = 0
        self._attr_native_max_value = 120
        self._attr_native_step = 15
        self._attr_unit_of_measurement = "min"

    @property
    def native_value(self) -> float | None:
        return int(self.coordinator.data.get("boost_remaining_min", 0))

    async def async_set_native_value(self, value: float) -> None:
        minutes = int((value // 15) * 15)
        secs = minutes * 60
        await self.coordinator._write_u16(1, secs)
        await self.coordinator.async_request_refresh()


class FuturaCirculationMinutes(FuturaEntity, NumberEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        super().__init__(coordinator, "Cirkulace – minuty", "circulation_minutes")
        self._attr_native_min_value = 0
        self._attr_native_max_value = 120
        self._attr_native_step = 1
        self._attr_unit_of_measurement = "min"

    @property
    def native_value(self) -> float | None:
        s = int(self.coordinator.data.get("circulation_remaining_s", 0))
        return (s + 59) // 60

    async def async_set_native_value(self, value: float) -> None:
        secs = int(value) * 60
        await self.coordinator._write_u16(2, secs)
        await self.coordinator.async_request_refresh()


class FuturaNightHours(FuturaEntity, NumberEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        super().__init__(coordinator, "Noc – hodiny", "night_hours")
        self._attr_native_min_value = 0
        self._attr_native_max_value = 10
        self._attr_native_step = 1
        self._attr_unit_of_measurement = "h"

    @property
    def native_value(self) -> float | None:
        s = int(self.coordinator.data.get("night_remaining_s", 0))
        return 0 if s == 0 else (s + 3599) // 3600

    async def async_set_native_value(self, value: float) -> None:
        v = max(0, min(10, int(value)))
        secs = v * 3600
        await self.coordinator._write_u16(4, secs)
        await self.coordinator.async_request_refresh()


class FuturaPartyHours(FuturaEntity, NumberEntity):
    def __init__(self, coordinator: FuturaCoordinator):
        super().__init__(coordinator, "Party – hodiny", "party_hours")
        self._attr_native_min_value = 0
        self._attr_native_max_value = 8
        self._attr_native_step = 1
        self._attr_unit_of_measurement = "h"

    @property
    def native_value(self) -> float | None:
        s = int(self.coordinator.data.get("party_remaining_s", 0))
        return 0 if s == 0 else (s + 3599) // 3600

    async def async_set_native_value(self, value: float) -> None:
        v = max(0, min(8, int(value)))
        secs = v * 3600
        await self.coordinator._write_u16(5, secs)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    coord: FuturaCoordinator = hass.data["jablotron_futura"][entry.entry_id]
    async_add_entities([
        FuturaTempSetNumber(coord),
        FuturaBoostMinutes(coord),
        FuturaCirculationMinutes(coord),
        FuturaNightHours(coord),
        FuturaPartyHours(coord),
    ], True)
