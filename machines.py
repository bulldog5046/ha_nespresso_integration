import ctypes, binascii
try:
    from enums import MachineType, BrewType, ErrorCode, Temprature
except ImportError:
    from .enums import MachineType, BrewType, ErrorCode, Temprature

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
        self.fw_version = None
        self.hw_version = None
        self.configurations = self.default_configurations()

    def default_configurations(self):
        # Default configurations for a generic coffee machine
        return {
            'temprature_control': False,
            'custom_recipes': False
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
            'custom_recipes': True
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
            res = val
        return {self.name:res}
    
def decode_machine_information(byte_array):
    """
    Decodes a bytearray into the MachineInformation properties.

    Parameters:
    byte_array (bytearray): A bytearray containing the machine information.

    Returns:
    dict: A dictionary containing the decoded properties.
    """

    def bytes_to_int(byte_pair):
        """Converts a pair of bytes to an integer."""
        return int.from_bytes(byte_pair, byteorder='big')

    def bytes_to_mac_address(byte_array):
        """Converts a bytearray to a MAC address string."""
        return ':'.join('{:02x}'.format(byte) for byte in byte_array)

    # Extract bytes for each property
    hardware_version_bytes = byte_array[0:2]
    bootloader_version_bytes = byte_array[2:4]
    main_firmware_version_bytes = byte_array[4:6]
    connectivity_firmware_version_bytes = byte_array[6:8]
    device_address_bytes = byte_array[8:]

    # Decode each property
    hardware_version = bytes_to_int(hardware_version_bytes)
    bootloader_version = bytes_to_int(bootloader_version_bytes)
    main_firmware_version = bytes_to_int(main_firmware_version_bytes)
    connectivity_firmware_version = bytes_to_int(connectivity_firmware_version_bytes)
    device_address = bytes_to_mac_address(device_address_bytes)

    # Returning the decoded properties in a dictionary
    return {
        "Hardware Version": VersionInformation(hardware_version).format_standard_version(),
        "Bootloader Version": VersionInformation(bootloader_version).format_standard_version(),
        "Main Firmware Version": VersionInformation(main_firmware_version).format_standard_version(),
        "Connectivity Firmware Version": ConnectivityFirmwareVersion(connectivity_firmware_version).format_standard_version(),
        "Device Address": device_address
    }

def decode_pairing_key_state(byte_buffer):
    """
    Decodes the pairing key state from a given byte buffer.

    Parameters:
    byte_buffer (bytearray): A bytearray containing the pairing key state.

    Returns:
    str: The decoded pairing key state as a string.
    """
    pairing_key_state_index = 0
    pairing_key_state_byte = byte_buffer[pairing_key_state_index]

    if pairing_key_state_byte in [0, 1]:
        return "ABSENT"
    elif pairing_key_state_byte == 2:
        return "PRESENT"
    elif pairing_key_state_byte == 3:
        return "UNDEFINED"
    else:
        raise ValueError(f"Undefined PairingKeyState: {pairing_key_state_byte}")
    
class VersionInformation:
    MAJOR_VERSION_MULTIPLIER = 100

    def __init__(self, version):
        self.version = version

    def get_major_version(self):
        return self.version // self.MAJOR_VERSION_MULTIPLIER

    def get_minor_version(self):
        return self.version % self.MAJOR_VERSION_MULTIPLIER

    def is_available(self):
        return self.version > 0

    def format_standard_version(self):
        if not self.is_available():
            return None
        return "{}.{}".format(self.get_major_version(), self.get_minor_version())

class ConnectivityFirmwareVersion:
    MAJOR_VERSION_MULTIPLIER = 10000
    MINOR_VERSION_MULTIPLIER = 100

    def __init__(self, version):
        self.version = version

    def get_build_version(self):
        return self.version % self.MINOR_VERSION_MULTIPLIER

    def get_major_version(self):
        return self.version // self.MAJOR_VERSION_MULTIPLIER

    def get_minor_version(self):
        return (self.version % self.MAJOR_VERSION_MULTIPLIER) // self.MINOR_VERSION_MULTIPLIER

    def is_available(self):
        return self.version > 0

    def format_standard_version(self):
        if not self.is_available():
            return None
        return "{}.{}.{}".format(
            self.get_major_version(),
            self.get_minor_version(),
            self.get_build_version()
        )



if __name__ == '__main__':
    machine = CoffeeMachineFactory.get_coffee_machine('Expert&Milk_12345ABCD', '0123456789123')

    print(machine)

    print(BrewType.is_brew_applicable_for_machine(BrewType.AMERICANO, machine.model))

    print(machine.configurations['temprature_control'])