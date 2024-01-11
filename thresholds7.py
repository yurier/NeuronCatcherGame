import sys
import numpy as np
import serial
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QSlider, QLabel, QVBoxLayout, QGraphicsEllipseItem
from scipy import signal
import time 
import pyautogui
import atexit
import subprocess
import warnings
warnings.filterwarnings("ignore")

def start_other_script():
    subprocess.Popen(["ipython", "game_neuron8.py"], cwd="/home/yurier/neuroncatcher_outreach")

# Serial Port Setup
SERIAL_PORT = '/dev/ttyUSB0'  # Adjust as needed for your system
BAUD_RATE = 230400  # Arduino's baud rate
serial_port = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# PyQtGraph Setup for Signal Plot
app = QtWidgets.QApplication(sys.argv)
main_win = QtWidgets.QWidget()
layout = QVBoxLayout()
main_win.setLayout(layout)

signal_win = pg.plot(title="Serial Data Plot")
curve = signal_win.plot(pen='y')
layout.addWidget(signal_win)

# Add threshold lines to the plot
higher_threshold = pg.InfiniteLine(pos=700, angle=0, pen=pg.mkPen('r', width=2), label='higher:700', labelOpts={'position':0.1, 'color': (200,0,0), 'movable': True})
lower_threshold = pg.InfiniteLine(pos=100, angle=0, pen=pg.mkPen('b', width=2), label='lower:100', labelOpts={'position':0.1, 'color': (0,0,200), 'movable': True})
signal_win.addItem(higher_threshold)
signal_win.addItem(lower_threshold)

# PyQtGraph Setup for Spectrogram
spectrogram_win = pg.plot(title="Spectrogram Plot")
img = pg.ImageItem()
spectrogram_win.addItem(img)
layout.addWidget(spectrogram_win)

# Define a scaling factor for y-axis limits
y_axis_scale = 30
spectrogram_win.setYRange(0, y_axis_scale)

