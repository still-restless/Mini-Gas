import time
import board
import busio
import digitalio
import adafruit_rfm9x
import adafruit_mcp9600

# Initialize I2C for MCP9600
i2c = busio.I2C(board.SCL, board.SDA)
mcp = adafruit_mcp9600.MCP9600(i2c)

# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in MHz.

# Define pins connected to the chip.
CS = digitalio.DigitalInOut(board.RFM9X_CS)
RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Initialize RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Set the transmission power (in dB).
rfm9x.tx_power = 23

# Initialize the LED pin
LED_PIN = board.D13  # Change to any other pin if needed
led = digitalio.DigitalInOut(LED_PIN)
led.direction = digitalio.Direction.OUTPUT

# Store the time of the last LED blink
last_blink_time = time.monotonic()

# Send temperature data continuously
while True:
    # Get temperature from MCP9600 sensor
    temperature = mcp.temperature
    print(f"Measured temperature: {temperature:.2f} °C")

    # Send temperature data via LoRa
    message = f"{temperature:.2f}"
    rfm9x.send(bytes(message, 'UTF-8'))
    print(f"Sent: {message}")

    # LED blinking every second (non-blocking)
    current_time = time.monotonic()
    if current_time - last_blink_time >= 1:
        led.value = not led.value  # Toggle LED state
        last_blink_time = current_time  # Update the last blink time

    # Maintain a 1-second delay for stable data transmission
    time.sleep(1)
