from enum import Enum

class ResponseCode(Enum):
    ACK = 32
    CONDITIONS_NOT_FULFILLED = 36
    OUT_OF_RANGE = 54
    INVALID = 255

    @staticmethod
    def from_id(id):
        for code in ResponseCode:
            if code.value == id:
                return code
        return ResponseCode.INVALID

class CommandResponse(Enum):
    DONE = "Done"
    OUT_OF_RANGE = "Out of Range"
    UNDEFINED = "Undefined"
    INVALID_STATE = "Invalid State"
    CAPSULE_CONTAINER_FULL = "Capsule Container Full"
    OBSTACLE_DETECTED = "Obstacle Detected"
    DESCALE_ON = "Descale On"
    LAST_ACTION_NOT_FINISHED = "Last Action Not Finished"
    NOT_ABORTABLE_ACTION = "Not Abortable Action"
    SLIDER_OPEN = "Slider Open"
    NO_PROGRAMMED_BREW_ACTIVE = "No Programmed Brew Active"
    PUMP_RUNNING = "Pump Running"
    MOTOR_RUNNING = "Motor Running"
    SLIDER_NOT_BEEN_OPENED = "Slider Not Been Opened"

def from_byte_buffer(byte_buffer):
    copy_of_range = byte_buffer[3:19]
    response_code = ResponseCode.from_id(copy_of_range[0])
    
    if response_code == ResponseCode.ACK:
        return CommandResponse.DONE
    elif response_code == ResponseCode.OUT_OF_RANGE:
        return CommandResponse.OUT_OF_RANGE
    elif response_code == ResponseCode.CONDITIONS_NOT_FULFILLED:
        return from_condition_not_full_filled(copy_of_range[1])
    else:
        return CommandResponse.UNDEFINED

def from_condition_not_full_filled(b):
    if b == 1 or b == 2:
        return CommandResponse.INVALID_STATE
    elif b == 3:
        return CommandResponse.CAPSULE_CONTAINER_FULL
    elif b == 4:
        return CommandResponse.OBSTACLE_DETECTED
    elif b == 5:
        return CommandResponse.DESCALE_ON
    elif b == 6:
        return CommandResponse.LAST_ACTION_NOT_FINISHED
    elif b == 7:
        return CommandResponse.NOT_ABORTABLE_ACTION
    elif b == 8:
        return CommandResponse.SLIDER_OPEN
    elif b == 9:
        return CommandResponse.NO_PROGRAMMED_BREW_ACTIVE
    elif b == 16:
        return CommandResponse.PUMP_RUNNING
    elif b == 17:
        return CommandResponse.MOTOR_RUNNING
    elif b == 18:
        return CommandResponse.SLIDER_NOT_BEEN_OPENED
    else:
        return CommandResponse.UNDEFINED
    
if __name__ == '__main__':
    # Test byte array
    byte_data = bytearray(b'\xc3\x05\x02$\x12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    response = from_byte_buffer(byte_data)
    print(response.value)  # This should print the human-readable error string