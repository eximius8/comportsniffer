"""
Command-line interface for the serial bridge.
"""

import logging
import time
from typing import Optional
import serial

import typer
from rich.console import Console

from comportsniffer.bridge import ComPortBridge
from comportsniffer.utils import (
    create_default_log_file,
    ensure_log_directory,
    print_ports_table,
    release_port,
    get_parity_name,
    get_parity_value,
    get_stopbits_name,
    get_stopbits_value
)

# Initialize Typer app and Rich console
app = typer.Typer(
    help="Serial Port Bridge - Connect real and virtual serial ports",
    add_completion=False,
)
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.command("list-ports")
def list_ports_command():
    """List all available serial ports on the system."""
    print_ports_table()


@app.command("release")
def release_command(
    port: str = typer.Argument(..., help="Port to release (e.g. COM3 or /dev/ttyUSB0)")
):
    """Release a potentially locked serial port."""
    with console.status(f"Releasing port {port}..."):
        if release_port(port):
            console.print(f"[green]Successfully released port {port}[/green]")
        else:
            console.print(f"[red]Failed to release port {port}[/red]")


@app.command("bridge")
def bridge_command(
    real_port: str = typer.Option(
        ..., "--real-port", "-r", help="Real serial port (e.g., COM3 or /dev/ttyUSB0)"
    ),
    virtual_port: str = typer.Option(
        ..., "--virtual-port", "-v", help="Virtual serial port (e.g., COM4 or /dev/ttyS0)"
    ),
    baud_rate: int = typer.Option(
        9600, "--baud-rate", "-b", help="Baud rate (default: 9600)"
    ),
    data_bits: int = typer.Option(
        8, "--data-bits", "-d", help="Number of data bits (5-8)", min=5, max=8
    ),
    parity: str = typer.Option(
        "N", "--parity", "-p", help="Parity (N=None, E=Even, O=Odd, M=Mark, S=Space)"
    ),
    stop_bits: str = typer.Option(
        "1", "--stop-bits", "-s", help="Stop bits (1, 1.5, or 2)"
    ),
    log_file: Optional[str] = typer.Option(
        None,
        "--log-file",
        "-l",
        help="Log file path (default: ./logs/bridge-TIMESTAMP.log)",
    ),
    auto_release: bool = typer.Option(
        True,
        "--auto-release/--no-auto-release",
        help="Automatically try to release ports before connecting",
    ),
    flow_control: bool = typer.Option(
        False,
        "--flow-control/--no-flow-control",
        help="Enable hardware flow control (RTS/CTS and DTR/DSR)",
    ),
    set_dtr: Optional[bool] = typer.Option(
        None,
        "--dtr/--no-dtr",
        help="Set DTR line on connection",
    ),
    set_rts: Optional[bool] = typer.Option(
        None,
        "--rts/--no-rts",
        help="Set RTS line on connection",
    ),
):
    """Start a bridge between real and virtual serial ports."""
    # Set default log file if not provided
    if not log_file:
        log_file = create_default_log_file()

    # Ensure log directory exists
    if not ensure_log_directory(log_file):
        console.print("[red]Failed to create log directory.[/red]")
        raise typer.Exit(1)

    # Release ports before starting (optional but can help with locked ports)
    if auto_release:
        with console.status("Attempting to release ports before starting..."):
            release_port(real_port)
            release_port(virtual_port)

    # Convert string parameters to PySerial constants
    parity_value = get_parity_value(parity)
    stopbits_value = get_stopbits_value(stop_bits)

    # Create and start the bridge
    console.print(f"[bold green]Starting bridge[/bold green]")
    console.print(f"Real port: [cyan]{real_port}[/cyan]")
    console.print(f"Virtual port: [cyan]{virtual_port}[/cyan]")
    console.print(f"Baud rate: [cyan]{baud_rate}[/cyan]")
    console.print(f"Data bits: [cyan]{data_bits}[/cyan]")
    console.print(f"Parity: [cyan]{get_parity_name(parity_value)}[/cyan]")
    console.print(f"Stop bits: [cyan]{get_stopbits_name(stopbits_value)}[/cyan]")
    console.print(f"Flow control: [cyan]{'Enabled' if flow_control else 'Disabled'}[/cyan]")
    if set_dtr is not None:
        console.print(f"DTR line: [cyan]{'Set' if set_dtr else 'Clear'}[/cyan]")
    if set_rts is not None:
        console.print(f"RTS line: [cyan]{'Set' if set_rts else 'Clear'}[/cyan]")
    console.print(f"Log file: [cyan]{log_file}[/cyan]")

    bridge = ComPortBridge(
        real_port=real_port,
        virtual_port=virtual_port,
        log_file=log_file,
        baud_rate=baud_rate,
        byte_size=data_bits,
        parity=parity_value,
        stop_bits=stopbits_value,
        timeout=0.1,
        rtscts=flow_control,
        dsrdtr=flow_control,
        set_dtr=set_dtr,
        set_rts=set_rts
    )

    try:
        if bridge.start():
            console.print(
                "[bold green]Bridge is running.[/bold green] Press Ctrl+C to stop."
            )

            # Keep the main thread alive
            while True:
                time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping bridge...[/yellow]")
        bridge.stop()
        console.print("[green]Bridge stopped[/green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        bridge.stop()
        raise typer.Exit(1)


@app.command("mikon")
def mikon_command(
    real_port: str = typer.Option(
        "COM11", "--port", "-p", help="Real serial port for MIKON-207 device"
    ),
    virtual_port: str = typer.Option(
        ..., "--virtual-port", "-v", help="Virtual serial port for application"
    ),
    baud_rate: int = typer.Option(
        57600, "--baud-rate", "-b", help="Baud rate (default: 57600 for MIKON-207)"
    ),
    log_file: Optional[str] = typer.Option(
        None,
        "--log-file",
        "-l",
        help="Log file path (default: ./logs/mikon-TIMESTAMP.log)",
    ),
    auto_release: bool = typer.Option(
        True,
        "--auto-release/--no-auto-release",
        help="Automatically try to release ports before connecting",
    ),
):
    """Start a bridge preconfigured for MIKON-207 device."""
    # Set default log file if not provided
    if not log_file:
        log_file = create_default_log_file("mikon")

    # Ensure log directory exists
    if not ensure_log_directory(log_file):
        console.print("[red]Failed to create log directory.[/red]")
        raise typer.Exit(1)

    # Release ports before starting (optional but can help with locked ports)
    if auto_release:
        with console.status("Attempting to release ports before starting..."):
            release_port(real_port)
            release_port(virtual_port)

    # MIKON-207 specific settings
    data_bits = 8
    parity_value = serial.PARITY_MARK  # 'M'
    stopbits_value = serial.STOPBITS_ONE  # '1'
    flow_control = True
    set_dtr = True
    set_rts = False

    # Create and start the bridge with MIKON-207 specific settings
    console.print(f"[bold green]Starting MIKON-207 bridge[/bold green]")
    console.print(f"MIKON port: [cyan]{real_port}[/cyan]")
    console.print(f"Virtual port: [cyan]{virtual_port}[/cyan]")
    console.print(f"Baud rate: [cyan]{baud_rate}[/cyan]")
    console.print(f"Data bits: [cyan]{data_bits}[/cyan]")
    console.print(f"Parity: [cyan]{get_parity_name(parity_value)}[/cyan]")
    console.print(f"Stop bits: [cyan]{get_stopbits_name(stopbits_value)}[/cyan]")
    console.print(f"Flow control: [cyan]Enabled[/cyan]")
    console.print(f"DTR line: [cyan]Set[/cyan]")
    console.print(f"RTS line: [cyan]Clear[/cyan]")
    console.print(f"Log file: [cyan]{log_file}[/cyan]")

    bridge = ComPortBridge(
        real_port=real_port,
        virtual_port=virtual_port,
        log_file=log_file,
        baud_rate=baud_rate,
        byte_size=data_bits,
        parity=parity_value,
        stop_bits=stopbits_value,
        timeout=0.01,  # MIKON uses 0.01 timeout
        rtscts=flow_control,
        dsrdtr=flow_control,
        set_dtr=set_dtr,
        set_rts=set_rts
    )

    try:
        if bridge.start():
            console.print(
                "[bold green]MIKON-207 bridge is running.[/bold green] Press Ctrl+C to stop."
            )

            # Keep the main thread alive
            while True:
                time.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping MIKON bridge...[/yellow]")
        bridge.stop()
        console.print("[green]MIKON bridge stopped[/green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        bridge.stop()
        raise typer.Exit(1)


@app.callback()
def main():
    """
    Serial Port Bridge - Connect real and virtual serial ports.
    
    This tool allows you to create a bidirectional bridge between a real serial port
    (connected to hardware) and a virtual serial port (used by applications).
    
    For MIKON-207 devices, use the 'mikon' command which sets up the correct parameters.
    """
    pass