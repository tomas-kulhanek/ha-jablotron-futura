from __future__ import annotations
from typing import List, Tuple, Dict

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FuturaCoordinator

# ----- mapy bitů (EN klíče -> CZ popis pro friendly name) --------------------

ERROR_BITS: List[Tuple[str, int, str]] = [
    ("error_sensor_ambient", 0,  "Chyba senzoru (ambient)"),
    ("error_sensor_indoor",  1,  "Chyba senzoru (indoor)"),
    ("error_sensor_fresh",   2,  "Chyba senzoru (fresh)"),
    ("error_sensor_waste",   3,  "Chyba senzoru (waste)"),
    ("error_fan_supply",     4,  "Chyba přívodního ventilátoru"),
    ("error_fan_extract",    5,  "Chyba odtahového ventilátoru"),
    ("error_hex_comm",       6,  "Chyba komunikace s výměníkem"),
    ("error_hex_damper",     7,  "Chyba polohy klapek výměníku"),
    ("error_io_board_comm",  8,  "Chyba komunikace s IO deskou"),
    ("error_fan_supply_blocked",  9,  "Zablokovaný přívodní ventilátor"),
    ("error_fan_extract_blocked", 10, "Zablokovaný odtahový ventilátor"),
    ("error_coolbreeze_comm",    11, "Chyba komunikace s CoolBreeze"),
    ("error_coolbreeze_outdoor", 12, "Chyba venkovní jednotky CoolBreeze"),
]

WARNING_NAMES_CZ: Dict[int, str] = {
    0:  "Neinicializovaný filtr",
    1:  "Filtr je příliš zanesený",
    2:  "Filtr se používá příliš dlouho",
    3:  "Nízké napětí RTC baterie",
    4:  "Příliš vysoké otáčky přívodního ventilátoru",
    5:  "Příliš vysoké otáčky odtahového ventilátoru",
    6:  "Varování – bit 6 (nezadokumentováno)",
    7:  "Varování – bit 7 (nezadokumentováno)",
    8:  "Příliš nízká venkovní teplota, omezená funkce větrání",
    9:  "Nesprávná konfigurace zón – přívod",
    10: "Nesprávná konfigurace zón – odtah",
    11: "Nouzové vypnutí",
    12: "Chyba komunikace se SuperBreeze",
    13: "Obecná chyba SuperBreeze",
    14: "Varování – bit 14 (nezadokumentováno)",
    15: "Varování – bit 15 (nezadokumentováno)",
    16: "Varování – bit 16 (nezadokumentováno)",
    17: "Varování – bit 17 (nezadokumentováno)",
    18: "Varování – bit 18 (nezadokumentováno)",
    19: "Varování – bit 19 (nezadokumentováno)",
    20: "Varování – bit 20 (nezadokumentováno)",
    21: "Varování – bit 21 (nezadokumentováno)",
    22: "Varování – bit 22 (nezadokumentováno)",
    23: "Varování – bit 23 (nezadokumentováno)",
    24: "Varování – bit 24 (nezadokumentováno)",
    25: "Varování – bit 25 (nezadokumentováno)",
    26: "Varování – bit 26 (nezadokumentováno)",
    27: "Varování – bit 27 (nezadokumentováno)",
    28: "Varování – bit 28 (nezadokumentováno)",
    29: "Varování – bit 29 (nezadokumentováno)",
    30: "Varování – bit 30 (nezadokumentováno)",
    31: "Varování – bit 31 (nezadokumentováno)",
}

# ----- společný základ --------------------------------------------------------

class _FuturaBinaryBase(CoordinatorEntity[FuturaCoordinator], BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: FuturaCoordinator, entry: ConfigEntry, key_en: str, name_cz: str) -> None:
        super().__init__(coordinator)
        # Friendly name (UI) česky:
        self._attr_name = name_cz
        # Stabilní unique_id:
        self._attr_unique_id = f"{entry.entry_id}_{key_en}"
        # Entity ID v angličtině (nastavit PŘED přidáním do HA):
        self.entity_id = f"binary_sensor.{DOMAIN}_{key_en}"

# ----- konkrétní senzory ------------------------------------------------------

class AnyErrorBinary(_FuturaBinaryBase):
    def __init__(self, coordinator: FuturaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "any_error", "Futura – je nějaká chyba")

    @property
    def is_on(self) -> bool:
        return int(self.coordinator.data.get("errors_bits_raw", 0) or 0) != 0


class AnyWarningBinary(_FuturaBinaryBase):
    def __init__(self, coordinator: FuturaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "any_warning", "Futura – je nějaké varování")

    @property
    def is_on(self) -> bool:
        return int(self.coordinator.data.get("warnings_bits_raw", 0) or 0) != 0


class AntiRadonBinary(_FuturaBinaryBase):
    def __init__(self, coordinator: FuturaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "antiradon_active", "Protiradon – aktivní")

    @property
    def is_on(self) -> bool:
        return int(self.coordinator.data.get("antiradon_raw", 0) or 0) == 0


class BitBinary(_FuturaBinaryBase):
    def __init__(
        self,
        coordinator: FuturaCoordinator,
        entry: ConfigEntry,
        key_en: str,
        name_cz: str,
        *,
        source: str,
        bit: int,
    ) -> None:
        super().__init__(coordinator, entry, key_en, name_cz)
        self._source = source
        self._bit = bit

    @property
    def is_on(self) -> bool:
        v = int(self.coordinator.data.get(self._source, 0) or 0)
        return ((v >> self._bit) & 1) == 1

# ----- setup ------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: FuturaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    # souhrny + antiradon
    entities.append(AnyErrorBinary(coordinator, entry))
    entities.append(AnyWarningBinary(coordinator, entry))
    entities.append(AntiRadonBinary(coordinator, entry))

    # chyby (0..12)
    for key_en, bit, name_cz in ERROR_BITS:
        entities.append(BitBinary(coordinator, entry, key_en, name_cz, source="errors_bits_raw", bit=bit))

    # varování (0..31)
    for bit in range(32):
        key_en = f"warning_bit_{bit}"
        name_cz = WARNING_NAMES_CZ.get(bit, f"Varování – bit {bit}")
        entities.append(BitBinary(coordinator, entry, key_en, name_cz, source="warnings_bits_raw", bit=bit))

    async_add_entities(entities)
