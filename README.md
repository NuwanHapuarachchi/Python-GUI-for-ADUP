# Advanced Diffusing Update Protocol (ADUP)

A hybrid routing protocol implementation that combines DUAL (Diffusing Update Algorithm) with Machine Learning for superior performance compared to traditional protocols like RIP, OSPF, and EIGRP.

## 🚀 Repository Information
- **GitHub Repository**: [Python-GUI-for-ADUP](https://github.com/NuwanHapuarachchi/Python-GUI-for-ADUP)
- **Author**: NuwanHapuarachchi
- **License**: Educational and Research Use

## Features

### Core Protocol Features
- **Dual-Algorithm Hybrid**: Combines reactive DUAL algorithm with proactive Multi-Armed Bandit optimization
- **Advanced Metrics**: Uses delay, jitter, packet loss, congestion, and link stability
- **Loop-Free Routing**: Guaranteed loop-free paths through DUAL algorithm
- **Intelligent Path Selection**: ML-based tie-breaking for optimal route selection
- **Fast Convergence**: Instant failover with pre-calculated backup paths

### Implementation Features
- **PyQt6 Desktop GUI**: Modern cross-platform desktop application with advanced visualization
- **Real-time Simulation**: SimPy-based discrete-event simulation
- **Web-based UI**: Interactive dashboard for monitoring and control
- **Network Visualization**: Animated packet flow and topology display
- **Comprehensive Logging**: Detailed packet and routing event logs
- **Modular Design**: Clean separation of protocol logic, simulation, and visualization

## Architecture

```
adup/
├── packets.py          # ADUP packet definitions (Hello, Update, Route Entry)
├── router.py           # Router implementation with DUAL algorithm
├── simulation.py       # Network simulation environment
├── visualizer.py       # Network topology and packet visualization
├── web_ui.py           # Web-based dashboard
├── enhanced_web_ui.py  # Enhanced web interface
└── __init__.py

gui/
├── main_window.py      # Main PyQt6 application window
├── network_widget.py   # Network topology visualization widget
├── metrics_widget.py   # Performance metrics display
├── config_widget.py    # Configuration panel
├── packet_log_widget.py # Packet logging interface
├── routing_table_widget.py # Routing table display
├── protocol_comparison_widget.py # Protocol comparison tools
├── advanced_packet_viz.py # Advanced packet visualization
└── __init__.py

main.py            # Command-line entry point
main_pyqt.py       # PyQt6 GUI entry point  
requirements.txt   # Python dependencies
```

## 🛠️ Installation

### Quick Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/NuwanHapuarachchi/Python-GUI-for-ADUP.git
   cd Python-GUI-for-ADUP
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Dependencies
- **Core**: `scapy`, `numpy`, `matplotlib`, `simpy`, `networkx`
- **GUI**: `PyQt6`, `pyqtgraph`
- **Web**: `websockets`

## 🎯 Usage

### 🖥️ PyQt6 Desktop Application (Recommended)
```bash
python main_pyqt.py
```
**Features:**
- Modern cross-platform GUI interface
- Real-time network topology visualization
- Advanced packet flow monitoring
- Interactive routing table display
- Performance metrics and charts
- Protocol configuration controls

### 🖲️ Command Line Simulation
```bash
python main.py --mode simulation --duration 60
```

### 🌐 Web Interface
```bash
python main.py --mode web --port 8050
```
Then open http://localhost:8050 in your browser.

### 📊 Network Visualization
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

## 🖥️ PyQt6 Desktop Application Features

### Main Interface
- **Network Topology View**: Interactive visualization of router connections and packet flows
- **Real-time Metrics**: Live charts showing delay, jitter, packet loss, and throughput
- **Routing Tables**: Dynamic display of each router's forwarding information base
- **Packet Log**: Detailed chronological view of all protocol messages
- **Configuration Panel**: Easy setup of simulation parameters and protocol settings

### Advanced Visualization
- **Animated Packet Flow**: Real-time visualization of packet transmission
- **Performance Graphs**: Historical and real-time performance metrics
- **Protocol Comparison**: Side-by-side comparison with RIP, OSPF, and EIGRP
- **Network Statistics**: Comprehensive network health monitoring

## 🌐 Web Dashboard Features

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

## 🔬 Future Enhancements

1. **Real Network Integration**: Support for actual network interfaces
2. **Advanced ML Models**: Q-learning and neural network path optimization
3. **Security Features**: Authentication and encryption support
4. **Scalability Testing**: Large-scale network simulations
5. **Performance Analysis**: Detailed comparison with existing protocols
6. **Mobile App**: Cross-platform mobile monitoring application

## 🤝 Contributing

This is a research implementation of the ADUP protocol. Contributions are welcome for:
- Protocol optimizations
- Additional visualization features
- Performance improvements
- Real-world testing scenarios
- Bug fixes and code improvements

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is for educational and research purposes.

## 📞 Contact

- **Author**: NuwanHapuarachchi
- **Email**: hapuarachchihadnd,22@uom.lk
- **GitHub**: [NuwanHapuarachchi](https://github.com/NuwanHapuarachchi)
- **Repository**: [Python-GUI-for-ADUP](https://github.com/NuwanHapuarachchi/Python-GUI-for-ADUP)

---

## 🗂️ Legacy Documentation

### Desktop Application (Electron.js - Not Currently Available)

### Desktop Application (Electron.js - Not Currently Available)

*Note: The following Electron.js desktop application features are planned for future implementation but not currently available in this repository.*

ADUP was designed to include a modern **Electron.js desktop application** for enhanced visualization and control:

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
