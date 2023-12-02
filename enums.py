from enum import Enum, auto
from collections import defaultdict

class MachineType(Enum):
    EXPERT = auto()
    VTP2 = auto()
    BLUE = auto()
    PRODIGIO = auto()

class BrewType(Enum):
    RISTRETTO = '00'
    ESPRESSO = '01'
    LUNGO = '02'
    HOT_WATER = '04'
    AMERICANO = '05'

    def is_brew_applicable_for_machine(brew, machine_type: MachineType) -> bool:
        return brew in APPLICABLE_BREW[machine_type]

class Temprature(Enum):
    LOW = '01'
    MEDIUM = '00'
    HIGH = '02'

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