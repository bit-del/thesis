# hardware_control.py
import logging
import time
import serial
from serial.tools import list_ports
import threading

from config import (GPIO, RPI_GPIO_AVAILABLE, STEPS_PER_UM_Z, STEPS_PER_UM_XY, BACKLASH_X, BACKLASH_Y)

class LightControl:
    def __init__(self, bf_pin, fluo_pin, status_callback):
        self.bf_pin = bf_pin; self.fluo_pin = fluo_pin
        self.status_callback = status_callback
        if RPI_GPIO_AVAILABLE:
            try:
                GPIO.setwarnings(False); GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.bf_pin, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.fluo_pin, GPIO.OUT, initial=GPIO.LOW)
                self.status_callback("Light controller initialized.")
                logging.info(f"Initialized GPIO pins: Bright Field={bf_pin}, Fluorescence={fluo_pin}")
            except Exception as e:
                self.status_callback(f"GPIO Error: {e}"); logging.error(f"Failed to initialize GPIO: {e}")
        else:
            self.status_callback("Light controller disabled (No GPIO).")
    def set_light(self, pin, state):
        if RPI_GPIO_AVAILABLE:
            output_state = GPIO.HIGH if state else GPIO.LOW
            GPIO.output(pin, output_state)
            light_name = "Bright Field" if pin == self.bf_pin else "Fluorescence"
            status = "ON" if state else "OFF"
            self.status_callback(f"{light_name} light turned {status}.")
            logging.info(f"Set GPIO pin {pin} to {status}")
        else:
            light_name = "Bright Field" if pin == self.bf_pin else "Fluorescence"
            status = "ON" if state else "OFF"
            logging.warning(f"Simulating: Turn {light_name} light {status} (GPIO pin {pin}).")
            self.status_callback("Cannot control light (No GPIO).")
    def cleanup(self):
        if RPI_GPIO_AVAILABLE:
            GPIO.cleanup(); logging.info("GPIO cleanup complete.")

class MotorConversion:
    @staticmethod
    def um_to_microsteps_z(um):
        return int(round(um * STEPS_PER_UM_Z))

    @staticmethod
    def um_to_microsteps_xy(um):
        return int(round(um * STEPS_PER_UM_XY))

class MotorControl:
    def __init__(self, status_callback):
        self.ser = None
        self.status_callback = status_callback
        self.port = self._find_arduino_port()
        self.lock = threading.Lock()
        self.last_direction = {'x': 1, 'y': 1, 'z': 1} # 1 for forward, -1 for reverse
        
        if self.port:
            try:
                self.ser = serial.Serial(self.port, 9600, timeout=0.1) 
                time.sleep(2) 
                self.status_callback(f"Connected to Arduino on {self.port}")
                logging.info(f"Successfully connected to Arduino on {self.port}")
            except serial.SerialException as e:
                self.status_callback(f"Error connecting to Arduino: {e}")
                logging.error(f"Failed to connect to Arduino on {self.port}: {e}")
                self.ser = None
        else:
            self.status_callback("Arduino not found.")
            logging.warning("Could not find an Arduino connected.")

    def _find_arduino_port(self):
        ports = list_ports.comports()
        for port in ports:
            if "arduino" in port.description.lower() or "ch340" in port.description.lower() or port.vid == 0x2341:
                return port.device
        return None

    def send_command(self, command, stop_flag=lambda: False, silent=False):
        with self.lock:
            if self.ser and self.ser.is_open:
                try:
                    final_command = command
                    original_command = command
                    
                    # --- 解析移動指令與背隙補償 (Backlash Compensation) ---
                    axis_found = None
                    steps_to_move = 0
                    
                    if command.startswith('s'):
                        # 's' 開頭代表直接輸入步數 (如 'sx100', 'sy-50')
                        cmd_body = command[1:].lower()
                        if len(cmd_body) > 1 and cmd_body[0] in ['x', 'y', 'z']:
                            axis_found = cmd_body[0]
                            try:
                                steps_to_move = int(float(cmd_body[1:]))
                            except ValueError:
                                axis_found = None
                        final_command = command[1:] # 預設去除 's'
                    elif command[0].lower() in ['x', 'y', 'z']:
                        # 一般開頭代表輸入 um (如 'x10.5')
                        axis_found = command[0].lower()
                        value_str = command[1:]
                        if value_str not in ['0', 'center']: 
                            try:
                                um_val = float(value_str)
                                if axis_found == 'z':
                                    microsteps = MotorConversion.um_to_microsteps_z(abs(um_val))
                                else:
                                    microsteps = MotorConversion.um_to_microsteps_xy(abs(um_val))
                                steps_to_move = microsteps if um_val >= 0 else -microsteps
                                final_command = f"{axis_found}{steps_to_move}"
                            except ValueError:
                                logging.error(f"Invalid motor val: {value_str}")
                                if not silent: self.status_callback(f"Invalid: {value_str}")
                                return
                        else:
                            axis_found = None # 0 或 center 不做補償

                    # 執行補償邏輯 (僅限 X, Y 軸且步數不為 0)
                    if axis_found in ['x', 'y'] and steps_to_move != 0:
                        new_dir = 1 if steps_to_move > 0 else -1
                        if new_dir != self.last_direction[axis_found]:
                            gap = BACKLASH_X if axis_found == 'x' else BACKLASH_Y
                            # 補償：在目標步數上額外增加 (方向 * 間隙)
                            steps_to_move += new_dir * gap
                            logging.info(f"Applying Backlash Compensation [{axis_found}]: {self.last_direction[axis_found]} -> {new_dir}, compensation: {new_dir * gap} steps")
                            if not silent: self.status_callback(f"Backlash Comp {axis_found.upper()}: {new_dir * gap} steps added")
                        
                        self.last_direction[axis_found] = new_dir
                        final_command = f"{axis_found}{steps_to_move}"

                    self.ser.reset_input_buffer() 
                    self.ser.write(f"{final_command}\n".encode('utf-8'))
                    
                    if not silent:
                        self.status_callback(f"Sent: {original_command} -> {final_command}. Waiting for ACK...")
                        logging.info(f"Sent to Arduino: {final_command}")
                    
                    if 'center' in final_command or final_command == 'z0':
                         return 

                    response = ""
                    start_time = time.time()
                    
                    while time.time() - start_time < 5.0:
                        if stop_flag():
                            logging.warning(f"Command {final_command} cancelled.")
                            return
                        
                        if not self.ser or not self.ser.is_open:
                            return

                        try:
                            line = self.ser.readline()
                            if line:
                                response = line.decode('utf-8').strip()
                                if response:
                                    if not silent:
                                        self.status_callback(f"Arduino ACK: {response}")
                                        logging.info(f"Arduino ACK: {response}")
                                    return
                        except Exception as e:
                            logging.error(f"Read error: {e}")
                            return
                        
                        # [優化] 避免 Busy Wait 吃滿 CPU
                        time.sleep(0.01)
                        
                    if not silent:
                        self.status_callback(f"Warning: No ACK for {final_command}")
                    logging.warning(f"No ACK from Arduino for {final_command}")

                except serial.SerialException as e:
                    if not silent: self.status_callback(f"Serial Error: {e}")
                    logging.error(f"Serial Error: {e}")
            else:
                if not silent: self.status_callback("Arduino not connected.")
                logging.warning(f"Arduino not connected.")

    def close(self):
        with self.lock:
            if self.ser and self.ser.is_open:
                self.ser.close()
                self.ser = None 
                logging.info("Serial port closed.")