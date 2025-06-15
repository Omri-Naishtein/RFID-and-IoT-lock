from omri_lock import SmartLock
from time import sleep

lock = SmartLock(
	wifi_ssid="Omri's hotspot",
	wifi_password="SECRET",
	aio_username="OmriTL",
	aio_key="SECRET",
	feed_name="lcd-rfid",
	allowed_uids=[[67, 32, 251, 27, 131], [82, 215, 186, 16, 47]], #allowed UIDs, list for more then one UID
	button_pin=15
)

def uid_match(uid, allowed): #helper function to match UID
	return list(uid) in allowed

def main_loop(): #main function
	lock.lcd_display("Locked", "Scan card...")
	last_state = lock.state
	while True:
		try:
			lock.client.check_msg() #check for adafruit msg
		except:
			pass

		if lock.state != last_state:
			lock.set_servo(lock.state == "lock")
			lock.display_switch_state()
			last_state = lock.state

		if lock.state == "unlock":
			sleep(1)
			continue

		if not lock.button.value(): #check button press
			lock.unlock_sequence()
			last_state = "lock"
			continue

		uid = lock.read_rfid_uid() #check rfid
		if uid:
			if uid_match(uid, lock.allowed_uids):
				lock.unlock_sequence()
				last_state = "lock"
			else:
				lock.lcd_display("Access Denied")
				sleep(2)
				lock.lcd_display("Locked", "Scan card...")

		sleep(0.1)

try:
	main_loop()
finally:
	lock.lcd_display("Program Stopped")