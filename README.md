# comportsniffer

A command-line tool to create bridges between real and virtual serial ports. This tool allows you to connect a physical serial device to a virtual serial port, enabling communication between applications and hardware devices.

## Features

- Create bidirectional bridges between real and virtual serial ports
- List all available serial ports on your system
- Release potentially locked serial ports
- Configurable baud rates and logging
- Rich command-line interface with color output

## Installation

### From PyPI

```bash
pip install comportsniffer
```

### From Source

```bash
git clone https://github.com/yourusername/serial-bridge.git
cd serial-bridge
pip install -e .
```

## Usage

### List Available Ports

```bash
serial-bridge list-ports
```

### Release a Locked Port

```bash
serial-bridge release COM3
```

### Create a Bridge

```bash
serial-bridge bridge --real-port COM3 --virtual-port COM4
```

### Additional Options

```bash
# Set custom baud rate
serial-bridge bridge -r COM3 -v COM4 -b 115200

# Specify log file location
serial-bridge bridge -r COM3 -v COM4 -l my_logs/session.log

# Disable automatic port release
serial-bridge bridge -r COM3 -v COM4 --no-auto-release
```

## Requirements

- Python 3.7 or higher
- pyserial
- typer
- rich

## License

MIT