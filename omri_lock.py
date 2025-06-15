class SmartLock: #defining the lock and all the necessary stuff - wifi pins and such
	def __init__(self, wifi_ssid, wifi_password, aio_username, aio_key, feed_name, allowed_uids, servo_pin=18, lcd_addr=0x27, button_pin=15):
		self.wifi_ssid = wifi_ssid
		self.wifi_password = wifi_password
		self.aio_username = aio_username
		self.aio_key = aio_key
		self.feed_name = feed_name
		self.allowed_uids = allowed_uids
		self.servo_pin = servo_pin
		self.button_pin = button_pin
		self.state = "unlock"
		self.last_lcd = ""
		self.mqtt_paused = False

		self._init_lcd(lcd_addr)
		self.lcd_display("Connecting", "to WiFi...")
		self._connect_wifi()
		self.lcd_display("WiFi", "Connected")

		self._init_servo()
		self._init_rfid()
		self._init_button()

		self.lcd_display("Connecting", "to MQTT...")
		self._connect_mqtt()
		self.lcd_display("MQTT", "Connected")

		self.lcd_display("Reading", "feed value...")
		self._get_last_feed_value()
		self.set_servo(self.state == "lock")
		self.display_switch_state()

	def display_switch_state(self): #display the state of the switch in adafruit on lcd
		status = "locked" if self.state in ("lock", "on", "locked") else "unlocked"
		self.lcd_display("Switch state:", status)

	def _connect_wifi(self): #connect to wifi with WLAN
		import network
		from time import sleep
		wlan = network.WLAN(network.STA_IF)
		wlan.active(True)
		wlan.connect(self.wifi_ssid, self.wifi_password)
		attempts = 0
		while not wlan.isconnected():
			if attempts > 20:
				self.lcd_display("WiFi Error", "No Connection")
				raise RuntimeError("WiFi connection failed")
			sleep(0.5)
			attempts += 1

	def _init_lcd(self, addr):#define lcd
		from machine import I2C, Pin
		from i2c_lcd import I2cLcd
		i2c = I2C(0, scl=Pin(19), sda=Pin(21), freq=100000)
		self.lcd = I2cLcd(i2c, addr, 2, 16)

	def _init_servo(self):#define servo
		from machine import Pin, PWM
		self.servo = PWM(Pin(self.servo_pin), freq=50)

	def _init_rfid(self):#define RFID
		from mfrc522 import MFRC522
		self.rfid = MFRC522(sck=14, mosi=13, miso=12, rst=4, cs=5)

	def _init_button(self): #define button
		from machine import Pin
		self.button = Pin(self.button_pin, Pin.IN, Pin.PULL_UP)

	def _connect_mqtt(self):#connect to mqtt
		import ubinascii
		import machine
		from umqtt.simple import MQTTClient
		client_id = ubinascii.hexlify(machine.unique_id())
		self.client = MQTTClient(client_id, "io.adafruit.com", user=self.aio_username, password=self.aio_key, ssl=False)
		self.client.set_callback(self._mqtt_callback)
		try:
			self.client.connect()
			self.client.subscribe(f"{self.aio_username}/feeds/{self.feed_name}")
		except OSError:
			self.lcd_display("MQTT Error", "Conn Failed")
			raise

	def _mqtt_callback(self, topic, msg):#gets switch state from adafruit when esp is online
		if self.mqtt_paused:
			return
		s = msg.decode().strip().lower()
		if s in ("1", "on", "true", "lock", "locked"):
			self.state = "lock"
		elif s in ("0", "off", "false", "unlock", "unlocked"):
			self.state = "unlock"

	def _get_last_feed_value(self):#gets switch state when esp was offline
		try:
			import urequests
			url = f"https://io.adafruit.com/api/v2/{self.aio_username}/feeds/{self.feed_name}/data/last"
			headers = {"X-AIO-Key": self.aio_key}
			resp = urequests.get(url, headers=headers)
			if resp.status_code == 200:
				val = resp.json().get("value", "").strip().lower()
				if val in ("1", "on", "true", "lock", "locked"):
					self.state = "lock"
				elif val in ("0", "off", "false", "unlock", "unlocked"):
					self.state = "unlock"
			else:
				self.lcd_display("Feed Error", "Bad Response")
			resp.close()
		except:
			self.lcd_display("Feed Error", "Request Failed")

	def update_feed(self, value):#updates switch state
		try:
			import urequests
			url = f"https://io.adafruit.com/api/v2/{self.aio_username}/feeds/{self.feed_name}/data"
			headers = {"X-AIO-Key": self.aio_key, "Content-Type": "application/json"}
			urequests.post(url, headers=headers, json={"value": value}).close()
		except:
			self.lcd_display("Feed Error", "Post Failed")

	def read_rfid_uid(self):#reads signal from rfid
		(stat, _) = self.rfid.request(self.rfid.REQIDL)
		if stat != self.rfid.OK:
			return None
		(stat, raw_uid) = self.rfid.anticoll()
		return raw_uid if stat == self.rfid.OK else None

	def set_servo(self, locked):#move servo
		self.servo.duty(120 if locked else 30)

	def lcd_display(self, line1, line2=""):#display easly on lcd
		self.lcd.clear()
		self.lcd.putstr(line1)
		if line2:
			self.lcd.move_to(0, 1)
			self.lcd.putstr(line2)

	def unlock_sequence(self):#action triggered by rfid or button
		from time import sleep
		self.mqtt_paused = True
		self.lcd_display("Access", "Granted")
		self.set_servo(False)
		self.update_feed("unlock")
		sleep(1)
		self.update_feed("lock")
		sleep(2)
		self.set_servo(True)
		self.lcd_display("Locked", "Scan card...")
		self.state = "lock"
		self.mqtt_paused = False