#!/usr/bin/env python3
"""
ADUP PyQt6 Main Window
Advanced Diffusing Update Protocol Desktop Application
"""

import sys
import os
import math
import traceback
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout, 
                            QHBoxLayout, QWidget, QSplitter, QPushButton, QLabel,
                            QComboBox, QSpinBox, QGroupBox, QTextEdit, QTableWidget,
                            QTableWidgetItem, QProgressBar, QStatusBar, QMenuBar,
                            QMenu, QToolBar, QMessageBox, QFileDialog, QCheckBox,
                            QSlider, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette

# Add the parent directory to the path for ADUP imports
sys.path.append(str(Path(__file__).parent.parent))

from adup.simulation import Simulation as ADUPSimulation
from gui.network_widget import NetworkVisualizationWidget
from gui.metrics_widget import MetricsWidget
from gui.routing_table_widget import RoutingTableWidget
from gui.packet_log_widget import PacketLogWidget
from gui.config_widget import ConfigurationWidget
from gui.protocol_comparison_widget import ProtocolComparisonWidget


class SimulationWorker(QThread):
    """Worker thread for running ADUP simulation"""
    
    # Signals for communication with main thread
    simulation_started = pyqtSignal()
    simulation_stopped = pyqtSignal()
    state_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.simulation = None
        self.is_running = False
        self.should_stop = False
        
    def setup_simulation(self, topology_type, num_nodes, connection_factor=2):
        """Setup simulation with given parameters"""
        try:
            self.simulation = ADUPSimulation()
            
            if topology_type == 'linear':
                self.simulation.create_linear_topology(num_nodes)
            elif topology_type == 'ring':
                self.simulation.create_ring_topology(num_nodes)
            elif topology_type == 'star':
                self.simulation.create_star_topology(num_nodes)
            elif topology_type == 'mesh':
                self.simulation.create_mesh_topology(num_nodes)
            elif topology_type == 'custom':
                self.simulation.create_custom_topology(num_nodes, connection_factor)
                
            return True
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False
    
    def start_simulation(self):
        """Start the simulation"""
        self.is_running = True
        self.should_stop = False
        self.start()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.should_stop = True
        self.is_running = False
    
    def run(self):
        """Main simulation loop"""
        if not self.simulation:
            self.error_occurred.emit("No simulation configured")
            return
            
        self.simulation_started.emit()
        
        try:
            # Run simulation for a specific duration or until stopped
            simulation_time = 0
            step_size = 0.5  # 500ms steps for better performance
            
            while self.is_running and not self.should_stop and simulation_time < 300:  # 5 minutes max
                # Step the simulation
                self.simulation.env.run(until=simulation_time + step_size)
                simulation_time += step_size
                
                # Emit state update
                try:
                    state = self.get_simulation_state()
                    self.state_updated.emit(state)
                except Exception as state_error:
                    print(f"DEBUG: Error getting simulation state: {state_error}")
                    import traceback
                    traceback.print_exc()
                
                # Sleep to control update rate
                self.msleep(500)  # 500ms = 2 FPS for better performance
                
        except Exception as e:
            self.error_occurred.emit(f"Simulation error: {str(e)}")
        finally:
            self.is_running = False
            self.simulation_stopped.emit()
    
    def get_simulation_state(self):
        """Get current simulation state with enhanced analysis data"""
        if not self.simulation:
            return {}
            
        state = {
            'routers': {},
            'links': [],
            'packets': [],
            'metrics': {},
            'time': self.simulation.env.now if self.simulation.env else 0,
            'path_analysis': [],
            'route_changes': [],
            'network_convergence': {}
        }
        
        # Collect all packet logs from all routers
        all_packet_logs = []
        all_route_changes = []
        all_path_analysis = []
        
        # Collect router information with generated positions
        for i, (router_id, router) in enumerate(self.simulation.routers.items()):            
            # Enhanced router state information
            router_routing_table = getattr(router, 'routing_table', {})
            router_fib = getattr(router, 'fib', {})
            
            # Combine routing_table and fib data, prioritizing fib
            combined_routes = dict(router_routing_table)
            combined_routes.update(router_fib)
            
            state['routers'][router_id] = {
                'id': router_id,
                'networks': getattr(router, 'networks', []),
                'neighbors': list(getattr(router, 'neighbor_table', {}).keys()),
                'routing_table': {dest: {
                    'next_hop': info.get('next_hop', ''), 
                    'cost': info.get('cost', info.get('metrics', {}).get('total_cost', 0) if isinstance(info, dict) else 0),
                    'metrics': info.get('metrics', {})
                } for dest, info in combined_routes.items()},
                'state': getattr(router, 'state', 'UNKNOWN'),
                'neighbor_metrics': getattr(router, 'neighbor_table', {}),
                'fib': router_fib,
                'path_usage': getattr(router, 'path_usage', {})
            }
            
            # Collect enhanced packet logs
            router_packet_logs = getattr(router, 'packet_log', [])
            all_packet_logs.extend(router_packet_logs)
            
            # Collect route changes
            router_route_changes = getattr(router, 'route_changes', [])
            all_route_changes.extend(router_route_changes)
            
            # Collect path analysis data
            router_path_analysis = getattr(router, 'path_analysis_log', [])
            all_path_analysis.extend(router_path_analysis)
        
        # Sort by time and add to state
        all_packet_logs.sort(key=lambda x: x.get('time', 0))
        all_route_changes.sort(key=lambda x: x.get('time', 0))
        all_path_analysis.sort(key=lambda x: x.get('time', 0))
        
        state['packet_logs'] = all_packet_logs
        state['route_changes'] = all_route_changes
        state['path_analysis'] = all_path_analysis
        
        # Extract enhanced link information
        processed_links = set()
        for router_id, router in self.simulation.routers.items():
            interfaces = getattr(router, 'interfaces', {})
            for interface_name, interface_info in interfaces.items():
                link = interface_info.get('link')
                if link:
                    # Create a unique identifier for the link to avoid duplicates
                    link_id = tuple(sorted([link.router1.name, link.router2.name]))
                    if link_id not in processed_links:
                        processed_links.add(link_id)
                        
                        # Calculate link metrics based on current neighbor data
                        r1_metrics = self.get_router_link_metrics(router_id, link.router2.name if link.router1.name == router_id else link.router1.name)
                        
                        state['links'].append({
                            'router1': link.router1.name,
                            'router2': link.router2.name,
                            'delay': r1_metrics.get('delay', getattr(link, 'delay', 10)),
                            'jitter': r1_metrics.get('jitter', getattr(link, 'jitter', 5)),
                            'packet_loss': r1_metrics.get('packet_loss', getattr(link, 'packet_loss', 0.01)),
                            'congestion': r1_metrics.get('congestion', 0),
                            'stability': r1_metrics.get('link_stability', 100)
                        })
        
        return state

    def get_router_link_metrics(self, router_id, neighbor_id):
        """Get current link metrics between two routers"""
        try:
            router = self.simulation.routers.get(router_id)
            if router and hasattr(router, 'neighbor_table'):
                neighbor_info = router.neighbor_table.get(neighbor_id, {})
                return neighbor_info.get('metrics', {})
        except:
            pass
        return {}


