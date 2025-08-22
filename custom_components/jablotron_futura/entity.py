from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FuturaCoordinator


class FuturaEntity(CoordinatorEntity[FuturaCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FuturaCoordinator, name: str, unique_suffix: str) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.host}-{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "manufacturer": "Jablotron",
            "model": "Futura",
            "name": "Jablotron Futura",
        }
