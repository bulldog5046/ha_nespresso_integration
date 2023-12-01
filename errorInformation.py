from enum import Enum

class ErrorCategory(Enum):
    DEVICE_ERROR_NONE = 0
    DEVICE_ERROR_POWER_LINE = 1
    DEVICE_ERROR_MMI = 2
    DEVICE_ERROR_MAIN_SYSTEM = 3
    DEVICE_ERROR_SENSOR = 4
    DEVICE_ERROR_ACTUATOR = 5
    DEVICE_ERROR_OTHER = 6

    @staticmethod
    def from_byte(b):
        # Right shift by 4 bits to get the category from the upper nibble
        category_index = (b >> 4) & 0x0F
        return ErrorCategory(category_index)

class ErrorInformation:
    def __init__(self, error_number, error_category, error_sub_code):
        self.error_number = error_number
        self.error_category = error_category
        self.error_sub_code = error_sub_code

    def __str__(self):
        return f"Error Number: {self.error_number}, Error Category: {self.error_category.name}, Error Sub-Code: {self.error_sub_code}"

def to_error_information(byte_data):
    error_number = byte_data[0]  # The error number is the first byte
    error_category = ErrorCategory.from_byte(byte_data[1])  # The second byte contains the error category
    error_sub_code = int.from_bytes(byte_data[2:4], 'big')  # The third and fourth bytes represent the error sub-code
    return ErrorInformation(error_number, error_category, error_sub_code)

if __name__ == '__main__':
    # Test with the provided byte array
    byte_data = bytearray(b'\x010&\x03\x04C\x97\xa4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    error_info = to_error_information(byte_data)
    print(error_info)
