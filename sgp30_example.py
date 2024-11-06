import time
import board
import busio
import digitalio
import adafruit_sgp30
import adafruit_rfm9x


######### CO2 #########
#Gas readout
""" Example for using the SGP30 with CircuitPython and the Adafruit library"""
i2c = busio.I2C(board.SCL, board.SDA)

# Create library object on our I2C port
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

sgp30.set_iaq_baseline(0x8973, 0x8AAE)
sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)

# Initate time count
elapsed_sec = 0

###### RADIO ########
# set the time interval (seconds) for sending packets
transmit_interval = 1

# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz.

# Define pins connected to the chip.
CS = digitalio.DigitalInOut(board.RFM9X_CS)
RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# You can however adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23


# send a broadcast mesage
print("Sending packets...")
# initialize flag and timer
while True:
    print("eCO2 = %d ppm \t TVOC = %d ppb" % (sgp30.eCO2, sgp30.TVOC))
    elapsed_sec += transmit_interval
    # send a broadcast mesage
    rfm9x.send(bytes("time = %d seconds \t eCO2 = %d ppm \t TVOC = %d ppb" % (elapsed_sec, sgp30.eCO2, sgp30.TVOC), "UTF-8"))
    time.sleep(transmit_interval)
