import sys
import time
import csv
import os
import threading
from queue import Queue
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont

# Import LoRa modules
import board
import busio
import digitalio
import adafruit_rfm9x

# CSV Configuration
CSV_DELIMITER = ';'
CSV_HEADER = ['Time (s)', 'Temperature (°C)']

# LoRa Configuration
RADIO_FREQ_MHZ = 915.0
CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
rfm9x.tx_power = 23  # Transmission power

TITLE_WINDOW_PLOT = "Real-Time Temperature 1.0"

class MainWindowPlot(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # GUI Layout
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        hbox_temp = QHBoxLayout()
        hbox_file = QHBoxLayout()
        hbox_buttons = QHBoxLayout()

        # Labels
        self.file_label = QLabel("Data file:")
        self.label_data = QLabel("Temperature(°C):")
        self.label_data.setFont(QFont('Arial', 20))

        # File Name Display
        self.file_output = QLineEdit()

        # Temperature Display
        self.output = QLineEdit()
        self.output.setStyleSheet("background: black; color: yellow; font-size:28px;")

        # Graph Configuration
        self.setCentralWidget(widget)
        self.figure = plt.Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        vbox.addLayout(hbox_temp)
        vbox.addWidget(self.canvas)
        vbox.addLayout(hbox_file)
        vbox.addLayout(hbox_buttons)

        # Adding Widgets
        hbox_temp.addWidget(self.label_data)
        hbox_temp.addWidget(self.output)
        hbox_file.addWidget(self.file_label)
        hbox_file.addWidget(self.file_output)

        # Buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.clear_button = QPushButton("Clear Plot")
        self.close_button = QPushButton("Close")

        hbox_buttons.addWidget(self.start_button)
        hbox_buttons.addWidget(self.stop_button)
        hbox_buttons.addWidget(self.clear_button)
        hbox_buttons.addWidget(self.close_button)

        # Button Actions
        self.start_button.clicked.connect(self.start_plot)
        self.stop_button.clicked.connect(self.stop_plot)
        self.clear_button.clicked.connect(self.clear_plot)
        self.close_button.clicked.connect(self.close_app)

        # Graph Settings
        self.x = []
        self.y = []
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('black')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.grid(True, color='gray')
        self.line, = self.ax.plot(self.x, self.y, color='green')

        # LoRa & Thread Configuration
        self.queue = Queue()
        self.running = False  # Flag for LoRa thread

        # Timer for Graph Update
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_data)

    def create_filename(self):
        """Creates a new file with a timestamp down to the second."""
        current_time = time.strftime("%d_%m_%Y_%H-%M-%S", time.localtime())
        filename = f'Temperature_{current_time}.csv'

        with open(filename, 'w', newline='') as File:
            csv.writer(File, delimiter=CSV_DELIMITER).writerow(CSV_HEADER)

        print(f'\nCreated new data file -> {filename}')
        return filename

    def start_plot(self):
        """Starts data collection and resets time to zero."""
        self.start_time = time.time()  # Reset start time
        self.x = []
        self.y = []
        self.line.set_data(self.x, self.y)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
        self.fileNameData = self.create_filename()
        self.file_output.setText(self.fileNameData)

        self.running = True  # Start LoRa reading
        self.timer.start()
        
        # Start LoRa Reading Thread
        producer = threading.Thread(target=self.read_lora_data, args=(self.queue,))
        producer.daemon = True
        producer.start()

    def stop_plot(self):
        """Stops data collection."""
        self.running = False
        self.timer.stop()
        print("Data collection stopped.")

    def clear_plot(self):
        """Clears the plot data."""
        self.x = []
        self.y = []
        self.line.set_data(self.x, self.y)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
        print("Plot cleared.")

    def close_app(self):
        """Closes the application."""
        self.running = False
        self.timer.stop()
        QtWidgets.qApp.quit()

    def read_lora_data(self, queue):
        """Reads LoRa packets and updates queue."""
        while self.running:
            packet = rfm9x.receive(timeout=5.0)
            if packet:
                try:
                    temp_value = float(packet.decode("utf-8").strip())
                    elapsed_time = round(time.time() - self.start_time, 2)  # Time since start in seconds

                    queue.put([elapsed_time, temp_value])
                    self.output.setText(str(round(temp_value, 1)))

                    with open(self.fileNameData, 'a', newline='') as File:
                        csv.writer(File, delimiter=CSV_DELIMITER).writerow([elapsed_time, temp_value])

                except ValueError:
                    print("Invalid packet format")
            time.sleep(0.5)

    def update_data(self):
        """Updates the graph with new temperature data."""
        if not self.queue.empty():
            data_consumer = self.queue.get()

            self.x.append(data_consumer[0])  # Time (s)
            self.y.append(data_consumer[1])  # Temperature

            # Update the plot
            self.line.set_data(self.x, self.y)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindowPlot()
    w.setWindowTitle(TITLE_WINDOW_PLOT)
    w.show()
    sys.exit(app.exec_())