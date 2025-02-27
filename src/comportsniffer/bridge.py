"""
Core bridge implementation for serial port communication.
"""

import logging
import queue
import threading

from typing import List, Optional

import serial

logger = logging.getLogger(__name__)


class ComPortBridge:
    """
    A bidirectional bridge between a real serial port and a virtual serial port.
    
    This class handles the communication between a physical device connected to a
    real serial port and an application connected to a virtual serial port.
    """
    
    def __init__(
        self, 
        real_port: str, 
        virtual_port: str, 
        log_file: str, 
        baud_rate: int = 9600, 
        byte_size: int = 8,
        parity: str = serial.PARITY_NONE,
        stop_bits: str = serial.STOPBITS_ONE,
        timeout: float = 0.1,
        rtscts: bool = False,
        dsrdtr: bool = False,
        set_dtr: bool = False,
        set_rts: bool = False
    ):
        """
        Initialize the bridge with the specified ports and settings.
        
        Args:
            real_port: The name of the real serial port (e.g., "COM3" or "/dev/ttyUSB0")
            virtual_port: The name of the virtual serial port (e.g., "COM4" or "/dev/ttyS0")
            log_file: Path where communication logs will be stored
            baud_rate: Communication speed in baud (default: 9600)
            byte_size: Number of data bits (default: 8)
            parity: Parity checking (default: PARITY_NONE)
            stop_bits: Number of stop bits (default: STOPBITS_ONE)
            timeout: Read timeout in seconds (default: 0.1)
            rtscts: Enable hardware flow control (RTS/CTS) (default: False)
            dsrdtr: Enable hardware flow control (DTR/DSR) (default: False)
            set_dtr: Set DTR line on connection (default: False)
            set_rts: Set RTS line on connection (default: False)
        """
        self.real_port = real_port
        self.virtual_port = virtual_port
        self.log_file = log_file
        self.baud_rate = baud_rate
        self.byte_size = byte_size
        self.parity = parity
        self.stop_bits = stop_bits
        self.timeout = timeout
        self.rtscts = rtscts
        self.dsrdtr = dsrdtr
        self.set_dtr = set_dtr
        self.set_rts = set_rts
        self.running = False
        self.device_to_app = queue.Queue()
        self.app_to_device = queue.Queue()
        self.threads: List[threading.Thread] = []
        self.real_serial: Optional[serial.Serial] = None
        self.virtual_serial: Optional[serial.Serial] = None
        
    def connect(self) -> bool:
        """
        Open connections to both the real and virtual serial ports.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Open both ports with all the specified parameters
            self.real_serial = serial.Serial(
                port=self.real_port,
                baudrate=self.baud_rate,
                bytesize=self.byte_size,
                parity=self.parity,
                stopbits=self.stop_bits,
                timeout=self.timeout,
                rtscts=self.rtscts,
                dsrdtr=self.dsrdtr
            )
            
            # Apply DTR and RTS settings if specified
            if self.set_dtr is not None:
                self.real_serial.setDTR(self.set_dtr)
            if self.set_rts is not None:
                self.real_serial.setRTS(self.set_rts)
            
            # Open virtual port (typically with default settings)
            self.virtual_serial = serial.Serial(
                port=self.virtual_port,
                baudrate=self.baud_rate,
                bytesize=self.byte_size,
                parity=self.parity,
                stopbits=self.stop_bits,
                timeout=self.timeout
            )
            
            logger.info(f"Connected to real port {self.real_port} with settings: "
                       f"baud={self.baud_rate}, data={self.byte_size}, "
                       f"parity={self.parity}, stop={self.stop_bits}, "
                       f"rtscts={self.rtscts}, dsrdtr={self.dsrdtr}")
            
            return True
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
            
    def read_from_device(self) -> None:
        """Read data from the real device and queue it for the application."""
        while self.running:
            if self.real_serial and self.real_serial.in_waiting:
                data = self.real_serial.read(self.real_serial.in_waiting)
                self.device_to_app.put(data)
                # Log data from device
                try:                    
                    with open(self.log_file, 'ab') as f:
                        f.write(b'response:')
                        f.write(data)
                        f.write(b'\n')
                except Exception as e:
                    logger.error(f"Error writing to log file: {str(e)}")
                
    def read_from_app(self) -> None:
        """Read data from the application and queue it for the real device."""
        while self.running:
            if self.virtual_serial and self.virtual_serial.in_waiting:
                data = self.virtual_serial.read(self.virtual_serial.in_waiting)
                self.app_to_device.put(data)
                # Log data from application
                try:
                    with open(self.log_file, 'ab') as f:
                        f.write(b'request:')
                        f.write(data)
                        f.write(b'\n')
                except Exception as e:
                    logger.error(f"Error writing to log file: {str(e)}")
                
    def write_to_device(self) -> None:
        """Write queued data to the real device."""
        while self.running:
            try:
                data = self.app_to_device.get(timeout=0.1)
                if self.real_serial:
                    self.real_serial.write(data)
            except queue.Empty:
                continue
                
    def write_to_app(self) -> None:
        """Write queued data to the application."""
        while self.running:
            try:
                data = self.device_to_app.get(timeout=0.1)
                if self.virtual_serial:
                    self.virtual_serial.write(data)
            except queue.Empty:
                continue
                
    def start(self) -> bool:
        """
        Start the bridge by connecting to ports and launching worker threads.
        
        Returns:
            bool: True if bridge started successfully, False otherwise
        """
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
            thread.daemon = True  # Make threads daemon so they exit when main thread exits
            thread.start()
            
        logger.info(f"Bridge started between {self.real_port} and {self.virtual_port}")
        return True
    
    def stop(self) -> None:
        """Stop the bridge and clean up all resources."""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=1.0)  # Add timeout to avoid hanging
            
        # Close serial ports
        try:
            if self.real_serial:
                self.real_serial.close()
            if self.virtual_serial:
                self.virtual_serial.close()
        except Exception as e:
            logger.error(f"Error closing serial ports: {str(e)}")
        
        logger.info("Bridge stopped")