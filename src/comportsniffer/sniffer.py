import serial
import threading
import queue
import time
import logging


logger = logging.getLogger(__name__)


class ComPortBridge:
    def __init__(self, real_port, virtual_port, log_file, baud_rate=9600, timeout=0.1):
        self.real_port = real_port
        self.virtual_port = virtual_port
        self.log_file = log_file
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.running = False
        self.device_to_app = queue.Queue()
        self.app_to_device = queue.Queue()
        
    def connect(self):
        try:
            # Open both ports
            self.real_serial = serial.Serial(
                self.real_port, 
                self.baud_rate, 
                timeout=self.timeout
            )
            self.virtual_serial = serial.Serial(
                self.virtual_port, 
                self.baud_rate, 
                timeout=self.timeout
            )
            return True
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
            
    def read_from_device(self):
        while self.running:
            if self.real_serial.in_waiting:
                data = self.real_serial.read(self.real_serial.in_waiting)
                self.device_to_app.put(data)
                # Log data from device

                try:                    
                    with open(self.log_file, 'ab') as f:
                        f.write(b'response')
                        f.write(data)
                except:
                    pass
                
    def read_from_app(self):
        while self.running:
            if self.virtual_serial.in_waiting:
                data = self.virtual_serial.read(self.virtual_serial.in_waiting)
                self.app_to_device.put(data)
                # Log data from application
                try:
                    
                    with open(self.log_file, 'ab') as f:
                        f.write(b'request:')
                        f.write(data)
                except:
                    pass
                
    def write_to_device(self):
        while self.running:
            try:
                data = self.app_to_device.get(timeout=0.1)
                self.real_serial.write(data)
            except queue.Empty:
                continue
                
    def write_to_app(self):
        while self.running:
            try:
                data = self.device_to_app.get(timeout=0.1)
                self.virtual_serial.write(data)
            except queue.Empty:
                continue
                
    def start(self):
        if not self.connect():
            return False
        
        self.running = True
        
        # Create and start threads
        self.threads = [
            threading.Thread(target=self.read_from_device),
            threading.Thread(target=self.read_from_app),
            threading.Thread(target=self.write_to_device),
            threading.Thread(target=self.write_to_app)
        ]
        
        for thread in self.threads:
            thread.start()
            
        logger.info(f"Bridge started between {self.real_port} and {self.virtual_port}")
        return True
    
    def stop(self):
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join()
            
        # Close serial ports
        self.real_serial.close()
        self.virtual_serial.close()
        
        logger.info("Bridge stopped")


# Function to safely check and release a port
def release_port(port_name):
    try:
        ser = serial.Serial(port_name)
        ser.close()
        print(f"{port_name} released")
    except:
        print(f"Couldn't access {port_name}")


def run_bridge(real_port, virtual_port, baud_rate=1000000):
    bridge = ComPortBridge(real_port, virtual_port, baud_rate)
    release_port(real_port)
    release_port(virtual_port)
    try:
        if bridge.start():
            print(f"Bridge running between {real_port} and {virtual_port}")
            print("Press Ctrl+C to stop")
            
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping bridge...")
        bridge.stop()
        print("Bridge stopped")
