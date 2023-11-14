from enum import Enum, auto
from collections import defaultdict
import ctypes, binascii

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

def get_machine_type_from_model_name(model_name):
    for machine_type in MachineType:
        # Convert the enum member to string and check if it's in the model name
        if machine_type.name in model_name.upper():
            return machine_type
    return None

def supported(name):
    return get_machine_type_from_model_name(name)

class CoffeeMachine:
    def __init__(self, model: MachineType, name: str = 'default', serial: str = 'default'):
        self.model = model
        self.name = name
        self.serial = serial
        self.configurations = self.default_configurations()

    def default_configurations(self):
        # Default configurations for a generic coffee machine
        return {
            'temprature_control': False,
        }

    def __repr__(self) -> dict:
        return f'Name: {self.name}\n' \
               f'Serial: {self.serial}'

class ExpertMachine(CoffeeMachine):
    def __init__(self, name: str, serial: str):
        super().__init__(MachineType.EXPERT, name, serial)

    def default_configurations(self):
        configurations = super().default_configurations()
        configurations.update({
            'temprature_control': True,
        })
        return configurations

class ProdigoMachine(CoffeeMachine):
    def __init__(self, name: str, serial: str):
        super().__init__(MachineType.PRODIGIO, name, serial)

    def default_configurations(self):
        configurations = super().default_configurations()
        # Default configurations for a generic coffee machine
        return {
            'placeholder': 1.0,
        }

class BlueMachine(CoffeeMachine):
    def __init__(self, name: str, serial: str):
        super().__init__(MachineType.PRODIGIO, name, serial)

    def default_configurations(self):
        # Default configurations for a generic coffee machine
        return {
            'placeholder': 1.0,
        }

class CoffeeMachineFactory:
    @staticmethod
    def get_coffee_machine(model_name: str, serial: str) -> CoffeeMachine:
        model = get_machine_type_from_model_name(model_name)
        match model:
            case MachineType.BLUE:
                return BlueMachine(model_name, serial)
            case MachineType.EXPERT:
                return ExpertMachine(model_name, serial)
            case MachineType.PRODIGIO:
                return ProdigoMachine(model_name, serial)
            case _:
                print(f"No specific machine found for model {model_name}. Using default.")
                return CoffeeMachine(model_name)

class ErrorCode(Enum):
    TRAY_FULL = b'2403'
    LID_NOT_CYCLED = b'2412'
    WRONG_COMMAND = b'3603'

def get_error_message(error_code):
    try:
        return ErrorCode(error_code).name.replace('_', ' ').title()
    except ValueError:
        return f"Unknown Error({error_code})"

c_uint8 = ctypes.c_uint8

class Flags_bits( ctypes.LittleEndianStructure ):
     _fields_ = [
                 ("bit0",     c_uint8, 1 ),  # asByte & 1
                 ("bit1",     c_uint8, 1 ),  # asByte & 2
                 ("bit2",     c_uint8, 1 ),  # asByte & 4
                 ("bit3",     c_uint8, 1 ),  # asByte & 8
                 ("bit4",     c_uint8, 1 ),  # asByte & 16
                 ("bit5",     c_uint8, 1 ),  # asByte & 32
                 ("bit6",     c_uint8, 1 ),  # asByte & 64
                 ("bit7",     c_uint8, 1 ),  # asByte & 128
                ]

class Flags( ctypes.Union ):
     _anonymous_ = ("bit",)
     _fields_ = [
                 ("bit",    Flags_bits ),
                 ("asByte", c_uint8    )
                ]

class BaseDecode:
    def __init__(self, name, format_type):
        self.name = name
        self.format_type = format_type

    def decode_data(self, raw_data):
        #val = struct.unpack(self.format_type,raw_data)
        val = raw_data
        if self.format_type == "caps_number":
            res = int.from_bytes(val,byteorder='big')
        elif self.format_type == "pairing_status":
            res = val != bytearray(b'\x00')
        elif self.format_type == "water_hardness":
            res = int.from_bytes(val[2:3],byteorder='big')
        elif self.format_type == "slider":
            res = binascii.hexlify(val)
            if (res) == b'00':
                res = 'open'
                #res = 'on'
            elif (res) == b'02':
                res = 'closed'
                #res = 'off'
            else :
                res = "N/A"
        elif self.format_type == "command_response":
            error = val[0] & 0x40
            _0x = binascii.hexlify(val)
            if not error:
                return {self.name:'success'}
            length = val[2]
            return {self.name:get_error_message(_0x[6:6+length*2])}

        elif self.format_type == "state":
            BYTE0 = Flags()
            BYTE1 = Flags()
            BYTE2 = Flags()
            BYTE3 = Flags()

            BYTE0.asByte = val[0]
            BYTE1.asByte = val[1]
            # TODO error counter
            BYTE2.asByte = val[2]
            BYTE3.asByte = val[3]
            try:
                descaling_counter = int.from_bytes(val[6:9],byteorder='big')
            except:
                #_LOGGER.debug("can't get descaling counter")
                descaling_counter = 0
            return {"water_is_empty":BYTE0.bit0,
                    "descaling_needed":BYTE0.bit2,
                    "capsule_mechanism_jammed":BYTE0.bit4,
                    "always_1":BYTE0.bit6,
                    "water_temp_low":BYTE1.bit0,
                    "awake":BYTE1.bit1,
                    "water_engadged":BYTE1.bit2,
                    "sleeping":BYTE1.bit3,
                    "tray_sensor_during_brewing":BYTE1.bit4,
                    "tray_open_tray_sensor_full":BYTE1.bit6,
                    "capsule_engaged":BYTE1.bit7,
                    "Fault":BYTE3.bit5,
                    "descaling_counter":descaling_counter
                    }
        else:
            #_LOGGER.debug("state_decoder else")
            res = val
        return {self.name:res}



if __name__ == '__main__':
    machine = CoffeeMachineFactory.get_coffee_machine('Expert&Milk_12345ABCD', '0123456789123')

    print(machine)

    print(BrewType.is_brew_applicable_for_machine(BrewType.AMERICANO, machine.model))

    print(machine.configurations['temprature_control'])