"""
Routing Table Widget for ADUP
Display and manage routing tables for all routers
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QHeaderView, QLabel, QComboBox,
                            QGroupBox, QSplitter, QFrame, QPushButton, QCheckBox,
                            QLineEdit, QSpacerItem, QSizePolicy, QTabWidget,
                            QScrollArea, QGridLayout, QProgressBar, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette


class RoutingTableWidget(QWidget):
    """Enhanced Widget for displaying routing tables"""
    
    def __init__(self):
        super().__init__()
        self.routers_data = {}
        self.current_router = None
        self.auto_refresh = True
        self.filter_text = ""
        self.route_filter = None
        
        # Initialize UI
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_tables)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
        
    def init_ui(self):
        """Initialize the enhanced user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Compact control panel
        control_panel = self.create_compact_control_panel()
        layout.addWidget(control_panel)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Routing Tables Tab
        routing_tab = QWidget()
        self.create_routing_tables_tab(routing_tab)
        self.tab_widget.addTab(routing_tab, "Routing Tables")
        
        # Network Overview Tab
        overview_tab = QWidget()
        self.create_network_overview_tab(overview_tab)
        self.tab_widget.addTab(overview_tab, "Network Overview")
        
        # Route Analysis Tab
        analysis_tab = QWidget()
        self.create_route_analysis_tab(analysis_tab)
        self.tab_widget.addTab(analysis_tab, "Route Analysis")
        
    def create_compact_control_panel(self):
        """Create a compact control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(50)
        panel.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #4a4a4a;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        # Router selection - properly sized
        router_label = QLabel("Router:")
        router_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(router_label)
        
        self.router_combo = QComboBox()
        self.router_combo.setFixedWidth(150)  # Increased width for better visibility
        self.router_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                background-color: #3c3c3c;
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
            }
            QComboBox:hover {
                border-color: #666666;
                background-color: #4a4a4a;
            }
            QComboBox:focus {
                border-color: #666666;
                background-color: #404040;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
        """)
        self.router_combo.currentTextChanged.connect(self.router_selected)
        layout.addWidget(self.router_combo)
        
        # Vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #dee2e6;")
        layout.addWidget(separator)
        
        # Filter with icon
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(filter_label)
        
        self.filter_input = QLineEdit()
        self.filter_input.setFixedWidth(180)
        self.filter_input.setPlaceholderText("Search destinations...")
        self.filter_input.setStyleSheet("""
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #666666;
                outline: none;
            }
        """)
        self.filter_input.textChanged.connect(self.filter_changed)
        layout.addWidget(self.filter_input)
        
        # Vertical separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("color: #dee2e6;")
        layout.addWidget(separator2)
        
        # Auto-refresh checkbox
        self.auto_refresh_cb = QCheckBox("Auto-refresh")
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #ffffff;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #4a4a4a;
                background-color: #3c3c3c;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #666666;
                background-color: #666666;
                border-radius: 3px;
            }
        """)
        self.auto_refresh_cb.toggled.connect(self.toggle_auto_refresh)
        layout.addWidget(self.auto_refresh_cb)
        
        # Spacer
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Action buttons with better styling
        button_style = """
            QPushButton {
                background-color: #666666;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(button_style)
        refresh_btn.setStyleSheet(button_style)
        refresh_btn.setToolTip("Refresh Tables")
        refresh_btn.clicked.connect(self.refresh_tables)
        layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(button_style.replace("#666666", "#28a745").replace("#777777", "#1e7e34").replace("#555555", "#155724"))
        export_btn.setToolTip("Export Tables")
        export_btn.clicked.connect(self.export_tables)
        layout.addWidget(export_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(button_style.replace("#666666", "#dc3545").replace("#777777", "#c82333").replace("#555555", "#bd2130"))
        clear_btn.setToolTip("Clear Tables")
        clear_btn.clicked.connect(self.clear)
        layout.addWidget(clear_btn)
        
        return panel
    def create_routing_tables_tab(self, parent):
        """Create the main routing tables tab with improved layout"""
        main_layout = QHBoxLayout(parent)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Router status and statistics (compact)
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Router status header with better styling
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #666666;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 6, 8, 6)
        
        header_label = QLabel("Router Status")
        header_label.setStyleSheet("font-weight: bold; font-size: 13px; color: white;")
        header_layout.addWidget(header_label)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #90EE90; font-size: 16px;")
        self.status_indicator.setToolTip("Network Status")
        header_layout.addWidget(self.status_indicator)
        
        left_layout.addWidget(header_frame)
        
        # Router status table with better styling
        self.router_table = QTableWidget()
        self.router_table.setColumnCount(4)
        self.router_table.setHorizontalHeaderLabels(["Router", "Status", "Routes", "Avg Cost"])
        self.router_table.setMaximumHeight(200)
        self.router_table.setMinimumHeight(150)
        
        # Configure table appearance
        self.router_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #4a4a4a;
                background-color: #2b2b2b;
                alternate-background-color: #3c3c3c;
                selection-background-color: #666666;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #666666;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #4a4a4a;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        
        # Configure table headers
        header = self.router_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.router_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.router_table.itemSelectionChanged.connect(self.router_table_selection_changed)
        self.router_table.setAlternatingRowColors(True)
        self.router_table.verticalHeader().setVisible(False)
        
        left_layout.addWidget(self.router_table)
        
        # Quick actions panel
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #ffffff;
            }
        """)
        actions_layout = QVBoxLayout(actions_group)
        
        # Quick action buttons
        action_button_style = """
            QPushButton {
                background-color: #4a4a4a;
                color: white;
                border: 1px solid #666666;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #555555;
                border-color: #777777;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """
        
        show_direct_btn = QPushButton("Show Direct Routes Only")
        show_direct_btn.setStyleSheet(action_button_style)
        show_direct_btn.clicked.connect(self.show_direct_routes_only)
        actions_layout.addWidget(show_direct_btn)
        
        show_all_btn = QPushButton("Show All Routes")
        show_all_btn.setStyleSheet(action_button_style)
        show_all_btn.clicked.connect(self.show_all_routes)
        actions_layout.addWidget(show_all_btn)
        
        sort_by_cost_btn = QPushButton("Sort by Cost")
        sort_by_cost_btn.setStyleSheet(action_button_style)
        sort_by_cost_btn.clicked.connect(self.sort_by_cost)
        actions_layout.addWidget(sort_by_cost_btn)
        
        left_layout.addWidget(actions_group)
        left_layout.addStretch()
        
        # Right panel - Main routing table (larger and cleaner)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Router info header with better styling
        self.router_info_label = QLabel("Select a router to view its routing table")
        self.router_info_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                font-size: 16px; 
                color: #FFFFFF; 
                padding: 15px; 
                background-color: #4a4a4a; 
                border: 1px solid #666666;
                border-radius: 8px;
                margin-bottom: 10px;
                text-align: center;
            }
        """)
        right_layout.addWidget(self.router_info_label)
        
        # Enhanced routing table with better styling
        self.routing_table = QTableWidget()
        self.routing_table.setColumnCount(7)  # Added one more column
        self.routing_table.setHorizontalHeaderLabels([
            "Destination", "Next Hop", "Cost", "Metric", 
            "Status", "Updated", "Interface"
        ])
        
        # Enhanced table styling
        self.routing_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #4a4a4a;
                background-color: #2b2b2b;
                alternate-background-color: #3c3c3c;
                selection-background-color: #666666;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                font-size: 13px;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #666666;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            QTableWidgetItem {
                padding: 8px;
                border-bottom: 1px solid #4a4a4a;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #4a9eff;
                color: white;
            }
        """)
        
        # Configure enhanced table headers
        header = self.routing_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Destination
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Next Hop
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Cost
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Metric
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Updated
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Interface
        
        self.routing_table.setAlternatingRowColors(True)
        self.routing_table.setSortingEnabled(True)
        self.routing_table.setShowGrid(True)
        self.routing_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.routing_table.verticalHeader().setVisible(False)
        
        # Enable row selection
        self.routing_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        right_layout.addWidget(self.routing_table)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (left panel smaller, right panel larger)
        splitter.setSizes([300, 700])
        
    def create_network_overview_tab(self, parent):
        """Create network overview tab"""
        layout = QVBoxLayout(parent)
        
        # Network topology summary
        summary_group = QGroupBox("Network Topology Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.network_size_label = QLabel("Network Size: 0 routers")
        self.connectivity_label = QLabel("Connectivity: 0%")
        self.diameter_label = QLabel("Network Diameter: 0 hops")
        self.convergence_label = QLabel("Convergence Status: Unknown")
        
        summary_layout.addWidget(self.network_size_label, 0, 0)
        summary_layout.addWidget(self.connectivity_label, 0, 1)
        summary_layout.addWidget(self.diameter_label, 1, 0)
        summary_layout.addWidget(self.convergence_label, 1, 1)
        
        layout.addWidget(summary_group)
        
        # Router comparison table
        comparison_group = QGroupBox("Router Comparison")
        comparison_layout = QVBoxLayout(comparison_group)
        
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(6)
        self.comparison_table.setHorizontalHeaderLabels([
            "Router", "Networks", "Neighbors", "Routes", "Avg Cost", "Status"
        ])
        
        # Configure comparison table
        header = self.comparison_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.setSortingEnabled(True)
        
        comparison_layout.addWidget(self.comparison_table)
        layout.addWidget(comparison_group)
        
    def create_route_analysis_tab(self, parent):
        """Create route analysis tab"""
        layout = QVBoxLayout(parent)
        
        # Analysis controls
        controls_group = QGroupBox("Route Analysis Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Source:"))
        self.source_combo = QComboBox()
        controls_layout.addWidget(self.source_combo)
        
        controls_layout.addWidget(QLabel("Destination:"))
        self.dest_combo = QComboBox()
        controls_layout.addWidget(self.dest_combo)
        
        analyze_btn = QPushButton("Analyze Path")
        analyze_btn.clicked.connect(self.analyze_path)
        controls_layout.addWidget(analyze_btn)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)
        
        # Path analysis results
        results_group = QGroupBox("Path Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.path_info_label = QLabel("Select source and destination to analyze path")
        self.path_info_label.setStyleSheet("font-weight: bold; color: #2E86AB;")
        results_layout.addWidget(self.path_info_label)
        
        self.path_table = QTableWidget()
        self.path_table.setColumnCount(4)
        self.path_table.setHorizontalHeaderLabels([
            "Hop", "Router", "Cost", "Cumulative Cost"
        ])
        
        header = self.path_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.path_table.setAlternatingRowColors(True)
        
        results_layout.addWidget(self.path_table)
        layout.addWidget(results_group)
        
    def update_state(self, state):
        """Update routing tables with new simulation state"""
        self.routers_data = state.get('routers', {})
        
        # Update router combo box
        current_selection = self.router_combo.currentText()
        self.router_combo.clear()
        
        if not self.routers_data:
            # Handle empty state
            self.router_info_label.setText("No simulation data available - Start the simulation to see routing tables")
            self.routing_table.setRowCount(1)
            empty_item = QTableWidgetItem("Start the simulation to see routing data")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            empty_item.setBackground(QColor(60, 60, 60))
            empty_item.setForeground(QColor(255, 165, 0))  # Orange for warning
            self.routing_table.setItem(0, 0, empty_item)
            for col in range(1, 7):
                empty_col_item = QTableWidgetItem("")
                empty_col_item.setFlags(empty_col_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                empty_col_item.setBackground(QColor(60, 60, 60))
                self.routing_table.setItem(0, col, empty_col_item)
            return
        
        # Add router options
        self.router_combo.addItems(sorted(self.routers_data.keys()))
        
        # Restore selection if possible
        if current_selection and current_selection in self.routers_data:
            self.router_combo.setCurrentText(current_selection)
        elif self.routers_data:
            self.router_combo.setCurrentText(sorted(self.routers_data.keys())[0])
            
        # Update router status table
        self.update_router_status_table()
        
        # Update routing table if a router is selected
        if self.current_router and self.current_router in self.routers_data:
            self.update_routing_table()
            
    def update_router_status_table(self):
        """Update the router status table"""
        self.router_table.setRowCount(len(self.routers_data))
        
        for row, (router_id, router_info) in enumerate(sorted(self.routers_data.items())):
            # Router ID
            id_item = QTableWidgetItem(router_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.router_table.setItem(row, 0, id_item)
            
            # Status
            neighbors = router_info.get('neighbors', [])
            status = "Active" if neighbors else "Isolated"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color code status
            if status == "Active":
                status_item.setBackground(QColor(46, 125, 50))  # Dark green
                status_item.setForeground(QColor(255, 255, 255))
            else:
                status_item.setBackground(QColor(183, 28, 28))  # Dark red
                status_item.setForeground(QColor(255, 255, 255))
                
            self.router_table.setItem(row, 1, status_item)
            
            # Number of routes
            # Check for both 'routing_table' and 'fib' fields (simulation uses 'fib')
            routing_table = router_info.get('routing_table', router_info.get('fib', {}))
            route_count = len(routing_table)
            count_item = QTableWidgetItem(str(route_count))
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.router_table.setItem(row, 2, count_item)
            
            # Average cost calculation
            if routing_table:
                costs = []
                for route_info in routing_table.values():
                    if isinstance(route_info, dict):
                        if 'cost' in route_info:
                            costs.append(route_info.get('cost', 0))
                        elif 'metrics' in route_info:
                            # Handle fib format where cost is in metrics
                            metrics = route_info.get('metrics', {})
                            cost = metrics.get('total_cost', metrics.get('total_delay', metrics.get('cost', 0)))
                            costs.append(cost)
                        elif 'delay' in route_info:
                            costs.append(route_info.get('delay', 0))
                        elif 'weight' in route_info:
                            costs.append(route_info.get('weight', 0))
                        else:
                            costs.append(1)  # Default cost for valid routes
                    else:
                        costs.append(1)  # Default cost for non-dict routes
                
                avg_cost = sum(costs) / len(costs) if costs else 0
            else:
                avg_cost = 0
                
            # Format cost display based on magnitude
            if avg_cost >= 1000:
                cost_display = f"{avg_cost/1000:.1f}k"
            elif avg_cost >= 100:
                cost_display = f"{avg_cost:.0f}"
            else:
                cost_display = f"{avg_cost:.1f}"
                
            avg_cost_item = QTableWidgetItem(cost_display)
            avg_cost_item.setFlags(avg_cost_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color code based on average cost (adjusted thresholds for realistic values)
            if avg_cost == 0:
                avg_cost_item.setBackground(QColor(96, 96, 96))  # Gray for no routes
                avg_cost_item.setForeground(QColor(255, 255, 255))
            elif avg_cost < 1000:
                avg_cost_item.setBackground(QColor(46, 125, 50))  # Dark green for low cost
                avg_cost_item.setForeground(QColor(255, 255, 255))
            elif avg_cost < 5000:
                avg_cost_item.setBackground(QColor(156, 111, 39))  # Dark yellow/brown for medium cost
                avg_cost_item.setForeground(QColor(255, 255, 255))
            else:
                avg_cost_item.setBackground(QColor(183, 28, 28))  # Dark red for high cost
                avg_cost_item.setForeground(QColor(255, 255, 255))
                
            self.router_table.setItem(row, 3, avg_cost_item)
            
    def update_routing_table(self):
        """Update the routing table for current router"""
        if not self.current_router or self.current_router not in self.routers_data:
            self.routing_table.setRowCount(0)
            self.router_info_label.setText("No router selected - Choose a router from the dropdown above")
            return
            
        router_info = self.routers_data[self.current_router]
        # Check for both 'routing_table' and 'fib' fields (simulation uses 'fib')
        routing_table = router_info.get('routing_table', router_info.get('fib', {}))
        
        # Apply filter if set
        if self.filter_text:
            filtered_table = {dest: route for dest, route in routing_table.items() 
                            if self.filter_text in dest.lower()}
        else:
            filtered_table = routing_table
            
        # Apply route filter for direct routes only
        if self.route_filter == "direct":
            filtered_table = {dest: route for dest, route in filtered_table.items() 
                            if route.get('next_hop', '') in ['Direct', 'self']}
        
        # Update router info label with better formatting
        neighbors = router_info.get('neighbors', [])
        networks = router_info.get('networks', [])
        filter_info = ""
        if self.route_filter == "direct":
            filter_info = " [DIRECT ROUTES ONLY]"
        elif self.filter_text:
            filter_info = f" [FILTERED: '{self.filter_text}']"
            
        self.router_info_label.setText(
            f"Router {self.current_router} - Networks: {len(networks)} - "
            f"Neighbors: {len(neighbors)} - Routes: {len(filtered_table)}/{len(routing_table)}{filter_info}"
        )
        
        # Handle empty routing table
        if not filtered_table:
            self.routing_table.setRowCount(1)
            empty_item = QTableWidgetItem("No routes available for this router")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            empty_item.setBackground(QColor(60, 60, 60))
            empty_item.setForeground(QColor(170, 170, 170))
            self.routing_table.setItem(0, 0, empty_item)
            
            # Clear other columns
            for col in range(1, 7):
                empty_col_item = QTableWidgetItem("")
                empty_col_item.setFlags(empty_col_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                empty_col_item.setBackground(QColor(60, 60, 60))
                self.routing_table.setItem(0, col, empty_col_item)
            return
        
        # Update table with actual data
        self.routing_table.setRowCount(len(filtered_table))
        
        for row, (destination, route_info) in enumerate(sorted(filtered_table.items())):
            # Destination
            dest_item = QTableWidgetItem(destination)
            dest_item.setFlags(dest_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.routing_table.setItem(row, 0, dest_item)
            
            # Next hop - handle both routing_table and fib formats
            if isinstance(route_info, dict):
                if 'next_hop' in route_info:
                    next_hop = route_info.get('next_hop', 'Direct')
                elif 'gateway' in route_info:
                    next_hop = route_info.get('gateway', 'Direct')
                else:
                    next_hop = 'Direct'
            else:
                # Handle cases where route_info might be a string or other type
                next_hop = str(route_info) if route_info else 'Direct'
            
            next_hop_item = QTableWidgetItem(str(next_hop))
            next_hop_item.setFlags(next_hop_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color code based on next hop
            if next_hop == 'Direct' or next_hop == 'self':
                next_hop_item.setBackground(QColor(46, 125, 50))  # Dark green
                next_hop_item.setForeground(QColor(255, 255, 255))
            else:
                next_hop_item.setBackground(QColor(156, 111, 39))  # Dark yellow/brown
                next_hop_item.setForeground(QColor(255, 255, 255))
                
            self.routing_table.setItem(row, 1, next_hop_item)
            
            # Cost - handle both routing_table and fib formats
            if isinstance(route_info, dict):
                if 'cost' in route_info:
                    cost = route_info.get('cost', 0)
                elif 'metrics' in route_info:
                    # Handle fib format where cost is in metrics
                    metrics = route_info.get('metrics', {})
                    cost = metrics.get('total_cost', metrics.get('total_delay', metrics.get('cost', 0)))
                elif 'delay' in route_info:
                    cost = route_info.get('delay', 0)
                elif 'weight' in route_info:
                    cost = route_info.get('weight', 0)
                else:
                    cost = 1  # Default cost for valid routes
            else:
                cost = 1  # Default cost for non-dict routes
            
            # Format cost display based on magnitude
            if cost >= 1000:
                cost_display = f"{cost/1000:.1f}k"
            elif cost >= 100:
                cost_display = f"{cost:.0f}"
            else:
                cost_display = f"{cost:.1f}"
                
            cost_item = QTableWidgetItem(cost_display)
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color code based on cost (adjusted thresholds for realistic values)
            if cost < 1000:
                cost_item.setBackground(QColor(46, 125, 50))  # Dark green
                cost_item.setForeground(QColor(255, 255, 255))
            elif cost < 5000:
                cost_item.setBackground(QColor(156, 111, 39))  # Dark yellow/brown
                cost_item.setForeground(QColor(255, 255, 255))
            else:
                cost_item.setBackground(QColor(183, 28, 28))  # Dark red
                cost_item.setForeground(QColor(255, 255, 255))
                
            self.routing_table.setItem(row, 2, cost_item)
            
            # Metric details (simplified)
            metric_item = QTableWidgetItem("Composite")
            metric_item.setFlags(metric_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.routing_table.setItem(row, 3, metric_item)
            
            # Status
            status = "Valid"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            status_item.setBackground(QColor(46, 125, 50))  # Dark green
            status_item.setForeground(QColor(255, 255, 255))
            self.routing_table.setItem(row, 4, status_item)
            
            # Updated timestamp (placeholder for now)
            updated_item = QTableWidgetItem("Recently")
            updated_item.setFlags(updated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.routing_table.setItem(row, 5, updated_item)
            
            # Interface column (new - column 6)
            interface_item = QTableWidgetItem("eth0")
            interface_item.setFlags(interface_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.routing_table.setItem(row, 6, interface_item)
            
    def router_selected(self, router_id):
        """Handle router selection from combo box"""
        self.current_router = router_id
        self.update_routing_table()
        
        # Select in router table
        for row in range(self.router_table.rowCount()):
            item = self.router_table.item(row, 0)
            if item and item.text() == router_id:
                self.router_table.selectRow(row)
                break
                
    def router_table_selection_changed(self):
        """Handle router table selection change"""
        current_row = self.router_table.currentRow()
        if current_row >= 0:
            item = self.router_table.item(current_row, 0)
            if item:
                router_id = item.text()
                if router_id != self.current_router:
                    self.router_combo.setCurrentText(router_id)
                    
    def export_tables(self):
        """Export routing tables to file"""
        # TODO: Implement export functionality
        print("Export tables functionality not yet implemented")
        
    def refresh_tables(self):
        """Refresh table display"""
        self.update_router_status_table()
        self.update_routing_table()
        
    def clear(self):
        """Clear all routing table data"""
        self.routers_data = {}
        self.current_router = None
        self.router_combo.clear()
        self.router_table.setRowCount(0)
        self.routing_table.setRowCount(0)
        self.router_info_label.setText("No simulation data available")
        
    def filter_changed(self, text):
        """Handle filter text change"""
        self.filter_text = text.lower()
        self.update_routing_table()
        
    def toggle_auto_refresh(self, enabled):
        """Toggle auto-refresh functionality"""
        self.auto_refresh = enabled
        if enabled:
            self.refresh_timer.start(2000)
        else:
            self.refresh_timer.stop()
            
    def auto_refresh_tables(self):
        """Auto-refresh timer callback"""
        if self.auto_refresh:
            self.refresh_tables()
            self.update_network_overview()
            
    def update_network_overview(self):
        """Update network overview tab"""
        if not self.routers_data:
            return
            
        # Update network summary
        total_routers = len(self.routers_data)
        active_routers = sum(1 for router_info in self.routers_data.values() 
                           if router_info.get('neighbors', []))
        connectivity = (active_routers / total_routers * 100) if total_routers > 0 else 0
        
        self.network_size_label.setText(f"Network Size: {total_routers} routers")
        self.connectivity_label.setText(f"Connectivity: {connectivity:.1f}%")
        
        # Update comparison table
        self.comparison_table.setRowCount(len(self.routers_data))
        
        for row, (router_id, router_info) in enumerate(sorted(self.routers_data.items())):
            # Router ID
            router_item = QTableWidgetItem(router_id)
            self.comparison_table.setItem(row, 0, router_item)
            
            # Networks
            networks = router_info.get('networks', [])
            networks_item = QTableWidgetItem(str(len(networks)))
            self.comparison_table.setItem(row, 1, networks_item)
            
            # Neighbors
            neighbors = router_info.get('neighbors', [])
            neighbors_item = QTableWidgetItem(str(len(neighbors)))
            self.comparison_table.setItem(row, 2, neighbors_item)
            
            # Routes
            routing_table = router_info.get('routing_table', router_info.get('fib', {}))
            routes_item = QTableWidgetItem(str(len(routing_table)))
            self.comparison_table.setItem(row, 3, routes_item)
            
            # Average cost
            if routing_table:
                costs = []
                for route_info in routing_table.values():
                    if isinstance(route_info, dict):
                        if 'cost' in route_info:
                            costs.append(route_info.get('cost', 0))
                        elif 'metrics' in route_info:
                            # Handle fib format where cost is in metrics
                            metrics = route_info.get('metrics', {})
                            cost = metrics.get('total_cost', metrics.get('total_delay', metrics.get('cost', 0)))
                            costs.append(cost)
                        elif 'delay' in route_info:
                            costs.append(route_info.get('delay', 0))
                        elif 'weight' in route_info:
                            costs.append(route_info.get('weight', 0))
                        else:
                            costs.append(1)  # Default cost for valid routes
                    else:
                        costs.append(1)  # Default cost for non-dict routes
                
                avg_cost = sum(costs) / len(costs) if costs else 0
            else:
                avg_cost = 0
            
            # Format cost display based on magnitude
            if avg_cost >= 1000:
                cost_display = f"{avg_cost/1000:.1f}k"
            elif avg_cost >= 100:
                cost_display = f"{avg_cost:.0f}"
            else:
                cost_display = f"{avg_cost:.1f}"
                
            avg_cost_item = QTableWidgetItem(cost_display)
            self.comparison_table.setItem(row, 4, avg_cost_item)
            
            # Status
            status = "Active" if neighbors else "Isolated"
            status_item = QTableWidgetItem(status)
            
            # Color code status
            if status == "Active":
                status_item.setBackground(QColor(46, 125, 50))  # Dark green
                status_item.setForeground(QColor(255, 255, 255))
            else:
                status_item.setBackground(QColor(183, 28, 28))  # Dark red
                status_item.setForeground(QColor(255, 255, 255))
                
            self.comparison_table.setItem(row, 5, status_item)
            
        # Update source and destination combos for analysis
        router_ids = sorted(self.routers_data.keys())
        
        # Update source combo
        current_source = self.source_combo.currentText()
        self.source_combo.clear()
        self.source_combo.addItems(router_ids)
        if current_source in router_ids:
            self.source_combo.setCurrentText(current_source)
            
        # Update destination combo
        current_dest = self.dest_combo.currentText()
        self.dest_combo.clear()
        self.dest_combo.addItems(router_ids)
        if current_dest in router_ids:
            self.dest_combo.setCurrentText(current_dest)
            
    def analyze_path(self):
        """Analyze path between source and destination"""
        source = self.source_combo.currentText()
        destination = self.dest_combo.currentText()
        
        if not source or not destination or source == destination:
            self.path_info_label.setText("Please select different source and destination routers")
            self.path_table.setRowCount(0)
            return
            
        # Simple path analysis - find route in source router's routing table
        if source not in self.routers_data:
            self.path_info_label.setText(f"Source router {source} not found")
            self.path_table.setRowCount(0)
            return
            
        # Check for both 'routing_table' and 'fib' fields (simulation uses 'fib')
        source_routing_table = self.routers_data[source].get('routing_table', self.routers_data[source].get('fib', {}))
        
        if destination not in source_routing_table:
            self.path_info_label.setText(f"No route from {source} to {destination}")
            self.path_table.setRowCount(0)
            return
            
        route_info = source_routing_table[destination]
        next_hop = route_info.get('next_hop', 'Direct')
        cost = route_info.get('cost', 0)
        
        self.path_info_label.setText(f"Path Analysis: {source} -> {destination} (Cost: {cost:.2f})")
        
        # Simple path display (could be enhanced with full path tracing)
        if next_hop == 'Direct':
            self.path_table.setRowCount(1)
            self.path_table.setItem(0, 0, QTableWidgetItem("1"))
            self.path_table.setItem(0, 1, QTableWidgetItem(f"{source} → {destination}"))
            self.path_table.setItem(0, 2, QTableWidgetItem(f"{cost:.2f}"))
            self.path_table.setItem(0, 3, QTableWidgetItem(f"{cost:.2f}"))
        else:
            self.path_table.setRowCount(2)
            self.path_table.setItem(0, 0, QTableWidgetItem("1"))
            self.path_table.setItem(0, 1, QTableWidgetItem(f"{source} → {next_hop}"))
            self.path_table.setItem(0, 2, QTableWidgetItem("..."))
            self.path_table.setItem(0, 3, QTableWidgetItem("..."))
            
            self.path_table.setItem(1, 0, QTableWidgetItem("..."))
            self.path_table.setItem(1, 1, QTableWidgetItem(f"... → {destination}"))
            self.path_table.setItem(1, 2, QTableWidgetItem("..."))
            self.path_table.setItem(1, 3, QTableWidgetItem(f"{cost:.2f}"))
            
    def sort_by_cost(self):
        """Sort routing table by cost"""
        if self.routing_table.rowCount() > 0:
            self.routing_table.sortItems(2, Qt.SortOrder.AscendingOrder)  # Sort by cost column (index 2)
        
    def show_direct_routes_only(self):
        """Show only direct routes"""
        self.route_filter = "direct"
        self.update_routing_table()
        
    def show_all_routes(self):
        """Show all routes"""
        self.route_filter = None
        self.update_routing_table()
        
    def auto_refresh_tables(self):
        """Auto-refresh timer callback"""
        if self.auto_refresh:
            self.refresh_tables()
            self.update_network_overview()
