from enum import Enum, auto
from collections import defaultdict

class MachineState(Enum):
    RESET = 0
    HEAT_UP = 1
    READY = 2
    DESCALING_READY = 3
    BREWING = 4
    ADVANCED_SELECTION_MENU = 5
    DESCALING = 6
    STEAM_OUT = 7
    ERROR = 8
    POWER_SAVE = 9
    OVER_HEAT = 10
    DIAGNOSTIC_MODE = 11
    BLE_SETTINGS = 12
    FACTORY_RESET = 13
    WATER_HARDNESS_SETTINGS = 14
    STAND_BY_DELAY_SETTINGS = 15
    UNKNOWN = 16

class VenusMachineState(Enum):
    FACTORY_RESET = 0
    HEAT_UP = 1
    READY = 2
    DESCALING_READY = 3
    BREWING = 4
    CLEANING = 5
    DESCALING = 6
    STEAM_OUT = 7
    ERROR = 8
    POWER_SAVE = 9
    OVER_HEAT = 10
    DIAGNOSTIC_MODE = 11
    STANDBY = 12
    UPDATING = 13
    RINSING = 14
    UNKNOWN = 16
    CAPSULE_READING = 17
    DESCALC_SEQUENCE_DECODING = 18
    TANK_EMPTY = 19
    DESCALING_PAUSED = 20
    INITIALIZATION = 21
    RINSING_READY = 22

class WaterIsEmpty(Enum):
    NOT_EMPTY = 0
    EMPTY = 1

class WaterIsFresh(Enum):
    NOT_FRESH = 0
    FRESH = 1

class DescalingNeeded(Enum):
    NOT_NEEDED = 0
    NEEDED = 1

class CapsuleMechanismJammed(Enum):
    NOT_JAMMED = 0
    JAMMED = 1

class SliderOpen(Enum):
    OPEN = 0
    CLOSED = 1

class WaterHardness(Enum):
    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4

class MachineType(Enum):
    EXPERT = auto()
    VTP2 = auto()
    BLUE = auto()
    PRODIGIO = auto()
    VENUS = auto()
    DV2 = auto()

class BrewType(Enum):
    RISTRETTO = 0
    ESPRESSO = 1
    LUNGO = 2
    HOT_WATER = 4
    AMERICANO = 5
    CUSTOM = 7

    def is_brew_applicable_for_machine(brew, machine_type: MachineType) -> bool:
        return brew in APPLICABLE_BREW[machine_type]

class Temprature(Enum):
    LOW = 1
    MEDIUM = 0
    HIGH = 2

class Ingredient(Enum):
    COFFEE = 1
    WATER = 2

class CupSizeType(Enum):
    RISTRETTO = auto()
    ESPRESSO = auto()
    LUNGO = auto()
    AMERICANO_COFFEE = auto()
    AMERICANO_WATER = auto()
    AMERICANO_XL_COFFEE = auto()
    AMERICANO_XL_WATER = auto()
    HOT_WATER = auto()
    HOT_WATER_VTP2 = auto()

    def is_cup_size_applicable_for_machine(cup_size, machine_type: MachineType) -> bool:
        return cup_size in APPLICABLE_CUP_SIZES[machine_type]
    
class ErrorCode(Enum):
    TRAY_FULL = b'2403'
    LID_NOT_CYCLED = b'2412'
    WRONG_COMMAND = b'3603'
    
APPLICABLE_CUP_SIZES = defaultdict(list)
APPLICABLE_CUP_SIZES[MachineType.EXPERT] = [
    CupSizeType.RISTRETTO, CupSizeType.ESPRESSO, CupSizeType.LUNGO,
    CupSizeType.HOT_WATER, CupSizeType.AMERICANO_COFFEE, CupSizeType.AMERICANO_WATER
]
APPLICABLE_CUP_SIZES[MachineType.VTP2] = [
    CupSizeType.ESPRESSO, CupSizeType.LUNGO, CupSizeType.HOT_WATER_VTP2,
    CupSizeType.AMERICANO_COFFEE, CupSizeType.AMERICANO_WATER,
    CupSizeType.AMERICANO_XL_COFFEE, CupSizeType.AMERICANO_XL_WATER
]
APPLICABLE_CUP_SIZES[MachineType.BLUE] = [
    CupSizeType.RISTRETTO, CupSizeType.ESPRESSO, CupSizeType.LUNGO
]

APPLICABLE_BREW = defaultdict(list)
APPLICABLE_BREW[MachineType.EXPERT] = [
    BrewType.RISTRETTO, BrewType.ESPRESSO, BrewType.LUNGO,
    BrewType.HOT_WATER, BrewType.AMERICANO
]
APPLICABLE_BREW[MachineType.PRODIGIO] = [
    BrewType.RISTRETTO, BrewType.ESPRESSO, BrewType.LUNGO,
]
APPLICABLE_BREW[MachineType.BLUE] = [
    BrewType.RISTRETTO, BrewType.ESPRESSO, BrewType.LUNGO
]