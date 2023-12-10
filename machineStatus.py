try:
    from enums import WaterIsEmpty, DescalingNeeded, CapsuleMechanismJammed, SliderOpen, WaterIsFresh, WaterHardness, MachineState
except ImportError:
    from .enums import WaterIsEmpty, DescalingNeeded, CapsuleMechanismJammed, SliderOpen, WaterIsFresh, WaterHardness, MachineState

class MachineStatus:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    def select_bits(self, start_bit, length):
        value = int.from_bytes(self.raw_data)
        value >>= (len(self.raw_data) * 8 - start_bit - length)
        mask = (1 << length) - 1
        return value & mask

    def decode_water_is_empty(self):
        return WaterIsEmpty(self.raw_data[0] & 1)

    def decode_descaling_needed(self):
        return DescalingNeeded((self.raw_data[0] >> 2) & 1)

    def decode_capsule_mechanism_jammed(self):
        return CapsuleMechanismJammed((self.raw_data[0] >> 4) & 1)
    
    def decode_awake(self): #TODO: This isn't right.
        return bool((self.raw_data[0] >> 2) & 1)
    
    def decode_water_fresh(self):
        return WaterIsFresh(self.raw_data[1] & 1)

    # Add more decode methods here for each status...

    def decode(self):
        return {
            "water_is_empty": self.decode_water_is_empty().name,
            "descaling_needed": self.decode_descaling_needed().name,
            "capsule_mechanism_jammed": self.decode_capsule_mechanism_jammed().name,
            "water_fresh": self.decode_water_fresh().name,
            "state": MachineState(self.select_bits(12, 4)).name,
            "descaling_counter": int.from_bytes(self.raw_data[6:9])
            
        }
    
class BaseDecode:
    def __init__(self, name, format_type):
        self.name = name
        self.format_type = format_type

    def decode_data(self, raw_data):
        if self.format_type == "state":
            status_decoder = MachineStatus(raw_data)
            return status_decoder.decode()
        elif self.format_type == "caps_number":
            return {self.name: int.from_bytes(raw_data, byteorder='big')}
        elif self.format_type == "pairing_status":
            return {self.name: raw_data != bytearray(b'\x00')}
        elif self.format_type == "water_hardness":
            return {self.name: WaterHardness(int.from_bytes(raw_data[2:3])).name}
        elif self.format_type == "slider":
            a = (raw_data[0] >> 1) & 1
            return {self.name: SliderOpen((raw_data[0] >> 1) & 1).name}

        # Default case
        return {self.name: raw_data}

if __name__ == '__main__':
    state_bytes = bytearray(b'A\x84\x7f\xec\x00\x00\xff\xff')
    caps_bytes = bytearray(b'\xff\xff')
    slider_bytes = bytearray(b'\x00')
    water_hardness_bytes = bytearray(b'\x02\x1c\x04\x00')
    decoder = BaseDecode("state", "state")
    decoded_data = decoder.decode_data(state_bytes)
    print(decoded_data)

    # "water_is_empty":BYTE0.bit0,
    #                 "descaling_needed":BYTE0.bit2,
    #                 "capsule_mechanism_jammed":BYTE0.bit4,
    #                 "always_1":BYTE0.bit6,
    #                 "water_temp_low":BYTE1.bit0,
    #                 "awake":BYTE1.bit1,
    #                 "water_engadged":BYTE1.bit2,
    #                 "sleeping":BYTE1.bit3,
    #                 "tray_sensor_during_brewing":BYTE1.bit4,
    #                 "tray_open_tray_sensor_full":BYTE1.bit6,
    #                 "capsule_engaged":BYTE1.bit7,
    #                 "Fault":BYTE3.bit5,
    #                 "descaling_counter":descaling_counter