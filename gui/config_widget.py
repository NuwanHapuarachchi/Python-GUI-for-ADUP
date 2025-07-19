"""
Configuration Widget for ADUP
Configure protocol parameters and simulation settings
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QSpinBox, QDoubleSpinBox, QComboBox,
                            QCheckBox, QSlider, QGroupBox, QPushButton,
                            QTextEdit, QTabWidget, QFrame, QLineEdit, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ConfigurationWidget(QWidget):
    """Widget for configuring ADUP protocol parameters"""
    
    config_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.config = self.get_default_config()
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Create tab widget for different configuration categories
        self.tab_widget = QTabWidget()
        self.tab_widget.setMaximumHeight(280)  # Much more compact
        self.tab_widget.setMinimumHeight(280)  # Fixed height
        layout.addWidget(self.tab_widget)
        
        # Protocol parameters tab
        protocol_tab = self.create_scrollable_tab(self.create_protocol_tab())
        self.tab_widget.addTab(protocol_tab, "Protocol")
        
        # Network parameters tab
        network_tab = self.create_scrollable_tab(self.create_network_tab())
        self.tab_widget.addTab(network_tab, "Network")
        
        # Simulation parameters tab
        simulation_tab = self.create_scrollable_tab(self.create_simulation_tab())
        self.tab_widget.addTab(simulation_tab, "Simulation")
        
        # Advanced parameters tab
        advanced_tab = self.create_scrollable_tab(self.create_advanced_tab())
        self.tab_widget.addTab(advanced_tab, "Advanced")
        
        # Action buttons
        button_panel = self.create_button_panel()
        layout.addWidget(button_panel)
        
        # Apply compact styling to all widgets
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                margin-top: 6px;
                padding-top: 3px;
                margin-bottom: 2px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                background-color: #2b2b2b;
                font-size: 11px;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                color: #ffffff;
                min-height: 18px;
                max-height: 22px;
                font-size: 11px;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
                margin: 1px;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                color: #ffffff;
                padding: 3px 6px;
                border: 1px solid #555555;
                margin-right: 2px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
                spacing: 3px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 4px 8px;
                color: #ffffff;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #0078d4;
            }
            QScrollArea {
                border: none;
                background-color: #2b2b2b;
            }
        """)
        
    def create_protocol_tab(self):
        """Create protocol parameters tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)  # Reduce spacing
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        
        # DUAL Algorithm settings
        dual_group = QGroupBox("DUAL Algorithm Settings")
        dual_layout = QGridLayout(dual_group)
        dual_layout.setSpacing(3)  # Reduce spacing
        dual_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        
        # Hello interval
        dual_layout.addWidget(QLabel("Hello Interval (s):"), 0, 0)
        self.hello_interval_spin = QDoubleSpinBox()
        self.hello_interval_spin.setRange(0.1, 60.0)
        self.hello_interval_spin.setValue(self.config['protocol']['hello_interval'])
        self.hello_interval_spin.setSingleStep(0.1)
        self.hello_interval_spin.valueChanged.connect(self.config_changed_handler)
        dual_layout.addWidget(self.hello_interval_spin, 0, 1)
        
        # Hold time
        dual_layout.addWidget(QLabel("Hold Time (s):"), 1, 0)
        self.hold_time_spin = QDoubleSpinBox()
        self.hold_time_spin.setRange(1.0, 300.0)
        self.hold_time_spin.setValue(self.config['protocol']['hold_time'])
        self.hold_time_spin.valueChanged.connect(self.config_changed_handler)
        dual_layout.addWidget(self.hold_time_spin, 1, 1)
        
        # Active time
        dual_layout.addWidget(QLabel("Active Time (s):"), 2, 0)
        self.active_time_spin = QDoubleSpinBox()
        self.active_time_spin.setRange(0.1, 60.0)
        self.active_time_spin.setValue(self.config['protocol']['active_time'])
        self.active_time_spin.valueChanged.connect(self.config_changed_handler)
        dual_layout.addWidget(self.active_time_spin, 2, 1)
        
        layout.addWidget(dual_group)
        
        # Multi-Armed Bandit settings
        mab_group = QGroupBox("Multi-Armed Bandit Settings")
        mab_layout = QGridLayout(mab_group)
        mab_layout.setSpacing(3)  # Reduce spacing
        mab_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        
        # Exploration rate
        mab_layout.addWidget(QLabel("Exploration Rate:"), 0, 0)
        self.exploration_rate_spin = QDoubleSpinBox()
        self.exploration_rate_spin.setRange(0.0, 1.0)
        self.exploration_rate_spin.setValue(self.config['mab']['exploration_rate'])
        self.exploration_rate_spin.setSingleStep(0.01)
        self.exploration_rate_spin.valueChanged.connect(self.config_changed_handler)
        mab_layout.addWidget(self.exploration_rate_spin, 0, 1)
        
        # Learning rate
        mab_layout.addWidget(QLabel("Learning Rate:"), 1, 0)
        self.learning_rate_spin = QDoubleSpinBox()
        self.learning_rate_spin.setRange(0.001, 1.0)
        self.learning_rate_spin.setValue(self.config['mab']['learning_rate'])
        self.learning_rate_spin.setSingleStep(0.001)
        self.learning_rate_spin.valueChanged.connect(self.config_changed_handler)
        mab_layout.addWidget(self.learning_rate_spin, 1, 1)
        
        # Memory window
        mab_layout.addWidget(QLabel("Memory Window:"), 2, 0)
        self.memory_window_spin = QSpinBox()
        self.memory_window_spin.setRange(10, 1000)
        self.memory_window_spin.setValue(self.config['mab']['memory_window'])
        self.memory_window_spin.valueChanged.connect(self.config_changed_handler)
        mab_layout.addWidget(self.memory_window_spin, 2, 1)
        
        layout.addWidget(mab_group)
        
        layout.addStretch()
        return widget
        
    def create_network_tab(self):
        """Create network parameters tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Metric weights
        metrics_group = QGroupBox("Metric Weights")
        metrics_layout = QGridLayout(metrics_group)
        metrics_layout.setSpacing(3)
        metrics_layout.setContentsMargins(5, 10, 5, 5)
        
        # Delay weight
        metrics_layout.addWidget(QLabel("Delay Weight:"), 0, 0)
        self.delay_weight_spin = QDoubleSpinBox()
        self.delay_weight_spin.setRange(0.0, 10.0)
        self.delay_weight_spin.setValue(self.config['metrics']['delay_weight'])
        self.delay_weight_spin.setSingleStep(0.1)
        self.delay_weight_spin.valueChanged.connect(self.config_changed_handler)
        metrics_layout.addWidget(self.delay_weight_spin, 0, 1)
        
        # Jitter weight
        metrics_layout.addWidget(QLabel("Jitter Weight:"), 1, 0)
        self.jitter_weight_spin = QDoubleSpinBox()
        self.jitter_weight_spin.setRange(0.0, 10.0)
        self.jitter_weight_spin.setValue(self.config['metrics']['jitter_weight'])
        self.jitter_weight_spin.setSingleStep(0.1)
        self.jitter_weight_spin.valueChanged.connect(self.config_changed_handler)
        metrics_layout.addWidget(self.jitter_weight_spin, 1, 1)
        
        # Packet loss weight
        metrics_layout.addWidget(QLabel("Packet Loss Weight:"), 2, 0)
        self.loss_weight_spin = QDoubleSpinBox()
        self.loss_weight_spin.setRange(0.0, 10.0)
        self.loss_weight_spin.setValue(self.config['metrics']['packet_loss_weight'])
        self.loss_weight_spin.setSingleStep(0.1)
        self.loss_weight_spin.valueChanged.connect(self.config_changed_handler)
        metrics_layout.addWidget(self.loss_weight_spin, 2, 1)
        
        # Congestion weight
        metrics_layout.addWidget(QLabel("Congestion Weight:"), 3, 0)
        self.congestion_weight_spin = QDoubleSpinBox()
        self.congestion_weight_spin.setRange(0.0, 10.0)
        self.congestion_weight_spin.setValue(self.config['metrics']['congestion_weight'])
        self.congestion_weight_spin.setSingleStep(0.1)
        self.congestion_weight_spin.valueChanged.connect(self.config_changed_handler)
        metrics_layout.addWidget(self.congestion_weight_spin, 3, 1)
        
        # Stability weight
        metrics_layout.addWidget(QLabel("Stability Weight:"), 4, 0)
        self.stability_weight_spin = QDoubleSpinBox()
        self.stability_weight_spin.setRange(0.0, 10.0)
        self.stability_weight_spin.setValue(self.config['metrics']['stability_weight'])
        self.stability_weight_spin.setSingleStep(0.1)
        self.stability_weight_spin.valueChanged.connect(self.config_changed_handler)
        metrics_layout.addWidget(self.stability_weight_spin, 4, 1)
        
        layout.addWidget(metrics_group)
        
        # Link parameters
        link_group = QGroupBox("Default Link Parameters")
        link_layout = QGridLayout(link_group)
        
        # Default delay range
        link_layout.addWidget(QLabel("Delay Range (ms):"), 0, 0)
        delay_layout = QHBoxLayout()
        self.min_delay_spin = QSpinBox()
        self.min_delay_spin.setRange(1, 1000)
        self.min_delay_spin.setValue(self.config['links']['min_delay'])
        self.min_delay_spin.valueChanged.connect(self.config_changed_handler)
        delay_layout.addWidget(self.min_delay_spin)
        delay_layout.addWidget(QLabel("to"))
        self.max_delay_spin = QSpinBox()
        self.max_delay_spin.setRange(1, 1000)
        self.max_delay_spin.setValue(self.config['links']['max_delay'])
        self.max_delay_spin.valueChanged.connect(self.config_changed_handler)
        delay_layout.addWidget(self.max_delay_spin)
        link_layout.addLayout(delay_layout, 0, 1)
        
        # Default packet loss range
        link_layout.addWidget(QLabel("Packet Loss Range (%):"), 1, 0)
        loss_layout = QHBoxLayout()
        self.min_loss_spin = QDoubleSpinBox()
        self.min_loss_spin.setRange(0.0, 50.0)
        self.min_loss_spin.setValue(self.config['links']['min_packet_loss'])
        self.min_loss_spin.setSingleStep(0.1)
        self.min_loss_spin.valueChanged.connect(self.config_changed_handler)
        loss_layout.addWidget(self.min_loss_spin)
        loss_layout.addWidget(QLabel("to"))
        self.max_loss_spin = QDoubleSpinBox()
        self.max_loss_spin.setRange(0.0, 50.0)
        self.max_loss_spin.setValue(self.config['links']['max_packet_loss'])
        self.max_loss_spin.setSingleStep(0.1)
        self.max_loss_spin.valueChanged.connect(self.config_changed_handler)
        loss_layout.addWidget(self.max_loss_spin)
        link_layout.addLayout(loss_layout, 1, 1)
        
        layout.addWidget(link_group)
        layout.addStretch()
        return widget
        
    def create_simulation_tab(self):
        """Create simulation parameters tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Simulation settings
        sim_group = QGroupBox("Simulation Settings")
        sim_layout = QGridLayout(sim_group)
        
        # Simulation speed
        sim_layout.addWidget(QLabel("Simulation Speed:"), 0, 0)
        self.sim_speed_spin = QDoubleSpinBox()
        self.sim_speed_spin.setRange(0.1, 10.0)
        self.sim_speed_spin.setValue(self.config['simulation']['speed'])
        self.sim_speed_spin.setSingleStep(0.1)
        self.sim_speed_spin.valueChanged.connect(self.config_changed_handler)
        sim_layout.addWidget(self.sim_speed_spin, 0, 1)
        
        # Update interval
        sim_layout.addWidget(QLabel("Update Interval (ms):"), 1, 0)
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(10, 5000)
        self.update_interval_spin.setValue(self.config['simulation']['update_interval'])
        self.update_interval_spin.valueChanged.connect(self.config_changed_handler)
        sim_layout.addWidget(self.update_interval_spin, 1, 1)
        
        # Auto-save interval
        sim_layout.addWidget(QLabel("Auto-save Interval (s):"), 2, 0)
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(0, 3600)
        self.autosave_interval_spin.setValue(self.config['simulation']['autosave_interval'])
        self.autosave_interval_spin.valueChanged.connect(self.config_changed_handler)
        sim_layout.addWidget(self.autosave_interval_spin, 2, 1)
        
        layout.addWidget(sim_group)
        
        # Visualization settings
        viz_group = QGroupBox("Visualization Settings")
        viz_layout = QGridLayout(viz_group)
        
        # Show packet animations
        self.show_packets_cb = QCheckBox("Show Packet Animations")
        self.show_packets_cb.setChecked(self.config['visualization']['show_packets'])
        self.show_packets_cb.toggled.connect(self.config_changed_handler)
        viz_layout.addWidget(self.show_packets_cb, 0, 0, 1, 2)
        
        # Show router labels
        self.show_labels_cb = QCheckBox("Show Router Labels")
        self.show_labels_cb.setChecked(self.config['visualization']['show_labels'])
        self.show_labels_cb.toggled.connect(self.config_changed_handler)
        viz_layout.addWidget(self.show_labels_cb, 1, 0, 1, 2)
        
        # Show link metrics
        self.show_metrics_cb = QCheckBox("Show Link Metrics")
        self.show_metrics_cb.setChecked(self.config['visualization']['show_metrics'])
        self.show_metrics_cb.toggled.connect(self.config_changed_handler)
        viz_layout.addWidget(self.show_metrics_cb, 2, 0, 1, 2)
        
        # Animation speed
        viz_layout.addWidget(QLabel("Animation Speed:"), 3, 0)
        self.anim_speed_spin = QDoubleSpinBox()
        self.anim_speed_spin.setRange(0.1, 5.0)
        self.anim_speed_spin.setValue(self.config['visualization']['animation_speed'])
        self.anim_speed_spin.setSingleStep(0.1)
        self.anim_speed_spin.valueChanged.connect(self.config_changed_handler)
        viz_layout.addWidget(self.anim_speed_spin, 3, 1)
        
        layout.addWidget(viz_group)
        layout.addStretch()
        return widget
        
    def create_advanced_tab(self):
        """Create advanced parameters tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Advanced DUAL settings
        dual_advanced_group = QGroupBox("Advanced DUAL Settings")
        dual_advanced_layout = QGridLayout(dual_advanced_group)
        
        # Feasible successor threshold
        dual_advanced_layout.addWidget(QLabel("Feasible Successor Threshold:"), 0, 0)
        self.fs_threshold_spin = QDoubleSpinBox()
        self.fs_threshold_spin.setRange(1.0, 10.0)
        self.fs_threshold_spin.setValue(self.config['advanced']['feasible_successor_threshold'])
        self.fs_threshold_spin.setSingleStep(0.1)
        self.fs_threshold_spin.valueChanged.connect(self.config_changed_handler)
        dual_advanced_layout.addWidget(self.fs_threshold_spin, 0, 1)
        
        # Query response timeout
        dual_advanced_layout.addWidget(QLabel("Query Response Timeout (s):"), 1, 0)
        self.query_timeout_spin = QDoubleSpinBox()
        self.query_timeout_spin.setRange(1.0, 60.0)
        self.query_timeout_spin.setValue(self.config['advanced']['query_response_timeout'])
        self.query_timeout_spin.valueChanged.connect(self.config_changed_handler)
        dual_advanced_layout.addWidget(self.query_timeout_spin, 1, 1)
        
        # Stuck in active timer
        dual_advanced_layout.addWidget(QLabel("Stuck in Active Timer (s):"), 2, 0)
        self.sia_timer_spin = QDoubleSpinBox()
        self.sia_timer_spin.setRange(60.0, 600.0)
        self.sia_timer_spin.setValue(self.config['advanced']['stuck_in_active_timer'])
        self.sia_timer_spin.valueChanged.connect(self.config_changed_handler)
        dual_advanced_layout.addWidget(self.sia_timer_spin, 2, 1)
        
        layout.addWidget(dual_advanced_group)
        
        # Debugging options
        debug_group = QGroupBox("Debugging Options")
        debug_layout = QGridLayout(debug_group)
        
        # Enable debug logging
        self.debug_logging_cb = QCheckBox("Enable Debug Logging")
        self.debug_logging_cb.setChecked(self.config['debug']['enable_logging'])
        self.debug_logging_cb.toggled.connect(self.config_changed_handler)
        debug_layout.addWidget(self.debug_logging_cb, 0, 0, 1, 2)
        
        # Log level
        debug_layout.addWidget(QLabel("Log Level:"), 1, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.config['debug']['log_level'])
        self.log_level_combo.currentTextChanged.connect(self.config_changed_handler)
        debug_layout.addWidget(self.log_level_combo, 1, 1)
        
        # Packet capture
        self.packet_capture_cb = QCheckBox("Enable Packet Capture")
        self.packet_capture_cb.setChecked(self.config['debug']['packet_capture'])
        self.packet_capture_cb.toggled.connect(self.config_changed_handler)
        debug_layout.addWidget(self.packet_capture_cb, 2, 0, 1, 2)
        
        layout.addWidget(debug_group)
        layout.addStretch()
        return widget
        
    def create_button_panel(self):
        """Create action buttons panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        layout = QHBoxLayout(panel)
        
        # Load defaults button
        defaults_btn = QPushButton("Load Defaults")
        defaults_btn.clicked.connect(self.load_defaults)
        layout.addWidget(defaults_btn)
        
        # Load from file button
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self.load_from_file)
        layout.addWidget(load_btn)
        
        # Save to file button
        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self.save_to_file)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        # Apply button
        apply_btn = QPushButton("Apply Configuration")
        apply_btn.clicked.connect(self.apply_configuration)
        layout.addWidget(apply_btn)
        
        return panel
        
    def get_default_config(self):
        """Get default configuration"""
        return {
            'protocol': {
                'hello_interval': 20.0,
                'hold_time': 15.0,
                'active_time': 3.0
            },
            'mab': {
                'exploration_rate': 0.1,
                'learning_rate': 0.01,
                'memory_window': 100
            },
            'metrics': {
                'delay_weight': 1.0,
                'jitter_weight': 0.5,
                'packet_loss_weight': 2.0,
                'congestion_weight': 1.5,
                'stability_weight': 1.0
            },
            'links': {
                'min_delay': 10,
                'max_delay': 100,
                'min_packet_loss': 0.0,
                'max_packet_loss': 10.0
            },
            'simulation': {
                'speed': 1.0,
                'update_interval': 100,
                'autosave_interval': 300
            },
            'visualization': {
                'show_packets': True,
                'show_labels': True,
                'show_metrics': False,
                'animation_speed': 1.0
            },
            'advanced': {
                'feasible_successor_threshold': 2.0,
                'query_response_timeout': 30.0,
                'stuck_in_active_timer': 180.0
            },
            'debug': {
                'enable_logging': False,
                'log_level': 'INFO',
                'packet_capture': False
            }
        }
        
    def config_changed_handler(self):
        """Handle configuration parameter changes"""
        self.update_config_from_ui()
        self.config_changed.emit(self.config)
        
    def update_config_from_ui(self):
        """Update configuration from UI values"""
        # Protocol settings
        self.config['protocol']['hello_interval'] = self.hello_interval_spin.value()
        self.config['protocol']['hold_time'] = self.hold_time_spin.value()
        self.config['protocol']['active_time'] = self.active_time_spin.value()
        
        # MAB settings
        self.config['mab']['exploration_rate'] = self.exploration_rate_spin.value()
        self.config['mab']['learning_rate'] = self.learning_rate_spin.value()
        self.config['mab']['memory_window'] = self.memory_window_spin.value()
        
        # Metric weights
        self.config['metrics']['delay_weight'] = self.delay_weight_spin.value()
        self.config['metrics']['jitter_weight'] = self.jitter_weight_spin.value()
        self.config['metrics']['packet_loss_weight'] = self.loss_weight_spin.value()
        self.config['metrics']['congestion_weight'] = self.congestion_weight_spin.value()
        self.config['metrics']['stability_weight'] = self.stability_weight_spin.value()
        
        # Link parameters
        self.config['links']['min_delay'] = self.min_delay_spin.value()
        self.config['links']['max_delay'] = self.max_delay_spin.value()
        self.config['links']['min_packet_loss'] = self.min_loss_spin.value()
        self.config['links']['max_packet_loss'] = self.max_loss_spin.value()
        
        # Simulation settings
        self.config['simulation']['speed'] = self.sim_speed_spin.value()
        self.config['simulation']['update_interval'] = self.update_interval_spin.value()
        self.config['simulation']['autosave_interval'] = self.autosave_interval_spin.value()
        
        # Visualization settings
        self.config['visualization']['show_packets'] = self.show_packets_cb.isChecked()
        self.config['visualization']['show_labels'] = self.show_labels_cb.isChecked()
        self.config['visualization']['show_metrics'] = self.show_metrics_cb.isChecked()
        self.config['visualization']['animation_speed'] = self.anim_speed_spin.value()
        
        # Advanced settings
        self.config['advanced']['feasible_successor_threshold'] = self.fs_threshold_spin.value()
        self.config['advanced']['query_response_timeout'] = self.query_timeout_spin.value()
        self.config['advanced']['stuck_in_active_timer'] = self.sia_timer_spin.value()
        
        # Debug settings
        self.config['debug']['enable_logging'] = self.debug_logging_cb.isChecked()
        self.config['debug']['log_level'] = self.log_level_combo.currentText()
        self.config['debug']['packet_capture'] = self.packet_capture_cb.isChecked()
        
    def load_defaults(self):
        """Load default configuration"""
        self.config = self.get_default_config()
        self.update_ui_from_config()
        
    def update_ui_from_config(self):
        """Update UI from current configuration"""
        # This would set all UI elements from config values
        # For brevity, implementing key ones
        self.hello_interval_spin.setValue(self.config['protocol']['hello_interval'])
        self.exploration_rate_spin.setValue(self.config['mab']['exploration_rate'])
        self.delay_weight_spin.setValue(self.config['metrics']['delay_weight'])
        # ... and so on for all parameters
        
    def load_from_file(self):
        """Load configuration from file"""
        # TODO: Implement file loading
        print("Load from file functionality not yet implemented")
        
    def save_to_file(self):
        """Save configuration to file"""
        # TODO: Implement file saving
        print("Save to file functionality not yet implemented")
        
    def apply_configuration(self):
        """Apply current configuration"""
        self.update_config_from_ui()
        self.config_changed.emit(self.config)
        
    def get_config(self):
        """Get current configuration"""
        self.update_config_from_ui()
        return self.config.copy()
        
    def set_config(self, config):
        """Set configuration"""
        self.config = config.copy()
        self.update_ui_from_config()
        
    def clear(self):
        """Clear configuration (reset to defaults)"""
        self.load_defaults()
        
    def create_scrollable_tab(self, content_widget):
        """Create a scrollable tab wrapper for content"""
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        return scroll_area
