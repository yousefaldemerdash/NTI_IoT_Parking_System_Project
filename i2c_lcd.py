import time
from lcd_api import LcdApi

MASK_RS = 0x01
MASK_RW = 0x02
MASK_E  = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4

class I2cLcd(LcdApi):
    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines if num_lines <= 4 else 4
        self.num_columns = num_columns if num_columns <= 40 else 40
        self.cursor_x = 0
        self.cursor_y = 0
        self.backlight = True
        time.sleep_ms(20)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(5)
        self.hal_write_init_nibble(0x03)
        time.sleep_ms(1)
        self.hal_write_init_nibble(0x03)
        self.hal_write_init_nibble(0x02)
        cmd = self.LCD_MOVE_2LINE if num_lines > 1 else 0
        self.hal_write_command(self.LCD_ENTRY_MODE | cmd)
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)
        self.clear()

    def hal_write_init_nibble(self, nibble):
        byte = (nibble << SHIFT_DATA) | (1 << SHIFT_BACKLIGHT)
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))

    def hal_backlight_on(self):
        self.backlight = True

    def hal_backlight_off(self):
        self.backlight = False

    def hal_write_command(self, cmd):
        self.hal_write_byte(cmd, 0)

    def hal_write_data(self, data):
        self.hal_write_byte(data, MASK_RS)

    def hal_write_byte(self, data, mode):
        bit_bl = (1 << SHIFT_BACKLIGHT) if self.backlight else 0
        high = (data & 0xF0) | mode | bit_bl
        low = ((data << 4) & 0xF0) | mode | bit_bl
        self.i2c.writeto(self.i2c_addr, bytes([high | MASK_E, high, low | MASK_E, low]))