# Define bipolar colormap for spectrogram
pos = np.array([0., 1., 0.5, 0.25, 0.75])
color = np.array([[0, 255, 255, 255], [255, 255, 0, 255], [0, 0, 0, 255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
cmap = pg.ColorMap(pos, color)
lut = cmap.getLookupTable(0.0, 1.0, 256)
img.setLookupTable(lut)

# Buffer for incomplete data frames
data_buffer = bytearray()

# Spectrogram parameters
FS = 1000
CHUNKSZ = 1024
overlap = 512
LOOKBACK_LENGTH = 1500

# Initialize filter coefficients for spectrogram
lowcut = 0.2
highcut = 40.0
nyquist = 0.5 * FS
low = lowcut / nyquist
high = highcut / nyquist
b, a = signal.butter(4, [low, high], btype='band')

# Initialize variables for the spectrogram
spectrogram_data = np.zeros((LOOKBACK_LENGTH, int(CHUNKSZ / 2) + 1))

# History size for signal plot lookback
SIGNAL_LOOKBACK_SIZE = 60000
signal_history = np.zeros(SIGNAL_LOOKBACK_SIZE, dtype=np.int32)

# Initialize arrays to track threshold activation
threshold_activation_history = np.zeros((2, SIGNAL_LOOKBACK_SIZE), dtype=np.int32)  # Two rows: one for each threshold

# PyQtGraph Setup for Threshold Activation Tracking
threshold_win = pg.plot(title="Threshold Activation")
higher_curve = threshold_win.plot(pen='r', name='Higher Threshold')
lower_curve = threshold_win.plot(pen='b', name='Lower Threshold')
layout.addWidget(threshold_win)

time_sensitivity = 1  # Initialize the global variable


# Function to update higher threshold
def update_higher_threshold(value):
    global higher_threshold
    higher_threshold.setValue(value)
    higher_threshold_label.setText(f'Higher Threshold: {value}')

# Function to update lower threshold
def update_lower_threshold(value):
    global lower_threshold
    lower_threshold.setValue(value)
    lower_threshold_label.setText(f'Lower Threshold: {value}')

# Function to update time sensitivity
def update_time_sensitivity(value):
    global time_sensitivity
    time_sensitivity = value
    time_sensitivity_label.setText(f'Time Sensitivity: {value}')
    
# Function to create a circle plot
def create_circle_plot():
    plot_widget = pg.PlotWidget()
    plot_widget.setYRange(-1, 1)
    plot_widget.setXRange(-1, 1)
    circle = QGraphicsEllipseItem(-0.5, -0.5, 1, 1)
    circle.setPen(pg.mkPen(None))
    circle.setBrush(pg.mkBrush('w'))
    plot_widget.addItem(circle)
    return plot_widget, circle

# Create and configure the sliders
higher_threshold_slider = QSlider(QtCore.Qt.Horizontal)
higher_threshold_slider.setMinimum(0)
higher_threshold_slider.setMaximum(1000)
higher_threshold_slider.setValue(700)  # Default value
higher_threshold_slider.valueChanged.connect(update_higher_threshold)

lower_threshold_slider = QSlider(QtCore.Qt.Horizontal)
lower_threshold_slider.setMinimum(0)
lower_threshold_slider.setMaximum(1000)
lower_threshold_slider.setValue(100)  # Default value
lower_threshold_slider.valueChanged.connect(update_lower_threshold)

time_sensitivity_slider = QSlider(QtCore.Qt.Horizontal)
time_sensitivity_slider.setMinimum(1)
time_sensitivity_slider.setMaximum(10)
time_sensitivity_slider.setValue(1)  # Default value
time_sensitivity_slider.valueChanged.connect(update_time_sensitivity)

# Define labels for the sliders
higher_threshold_label = QLabel('Higher Threshold: 700')  # Initial value is shown
lower_threshold_label = QLabel('Lower Threshold: 100')   # Initial value is shown
time_sensitivity_label = QLabel('Time Sensitivity: 1')    # Initial value is shown

# Add widgets to the layout
layout.addWidget(higher_threshold_label)
layout.addWidget(higher_threshold_slider)
layout.addWidget(lower_threshold_label)
layout.addWidget(lower_threshold_slider)
layout.addWidget(time_sensitivity_label)
layout.addWidget(time_sensitivity_slider)

# Setup for the visual feedback of keys
key_visual_win = pg.GraphicsLayoutWidget()  # Use GraphicsLayoutWidget
layout.addWidget(key_visual_win)

# Create two circle plots for 'q' and 'w' keys
q_key_plot, q_key_circle = create_circle_plot()
w_key_plot, w_key_circle = create_circle_plot()

# Add the circle plots to the GraphicsLayoutWidget
q_key_widget = key_visual_win.addPlot(row=0, col=0)  # Create and add a new plot widget at (row=0, col=0)
w_key_widget = key_visual_win.addPlot(row=0, col=1)  # Create and add a new plot widget at (row=0, col=1)

# Add the circle items to the new plot widgets
q_key_widget.addItem(q_key_circle)
w_key_widget.addItem(w_key_circle)

# Decode samples from data frames
def decode_samples(data):
    samples = []
    i = 0
    while i < len(data) - 1:
        if data[i] & 0x80:  # Check for start of frame
            sample = ((data[i] & 0x7F) << 7) | (data[i + 1] & 0x7F)
            samples.append(sample)
            i += 2
        else:
            i += 1
    return samples, data[i:]  # Return samples and remaining data

# Initialize filter state
zi = signal.lfilter_zi(b, a)

# At the top of your script, add these lines to define time tracking variables
last_higher_activation = -np.inf  # Initialize to negative infinity
last_lower_activation = -np.inf   # Initialize to negative infinity

# At the top of your script, define the duration for button press
button_press_duration = 1  # Duration in seconds

# Add two variables to track the start time of button presses
start_time_q = None
start_time_w = None

# At the top of your script, add these lines to track the key states
is_q_pressed = False
is_w_pressed = False

def update():
    global data_buffer, spectrogram_data, zi, signal_history, higher_threshold, lower_threshold
    global threshold_activation_history, last_higher_activation, last_lower_activation, time_sensitivity
    global q_key_circle, w_key_circle, is_q_pressed, is_w_pressed, start_time_q, start_time_w


    # Current time in seconds
    current_time = time.time()

    if serial_port.in_waiting > 0:
        new_data = serial_port.read(serial_port.in_waiting)
        data_buffer += new_data

    # Current time in seconds
    current_time = time.time()

    if serial_port.in_waiting > 0:
        new_data = serial_port.read(serial_port.in_waiting)
        data_buffer += new_data

    while len(data_buffer) >= CHUNKSZ * 2:
        samples, data_buffer = decode_samples(data_buffer)
        if samples:
            
            # Apply smoothing
            window_size = 100
            window = np.ones(window_size) / window_size
            smoothed_samples = np.convolve(samples, window, mode='valid')

            # Update signal plot history
            signal_history = np.roll(signal_history, -len(smoothed_samples))
            signal_history[-len(smoothed_samples):] = smoothed_samples
            
            # Update signal plot
            display_size = 60000  # Adjust this to control how much of the history is displayed
            curve.setData(signal_history[-display_size:])

            # Check and update threshold activation
            max_sample = np.max(smoothed_samples)
            min_sample = np.min(smoothed_samples)
            higher_activated_now = max_sample >= higher_threshold.value()
            lower_activated_now = min_sample <= lower_threshold.value()

            # Update the activation history
            threshold_activation_history = np.roll(threshold_activation_history, -1, axis=1)
            threshold_activation_history[0, -1] = int(higher_activated_now)
            threshold_activation_history[1, -1] = int(lower_activated_now)
            display_size_threshold = 100  # Adjust this to control how much of the history is displayed

            # Update threshold activation plots with the same display range as the signal plot
            higher_curve.setData(threshold_activation_history[0, -display_size_threshold:])
            lower_curve.setData(threshold_activation_history[1, -display_size_threshold:])

            # Calculate spectrogram for the current chunk
            f, t, Sxx = signal.spectrogram(
                smoothed_samples,
                FS,
                nperseg=CHUNKSZ,
                noverlap=overlap,
                scaling='spectrum',
            )

            # Update the spectrogram data
            spectrogram_data = np.roll(spectrogram_data, -1, axis=0)
            Sxx_resized = Sxx[:spectrogram_data.shape[1], :]
            flattened_Sxx = Sxx_resized.flatten()
            try:
                if flattened_Sxx.shape[0] > spectrogram_data.shape[1]:
                    flattened_Sxx = flattened_Sxx[:spectrogram_data.shape[1]]
                spectrogram_data[-1, :] = 10 * np.log10(flattened_Sxx)
                img.setImage(spectrogram_data, autoLevels=False, levels=[-50, 40])
            except ValueError as e:
                # Handle or log the error
                print(f" ")
                
            # Check for threshold activation and update time of last activation
            if higher_activated_now and current_time - last_higher_activation > time_sensitivity:
                last_higher_activation = current_time
                start_time_w = current_time
            if lower_activated_now and current_time - last_lower_activation > time_sensitivity:
                last_lower_activation = current_time
                start_time_q = current_time

            # Determine if conditions are met to activate keys
            if last_lower_activation > last_higher_activation and current_time - last_lower_activation < time_sensitivity:
                if not is_q_pressed or (is_q_pressed and current_time - start_time_q > button_press_duration):
                    is_q_pressed = True
                    pyautogui.keyDown('q')
                    start_time_q = current_time
                if is_w_pressed:
                    is_w_pressed = False
                    pyautogui.keyUp('w')
            elif last_higher_activation > last_lower_activation and current_time - last_higher_activation < time_sensitivity:
                if not is_w_pressed or (is_w_pressed and current_time - start_time_w > button_press_duration):
                    is_w_pressed = True
                    pyautogui.keyDown('w')
                    start_time_w = current_time
                if is_q_pressed:
                    is_q_pressed = False
                    pyautogui.keyUp('q')
            else:
                if is_q_pressed and current_time - start_time_q > button_press_duration:
                    is_q_pressed = False
                    pyautogui.keyUp('q')
                if is_w_pressed and current_time - start_time_w > button_press_duration:
                    is_w_pressed = False
                    pyautogui.keyUp('w')

            # Update the visual feedback for the keys
            q_key_circle.setBrush(pg.mkBrush('g' if is_q_pressed else 'w'))
            w_key_circle.setBrush(pg.mkBrush('g' if is_w_pressed else 'w'))


# PyQt Timer Setup
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)  # Update interval in ms

# Show the main window
main_win.show()

if __name__ == '__main__':
    start_other_script()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()

    # Close the serial port
    serial_port.close()
