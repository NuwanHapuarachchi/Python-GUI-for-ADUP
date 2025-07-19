# Advanced Diffusing Update Protocol (ADUP)

A hybrid routing protocol implementation that combines DUAL (Diffusing Update Algorithm) with Machine Learning for superior performance compared to traditional protocols like RIP, OSPF, and EIGRP.

## Features

### Core Protocol Features
- **Dual-Algorithm Hybrid**: Combines reactive DUAL algorithm with proactive Multi-Armed Bandit optimization
- **Advanced Metrics**: Uses delay, jitter, packet loss, congestion, and link stability
- **Loop-Free Routing**: Guaranteed loop-free paths through DUAL algorithm
- **Intelligent Path Selection**: ML-based tie-breaking for optimal route selection
- **Fast Convergence**: Instant failover with pre-calculated backup paths

### Implementation Features
- **Real-time Simulation**: SimPy-based discrete-event simulation
- **Web-based UI**: Interactive dashboard for monitoring and control
- **Network Visualization**: Animated packet flow and topology display
- **Comprehensive Logging**: Detailed packet and routing event logs
- **Modular Design**: Clean separation of protocol logic, simulation, and visualization

## Architecture

```
adup/
├── packets.py      # ADUP packet definitions (Hello, Update, Route Entry)
├── router.py       # Router implementation with DUAL algorithm
├── simulation.py   # Network simulation environment
├── visualizer.py   # Network topology and packet visualization
├── web_ui.py       # Web-based dashboard
└── __init__.py

tests/              # Unit tests
main.py            # Main entry point
requirements.txt   # Python dependencies
```

## Installation

1. Clone the repository and navigate to the project directory
2. Create a virtual environment (automatically handled by VS Code)
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Simulation
```bash
python main.py --mode simulation --duration 60
```

### Web Interface
```bash
python main.py --mode web --port 8050
```
Then open http://localhost:8050 in your browser.

### Network Visualization
```bash
python main.py --mode visualize
```

## Protocol Details

### Packet Formats

#### ADUP Hello Packet (12 bytes)
- Version (4 bits)
- OpCode (4 bits) - 1 for Hello
- Reserved (8 bits)
- Delay (16 bits)
- Jitter (16 bits)
- Packet Loss (8 bits)
- Congestion (8 bits)
- Link Stability (16 bits)
- Checksum (16 bits)

#### ADUP Update Packet (Variable length)
- Header (4 bytes): Version, OpCode (2), Reserved, Checksum
- Route Entries (20 bytes each): Prefix Length, Destination, Metrics

### Routing Algorithm

1. **Neighbor Discovery**: Periodic Hello packets exchange link metrics
2. **Route Calculation**: DUAL ensures loop-free topology
3. **Intelligent Selection**: MAB algorithm optimizes path choice
4. **Triggered Updates**: Immediate propagation of topology changes
5. **Fast Failover**: Pre-calculated backup paths for instant recovery

### Metrics Calculation
```
Cost = w₁ × Delay + w₂ × Jitter + w₃ × PacketLoss + w₄ × Congestion
```

## Example Network Topology

The simulation creates a simple 3-router topology:
```
R1 (192.168.1.0/24) ←→ R2 (192.168.2.0/24) ←→ R3 (192.168.3.0/24)
```

Each router:
- Exchanges Hello packets every 5 seconds
- Maintains neighbor and routing tables
- Performs DUAL calculations for route selection
- Logs all protocol activities

## Web Dashboard Features

- **Real-time Network Topology**: Visual representation of router connections
- **Routing Tables**: Live view of each router's forwarding information base
- **Packet Flow Log**: Chronological list of protocol messages
- **Simulation Controls**: Start, stop, and reset simulation
- **Performance Metrics**: Protocol statistics and convergence graphs

## Advanced Features

### Multi-Armed Bandit Integration
- Learns optimal paths through historical performance data
- Provides intelligent tie-breaking between equal-cost paths
- Adapts to changing network conditions

### Comprehensive Logging
- Neighbor discovery events
- Routing table changes
- Packet transmission logs
- Performance metrics

### Extensible Design
- Modular architecture for easy extension
- Support for additional metrics
- Pluggable visualization backends

## Future Enhancements

1. **Real Network Integration**: Support for actual network interfaces
2. **Advanced ML Models**: Q-learning and neural network path optimization
3. **Security Features**: Authentication and encryption support
4. **Scalability Testing**: Large-scale network simulations
5. **Performance Analysis**: Detailed comparison with existing protocols

## Contributing

This is a research implementation of the ADUP protocol. Contributions are welcome for:
- Protocol optimizations
- Additional visualization features
- Performance improvements
- Real-world testing scenarios

## License

This project is for educational and research purposes.

## Desktop Application

ADUP now includes a modern **Electron.js desktop application** for enhanced visualization and control:

### Desktop App Features
- **Native Desktop Experience**: Cross-platform desktop application (Windows, macOS, Linux)
- **Real-time Network Visualization**: Interactive topology with vis-network
- **Live Packet Tracking**: Animated packet flow visualization
- **Comprehensive Monitoring**: Charts for delay, throughput, packet loss, and convergence
- **Protocol Configuration**: Easy-to-use interface for DUAL and MAB settings
- **Topology Generation**: Support for linear, ring, star, and mesh topologies
- **Export/Import**: Save and load simulation configurations

### Quick Start - Desktop App
1. **Easy Launch** (Windows):
   ```bash
   # Double-click or run from command line
   launch_adup.bat
   ```

2. **Easy Launch** (Linux/Mac):
   ```bash
   chmod +x launch_adup.sh
   ./launch_adup.sh
   ```

3. **Manual Launch**:
   ```bash
   # Terminal 1: Start Python backend
   .venv\Scripts\python.exe -m adup.electron_backend  # Windows
   # source .venv/bin/activate && python -m adup.electron_backend  # Linux/Mac
   
   # Terminal 2: Start Electron app
   cd electron-ui
   npm start
   ```

### Desktop App Usage
1. **Configure Network**: Select topology, node count, and protocol parameters
2. **Start Simulation**: Click "Start" to begin real-time simulation
3. **Monitor Performance**: View live charts and routing tables
4. **Interact**: Click nodes/links for detailed information
5. **Export Results**: Save configurations and simulation data

## Web Interface (Alternative)

For web-based access, ADUP also provides a browser interface:

### Quick Start - Web UI
```
