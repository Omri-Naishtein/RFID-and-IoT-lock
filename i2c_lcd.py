from lcd_api import LcdApi
from machine import I2C
import time

MASK_RS = 0x01
MASK_RW = 0x02
MASK_E = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4

class I2cLcd(LcdApi):
	def __init__(self, i2c: I2C, i2c_addr: int, num_lines: int, num_columns: int):
		self.i2c = i2c
		self.i2c_addr = i2c_addr
		self.i2c.writeto(self.i2c_addr, bytes([0]))
		time.sleep(0.02)
		self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
		time.sleep(0.005)
		self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
		time.sleep(0.001)
		self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
		time.sleep(0.001)
		self.hal_write_init_nibble(self.LCD_FUNCTION)
		time.sleep(0.001)
		super().__init__(num_lines, num_columns)
		cmd = self.LCD_FUNCTION
		if num_lines > 1:
			cmd |= self.LCD_FUNCTION_2LINES
		self.hal_write_command(cmd)

	def hal_write_init_nibble(self, nibble):
		byte = ((nibble >> 4) & 0x0F) << SHIFT_DATA
		self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
		self.i2c.writeto(self.i2c_addr, bytes([byte]))

	def hal_backlight_on(self):
		self.i2c.writeto(self.i2c_addr, bytes([1 << SHIFT_BACKLIGHT]))

	def hal_backlight_off(self):
		self.i2c.writeto(self.i2c_addr, bytes([0]))

	def hal_sleep_us(self, usecs):
		time.sleep_us(usecs)

	def hal_write_command(self, cmd):
		self.hal_write_byte(cmd, is_data=False)
		if cmd <= 3:
			time.sleep(0.005)

	def hal_write_data(self, data):
		self.hal_write_byte(data, is_data=True)

	def hal_write_byte(self, byte, is_data):
		rs_bit = MASK_RS if is_data else 0
		upper = rs_bit | (self.backlight << SHIFT_BACKLIGHT) | ((byte >> 4 & 0x0F) << SHIFT_DATA)
		lower = rs_bit | (self.backlight << SHIFT_BACKLIGHT) | ((byte & 0x0F) << SHIFT_DATA)
		self.i2c.writeto(self.i2c_addr, bytes([upper | MASK_E]))
		self.i2c.writeto(self.i2c_addr, bytes([upper]))
		self.i2c.writeto(self.i2c_addr, bytes([lower | MASK_E]))
		self.i2c.writeto(self.i2c_addr, bytes([lower]))

