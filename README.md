# ESP32 RFID Smart Lock

This project is a MicroPython-based smart lock system that uses an ESP32, an I2C 1602 LCD display, and an MFRC522 RFID reader. The system authenticates RFID cards and displays status messages on the LCD. It also integrates with Adafruit IO for remote interaction via MQTT.

## Hardware Used

ESP32 Dev Board
MFRC522 RFID module
I2C LCD 1602A
Servo motor (for locking)
Wi-Fi connection (for MQTT with Adafruit IO)

## Credits

`mfrc522.py` based on [wendlers/micropython-mfrc522](https://github.com/wendlers/micropython-mfrc522) by **Christian Wendler** - licensed under MIT.
`i2c_lcd.py` and `lcd_api.py` based on [dhylands/python_lcd](https://github.com/dhylands/python_lcd) by **Dave Hylands** - licensed under MIT.