class ADUPMainWindow(QMainWindow):
    """Main window for ADUP desktop application"""
    
    def __init__(self):
        super().__init__()
        self.simulation_worker = SimulationWorker()
        self.is_simulation_running = False
        self.current_topology = 'custom'
        self.current_nodes = 10
        
        self.init_ui()
        self.setup_connections()
        self.setup_timer()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ADUP - Advanced Diffusing Update Protocol")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        main_layout.setSpacing(2)  # Reduce spacing
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar (includes all controls now)
        self.create_toolbar()
        
        # Create main content area with tabs (no separate control panel)
        self.create_tab_widget()
        main_layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.create_status_bar()
        
    def setup_connections(self):
        """Setup signal connections between simulation worker and UI"""
        # Connect simulation worker signals
        self.simulation_worker.simulation_started.connect(self.on_simulation_started)
        self.simulation_worker.simulation_stopped.connect(self.on_simulation_stopped)
        self.simulation_worker.state_updated.connect(self.on_state_updated)
        self.simulation_worker.error_occurred.connect(self.on_simulation_error)
        
    def setup_timer(self):
        """Setup update timer for periodic UI updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        # Timer will be started when simulation starts
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Simulation', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_simulation)
        file_menu.addAction(new_action)
        
        load_action = QAction('Load Configuration', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_configuration)
        file_menu.addAction(load_action)
        
        save_action = QAction('Save Configuration', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu('Simulation')
        
        start_action = QAction('Start', self)
        start_action.setShortcut('F5')
        start_action.triggered.connect(self.start_simulation)
        sim_menu.addAction(start_action)
        
        stop_action = QAction('Stop', self)
        stop_action.setShortcut('F6')
        stop_action.triggered.connect(self.stop_simulation)
        sim_menu.addAction(stop_action)
        
        reset_action = QAction('Reset', self)
        reset_action.setShortcut('F7')
        reset_action.triggered.connect(self.reset_simulation)
        sim_menu.addAction(reset_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About ADUP', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create a clean, compact toolbar with all controls"""
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #3c3c3c;
                border-bottom: 1px solid #555555;
                spacing: 6px;
                padding: 4px;
            }
        """)
        self.addToolBar(self.toolbar)
        
        # Simulation controls with clear, readable styling
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.start_simulation)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.toolbar.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏸ Stop")
        self.stop_btn.clicked.connect(self.stop_simulation)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.toolbar.addWidget(self.stop_btn)
        
        self.reset_btn = QPushButton("⟲ Reset")
        self.reset_btn.clicked.connect(self.reset_simulation)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)
        self.toolbar.addWidget(self.reset_btn)
        
        self.toolbar.addSeparator()
        
        # Topology controls with dark theme styling
        topo_label = QLabel("Topology:")
        topo_label.setStyleSheet("font-weight: bold; color: #ffffff; margin-right: 5px; font-size: 12px;")
        self.toolbar.addWidget(topo_label)
        
        self.topology_combo = QComboBox()
        self.topology_combo.addItems(['linear', 'ring', 'star', 'mesh', 'custom'])
        self.topology_combo.setCurrentText('custom')
        self.topology_combo.currentTextChanged.connect(self.topology_changed)
        self.topology_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #666666;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
                font-size: 12px;
                min-width: 80px;
            }
            QComboBox:hover {
                border-color: #0078d4;
                background-color: #505050;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #666666;
                background-color: #404040;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                selection-background-color: #0078d4;
                border: 1px solid #666666;
            }
        """)
        self.toolbar.addWidget(self.topology_combo)
        
        nodes_label = QLabel("Nodes:")
        nodes_label.setStyleSheet("font-weight: bold; color: #ffffff; margin-left: 10px; margin-right: 5px; font-size: 12px;")
        self.toolbar.addWidget(nodes_label)
        
        self.nodes_spinbox = QSpinBox()
        self.nodes_spinbox.setRange(3, 20)
        self.nodes_spinbox.setValue(10)
        self.nodes_spinbox.valueChanged.connect(self.nodes_changed)
        self.nodes_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #666666;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
                font-size: 12px;
                min-width: 60px;
            }
            QSpinBox:hover {
                border-color: #0078d4;
                background-color: #505050;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #404040;
                border: 1px solid #666666;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #505050;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
            }
            QSpinBox::up-arrow {
                border-bottom: 3px solid #ffffff;
            }
            QSpinBox::down-arrow {
                border-top: 3px solid #ffffff;
            }
        """)
        self.toolbar.addWidget(self.nodes_spinbox)
        
        # Connection factor for custom topology
        factor_label = QLabel("Connection:")
        factor_label.setStyleSheet("font-weight: bold; color: #ffffff; margin-left: 10px; margin-right: 5px; font-size: 12px;")
        self.toolbar.addWidget(factor_label)
        
        self.connection_factor_spinbox = QSpinBox()
        self.connection_factor_spinbox.setRange(10, 100)  # 10% to 100%
        self.connection_factor_spinbox.setValue(20)  # Default 20%
        self.connection_factor_spinbox.setSuffix("%")
        self.connection_factor_spinbox.setToolTip("Connection density as percentage of possible connections")
        self.connection_factor_spinbox.valueChanged.connect(self.connection_factor_changed)
        self.connection_factor_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 6px;
                border: 1px solid #666666;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
                font-size: 12px;
                min-width: 60px;
            }
            QSpinBox:hover {
                border-color: #0078d4;
                background-color: #505050;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #404040;
                border: 1px solid #666666;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #505050;
            }
        """)
        self.toolbar.addWidget(self.connection_factor_spinbox)
        
        # Show/hide connection factor based on topology
        self.update_topology_controls()
        
        self.toolbar.addSeparator()
        
        # Status indicator with dark theme styling
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold; color: #ffffff; margin-right: 5px; font-size: 12px;")
        self.toolbar.addWidget(status_label)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #ffffff;
                padding: 6px 12px;
                background-color: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.toolbar.addWidget(self.status_label)
        
        # Add spacer to push time to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Simulation time with dark theme styling
        time_label = QLabel("Time:")
        time_label.setStyleSheet("font-weight: bold; color: #ffffff; margin-right: 5px; font-size: 12px;")
        self.toolbar.addWidget(time_label)
        
        self.time_label = QLabel("0.00s")
        self.time_label.setStyleSheet("""
            QLabel {
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-weight: bold;
                color: #ffffff;
                padding: 6px 12px;
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 4px;
                font-size: 12px;
                min-width: 70px;
            }
        """)
        self.toolbar.addWidget(self.time_label)
        
    def create_tab_widget(self):
        """Create the main tab widget"""
        self.tab_widget = QTabWidget()
        
        # Network Visualization Tab
        self.network_widget = NetworkVisualizationWidget()
        self.tab_widget.addTab(self.network_widget, "Network")
        
        # Routing Tables Tab
        self.routing_widget = RoutingTableWidget()
        self.tab_widget.addTab(self.routing_widget, "Routing Tables")
        
        # Metrics Tab
        self.metrics_widget = MetricsWidget()
        self.tab_widget.addTab(self.metrics_widget, "Metrics")
        
        # Packet Log Tab
        self.packet_log_widget = PacketLogWidget()
        self.tab_widget.addTab(self.packet_log_widget, "Packet Log")
        
        # Configuration Tab
        self.config_widget = ConfigurationWidget()
        self.tab_widget.addTab(self.config_widget, "Configuration")
        
        # Protocol Comparison Tab
        self.comparison_widget = ProtocolComparisonWidget()
        self.tab_widget.addTab(self.comparison_widget, "Protocol Comparison")
        
    def create_status_bar(self):
        """Create the status bar with additional information"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets to status bar
        self.nodes_status_label = QLabel("Nodes: 0")
        self.nodes_status_label.setStyleSheet("padding: 2px 6px;")
        self.status_bar.addPermanentWidget(self.nodes_status_label)
        
        self.packets_status_label = QLabel("Packets: 0")
        self.packets_status_label.setStyleSheet("padding: 2px 6px;")
        self.status_bar.addPermanentWidget(self.packets_status_label)
        
        self.status_bar.showMessage("Ready - Configure topology and start simulation")
        
    # Slot methods
    @pyqtSlot()
    def start_simulation(self):
        """Start the simulation"""
        if not self.is_simulation_running:
            # Setup simulation with current parameters
            connection_factor = self.connection_factor_spinbox.value() / 100.0 if hasattr(self, 'connection_factor_spinbox') else 0.3
            if self.simulation_worker.setup_simulation(self.current_topology, self.current_nodes, connection_factor):
                self.simulation_worker.start_simulation()
            
    @pyqtSlot()
    def stop_simulation(self):
        """Stop the simulation"""
        if self.is_simulation_running:
            self.simulation_worker.stop_simulation()
            
    @pyqtSlot()
    def reset_simulation(self):
        """Reset the simulation"""
        self.stop_simulation()
        # Clear displays
        self.network_widget.clear()
        self.routing_widget.clear()
        self.metrics_widget.clear()
        self.packet_log_widget.clear()
        self.time_label.setText("0.00s")
        
    @pyqtSlot()
    def on_simulation_started(self):
        """Handle simulation start"""
        self.is_simulation_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Running")
        self.status_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: white;
                padding: 6px 12px;
                background-color: #28a745;
                border: 1px solid #1e7e34;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.status_bar.showMessage("Simulation running...")
        self.update_timer.start(500)  # Update every 500ms (2 FPS for better performance)
        
    @pyqtSlot()
    def on_simulation_stopped(self):
        """Handle simulation stop"""
        self.is_simulation_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: white;
                padding: 6px 12px;
                background-color: #dc3545;
                border: 1px solid #bd2130;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        self.status_bar.showMessage("Simulation stopped")
        self.update_timer.stop()
        
    @pyqtSlot(dict)
    def on_state_updated(self, state):
        """Handle simulation state update"""
        # Update time display
        self.time_label.setText(f"{state.get('time', 0):.2f}s")
        
        # Update status bar with current statistics
        num_routers = len(state.get('routers', {}))
        num_packets = len(state.get('packet_logs', []))
        self.nodes_status_label.setText(f"Nodes: {num_routers}")
        self.packets_status_label.setText(f"Packets: {num_packets}")
        
        # Update all widgets
        self.network_widget.update_state(state)
        self.routing_widget.update_state(state)
        self.metrics_widget.update_state(state)
        self.packet_log_widget.update_state(state)
        self.comparison_widget.update_state(state)
        
    @pyqtSlot(str)
    def on_simulation_error(self, error_msg):
        """Handle simulation error"""
        QMessageBox.critical(self, "Simulation Error", error_msg)
        self.stop_simulation()
        
    def topology_changed(self, topology):
        """Handle topology change"""
        self.current_topology = topology
        self.update_topology_controls()
        if not self.is_simulation_running:
            self.reset_simulation()
            
    @pyqtSlot(int)
    def nodes_changed(self, nodes):
        """Handle nodes count change"""
        self.current_nodes = nodes
        if not self.is_simulation_running:
            self.reset_simulation()
    
    def connection_factor_changed(self):
        """Handle connection factor changes"""
        if self.topology_combo.currentText() == 'custom':
            if not self.is_simulation_running:
                self.reset_simulation()
    
    def reset_and_restart_simulation(self):
        """Reset and restart simulation with new topology"""
        was_running = self.is_simulation_running
        if was_running:
            self.stop_simulation()
        
        # Wait a moment for stop to complete
        QTimer.singleShot(100, lambda: self.start_simulation() if was_running else None)
        
    def update_topology_controls(self):
        """Update visibility of topology controls based on selected topology"""
        topology_type = self.topology_combo.currentText()
        is_custom = topology_type == 'custom'
        
        # Show/hide connection factor controls for custom topology
        if hasattr(self, 'connection_factor_spinbox'):
            # Find the factor label by walking through toolbar widgets
            factor_label = None
            for action in self.toolbar.actions():
                widget = self.toolbar.widgetForAction(action)
                if widget and isinstance(widget, QLabel) and "Connection:" in widget.text():
                    factor_label = widget
                    break
            
            if factor_label:
                factor_label.setVisible(is_custom)
            self.connection_factor_spinbox.setVisible(is_custom)
        
    def update_display(self):
        """Update display elements"""
        # This can be used for any periodic updates not covered by state updates
        pass
        
    def new_simulation(self):
        """Create a new simulation"""
        self.reset_simulation()
        
    def load_configuration(self):
        """Load configuration from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", "", "JSON Files (*.json)")
        if filename:
            # TODO: Implement configuration loading
            self.status_bar.showMessage(f"Configuration loaded from {filename}")
            
    def save_configuration(self):
        """Save configuration to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "JSON Files (*.json)")
        if filename:
            # TODO: Implement configuration saving
            self.status_bar.showMessage(f"Configuration saved to {filename}")
            
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About ADUP", 
            "ADUP - Advanced Diffusing Update Protocol\n\n"
            "A hybrid routing protocol featuring:\n"
            "• DUAL (Diffusing Update Algorithm)\n"
            "• Multi-Armed Bandit machine learning\n"
            "• Multi-metric support\n"
            "• Real-time simulation and visualization\n\n"
            "Built with Python and PyQt6")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("ADUP")
    app.setApplicationVersion("1.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Apply a modern dark theme palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.darkGray)
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.AlternateBase, Qt.GlobalColor.darkGray)
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, Qt.GlobalColor.darkGray)
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, Qt.GlobalColor.blue)
    palette.setColor(QPalette.ColorRole.Highlight, Qt.GlobalColor.blue)
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    # Set modern dark theme application-wide stylesheet
    app.setStyleSheet("""
        /* Main Window - Dark Theme */
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        /* Toolbar - Dark and compact */
        QToolBar {
            background-color: #3c3c3c;
            border-bottom: 1px solid #555555;
            padding: 4px;
        }
        
        /* Tab Widget - Dark theme */
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        
        QTabBar::tab {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 8px 16px;
            margin-right: 2px;
            color: #ffffff;
        }
        
        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-bottom: 2px solid #0078d4;
            font-weight: bold;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #404040;
        }
        
        /* Status Bar - Dark */
        QStatusBar {
            background-color: #3c3c3c;
            border-top: 1px solid #555555;
            color: #ffffff;
        }
        
        /* Buttons - Dark theme with good visibility */
        QPushButton {
            background-color: #404040;
            border: 1px solid #666666;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
        }
        
        QPushButton:hover {
            background-color: #505050;
            border-color: #0078d4;
        }
        
        QPushButton:pressed {
            background-color: #353535;
        }
        
        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #666666;
            border-color: #444444;
        }
        
        /* ComboBox and SpinBox - Dark with dropdown fix */
        QComboBox, QSpinBox {
            background-color: #404040;
            border: 1px solid #666666;
            border-radius: 3px;
            padding: 4px 8px;
            color: #ffffff;
        }
        
        QComboBox:hover, QSpinBox:hover {
            border-color: #0078d4;
        }
        
        QComboBox::drop-down {
            border-left: 1px solid #666666;
            background-color: #404040;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid #ffffff;
        }
        
        QComboBox QAbstractItemView {
            background-color: #404040;
            color: #ffffff;
            selection-background-color: #0078d4;
            selection-color: #ffffff;
            border: 1px solid #666666;
        }
        
        QSpinBox::up-button, QSpinBox::down-button {
            background-color: #404040;
            border: 1px solid #666666;
        }
        
        QSpinBox::up-arrow, QSpinBox::down-arrow {
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
        }
        
        QSpinBox::up-arrow {
            border-bottom: 3px solid #ffffff;
        }
        
        QSpinBox::down-arrow {
            border-top: 3px solid #ffffff;
        }
        
        /* Labels - White text */
        QLabel {
            color: #ffffff;
        }
        
        /* CheckBoxes - Dark theme */
        QCheckBox {
            color: #ffffff;
        }
        
        QCheckBox::indicator {
            background-color: #404040;
            border: 1px solid #666666;
            border-radius: 2px;
        }
        
        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border-color: #0078d4;
        }
        
        /* Sliders - Dark theme */
        QSlider::groove:horizontal {
            background-color: #404040;
            border: 1px solid #666666;
            height: 6px;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background-color: #0078d4;
            border: 1px solid #0078d4;
            width: 16px;
            border-radius: 8px;
            margin: -5px 0;
        }
        
        QSlider::handle:horizontal:hover {
            background-color: #106ebe;
        }
        
        /* Frame panels - Dark */
        QFrame {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            color: #ffffff;
        }
        
        /* Tables - Dark */
        QTableWidget {
            background-color: #2b2b2b;
            alternate-background-color: #353535;
            gridline-color: #555555;
            border: 1px solid #555555;
            color: #ffffff;
        }
        
        QTableWidget::item {
            padding: 6px;
            border-bottom: 1px solid #404040;
        }
        
        QTableWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        QHeaderView::section {
            background-color: #404040;
            border: 1px solid #555555;
            padding: 6px;
            font-weight: bold;
            color: #ffffff;
        }
        
        /* Text areas - Dark */
        QTextEdit {
            background-color: #2b2b2b;
            border: 1px solid #555555;
            border-radius: 3px;
            color: #ffffff;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }
        
        /* Group boxes - Dark */
        QGroupBox {
            font-weight: bold;
            color: #ffffff;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: #2b2b2b;
        }
    """)
    
    # Create and show main window
    window = ADUPMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
