from enum import Enum

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

def default_machine_state_from(b):
    return MachineState(b if b in range(16) else 16).name

def get_boolean(byte_array, bit_position):
    byte_index = bit_position // 8
    bit_index = bit_position % 8
    return (byte_array[byte_index] & (1 << bit_index)) != 0

def select_bits(byte_array, start_bit, length):
    value = int.from_bytes(byte_array, 'big')
    value >>= (len(byte_array) * 8 - start_bit - length)
    mask = (1 << length) - 1
    return value & mask

def from_byte_array(byte_array):
    machine_state = MachineState(select_bits(byte_array, 12, 4))  # Adjusted to 4 bits based on the enum
    #capsule_stock_low = get_boolean(byte_array, 16) Seems incorrect. Reversed from decompiled code.
    capsule_stock_counter = select_bits(byte_array, 17, 10)  # 10 bits for the counter
    programmed_brewing_active = get_boolean(byte_array, 27)
    programmed_brew_event_counter = select_bits(byte_array, 28, 2)
    capsule_stock_event_counter = select_bits(byte_array, 30, 2)
    blocked_machine_event_counter = select_bits(byte_array, 32, 2)
    #slider_open = not get_boolean(byte_array, 46) # Seems incorrect. Reversed from decompiled code.
    #obstacle_detected = get_boolean(byte_array, 47) # Seems incorrect. Reversed from decompiled code.

    return {
        'MachineState': machine_state.name,
        #'CapsuleStockLow': capsule_stock_low,
        'CapsuleStockCounter': capsule_stock_counter,
        'ProgrammedBrewingActive': programmed_brewing_active,
        'ProgrammedBrewEventCounter': programmed_brew_event_counter,
        'CapsuleStockEventCounter': capsule_stock_event_counter,
        'BlockedMachineEventCounter': blocked_machine_event_counter,
        #'SliderOpen': slider_open,
        #'ObstacleDetected': obstacle_detected
    }

if __name__ == '__main__':
    # Test with the byte array
    byte_array = bytearray(b'@\t\x0b\xe0\xc0\x00\xff\xff')
    status = from_byte_array(byte_array)
    for key, value in status.items():
        print(f"{key}: {value}")

