import time
import board
import busio
import digitalio
import adafruit_rfm9x
import adafruit_mcp9600
import adafruit_scd4x

# set the time interval (seconds) for sending packets
transmit_interval = 1

# Initate time count
elapsed_sec = 0

######### CO2 #########
#Gas readout
i2c = board.I2C()  # uses board.SCL and board.SDA
scd4x = adafruit_scd4x.SCD4X(i2c)

scd4x.start_periodic_measurement()

######### Temperature #########
# Initialize I2C for MCP9600
i2c = busio.I2C(board.SCL, board.SDA)
mcp = adafruit_mcp9600.MCP9600(i2c)

###### RADIO ########
# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in MHz.

# Define pins connected to the chip.
CS = digitalio.DigitalInOut(board.D5)
RESET = digitalio.DigitalInOut(board.D6)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Initialize RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Set the transmission power (in dB).  You can however adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23

###### Record and Send CO2 and Temp Data ########
# Send temperature data continuously
print("Sending packets...")
while True:
    # Get temperature from MCP9600 sensor
    print("CO2 = %d ppm \t Temperature = %d °C" % (scd4x.CO2, mcp.temperature))
    elapsed_sec += transmit_interval
    # send a broadcast mesage
    rfm9x.send(bytes("time = %d seconds \t CO2 = %d ppm \t Temperature = %d °C" % (elapsed_sec, scd4x.CO2, mcp.temperature), "UTF-8"))
    time.sleep(transmit_interval)
