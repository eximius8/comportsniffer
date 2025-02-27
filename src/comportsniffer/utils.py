"""
Utility functions for the serial bridge.
"""

import logging
import os
import time
from typing import List, Optional, Tuple

import serial
from rich.console import Console
from rich.table import Table
from serial.tools import list_ports

logger = logging.getLogger(__name__)
console = Console()


def release_port(port_name: str) -> bool:
    """
    Safely check and release a serial port.
    
    Args:
        port_name: The name of the port to release (e.g., "COM3" or "/dev/ttyUSB0")
        
    Returns:
        bool: True if port was successfully released, False otherwise
    """
    try:
        ser = serial.Serial(port_name)
        ser.close()
        logger.info(f"Port {port_name} released")
        return True
    except Exception as e:
        logger.warning(f"Couldn't access or release {port_name}: {str(e)}")
        return False


def get_parity_value(parity_str: str) -> str:
    """
    Convert a parity string to PySerial constant.
    
    Args:
        parity_str: Parity string ('N', 'E', 'O', 'M', 'S')
        
    Returns:
        PySerial parity constant
    """
    parity_map = {
        'N': serial.PARITY_NONE,
        'E': serial.PARITY_EVEN,
        'O': serial.PARITY_ODD,
        'M': serial.PARITY_MARK,
        'S': serial.PARITY_SPACE
    }
    return parity_map.get(parity_str.upper(), serial.PARITY_NONE)


def get_stopbits_value(stopbits_str: str) -> float:
    """
    Convert a stop bits string to PySerial constant.
    
    Args:
        stopbits_str: Stop bits string ('1', '1.5', '2')
        
    Returns:
        PySerial stop bits constant
    """
    stopbits_map = {
        '1': serial.STOPBITS_ONE,
        '1.5': serial.STOPBITS_ONE_POINT_FIVE,
        '2': serial.STOPBITS_TWO
    }
    return stopbits_map.get(stopbits_str, serial.STOPBITS_ONE)


def get_parity_name(parity_value: str) -> str:
    """
    Get human-readable parity name.
    
    Args:
        parity_value: PySerial parity constant
        
    Returns:
        str: Human-readable parity name
    """
    parity_names = {
        serial.PARITY_NONE: "None",
        serial.PARITY_EVEN: "Even",
        serial.PARITY_ODD: "Odd",
        serial.PARITY_MARK: "Mark",
        serial.PARITY_SPACE: "Space"
    }
    return parity_names.get(parity_value, str(parity_value))


def get_stopbits_name(stopbits_value: float) -> str:
    """
    Get human-readable stop bits name.
    
    Args:
        stopbits_value: PySerial stop bits constant
        
    Returns:
        str: Human-readable stop bits name
    """
    stopbit_names = {
        serial.STOPBITS_ONE: "1",
        serial.STOPBITS_ONE_POINT_FIVE: "1.5",
        serial.STOPBITS_TWO: "2"
    }
    return stopbit_names.get(stopbits_value, str(stopbits_value))


def create_default_log_file(prefix: str = "bridge") -> str:
    """
    Create a default log file name based on current date and time.
    
    Args:
        prefix: Prefix for the log file name (default: "bridge")
        
    Returns:
        str: Path to the log file
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_dir = "logs"
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    return os.path.join(log_dir, f"{prefix}-{timestamp}.log")


def get_available_ports() -> List[Tuple[str, str, str]]:
    """
    Get a list of all available serial ports on the system.
    
    Returns:
        List of tuples containing (port_name, description, hardware_id)
    """
    ports = []
    for port in list_ports.comports():
        ports.append((port.device, port.description, port.hwid))
    return ports


def print_ports_table(ports: Optional[List[Tuple[str, str, str]]] = None) -> None:
    """
    Print a nicely formatted table of available serial ports.
    
    Args:
        ports: Optional list of ports. If None, will get all available ports.
    """
    if ports is None:
        ports = get_available_ports()
    
    if not ports:
        console.print("[yellow]No serial ports found on this system.[/yellow]")
        return
    
    table = Table(title="Available Serial Ports")
    table.add_column("Index", style="cyan")
    table.add_column("Port", style="green")
    table.add_column("Description", style="yellow")
    table.add_column("Hardware ID", style="blue")
    
    for i, (device, description, hwid) in enumerate(ports):
        table.add_row(
            str(i+1),
            device,
            description,
            hwid
        )
    
    console.print(table)


def ensure_log_directory(log_file: str) -> bool:
    """
    Ensure that the directory for the log file exists.
    
    Args:
        log_file: Path to the log file
        
    Returns:
        bool: True if directory exists or was created, False on error
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
            return True
        except Exception as e:
            logger.error(f"Error creating log directory: {str(e)}")
            return False
    return True