"""
Packet Log Widget for ADUP
Display and filter packet logs
"""

import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QHeaderView, QLabel, QComboBox,
                            QLineEdit, QPushButton, QCheckBox, QGroupBox,
                            QFrame, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from collections import deque
import time


class PacketLogWidget(QWidget):
    """Widget for displaying packet logs with filtering"""
    
    def __init__(self):
        super().__init__()
        self.packet_log = deque(maxlen=500)  # Keep last 500 packets (reduced from 1000)
        self.filtered_packets = []
        self.auto_scroll = True
        self.last_packet_count = 0  # Track when we need to update
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Filter panel
        filter_panel = self.create_filter_panel()
        layout.addWidget(filter_panel)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Packet table
        table_panel = self.create_table_panel()
        splitter.addWidget(table_panel)
        
        # Packet details
        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
        
    def create_filter_panel(self):
        """Create filter panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        layout = QHBoxLayout(panel)
        
        # Packet type filter
        layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Hello", "Update", "Data"])
        self.type_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.type_combo)
        
        # Source filter
        layout.addWidget(QLabel("Source:"))
        self.source_combo = QComboBox()
        self.source_combo.addItem("All")
        self.source_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.source_combo)
        
        # Destination filter
        layout.addWidget(QLabel("Destination:"))
        self.dest_combo = QComboBox()
        self.dest_combo.addItem("All")
        self.dest_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.dest_combo)
        
        # Search filter
        layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in packet data...")
        self.search_edit.textChanged.connect(self.apply_filters)
        layout.addWidget(self.search_edit)
        
        layout.addStretch()
        
        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto Scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.toggled.connect(self.toggle_auto_scroll)
        layout.addWidget(self.auto_scroll_cb)
        
        # Clear button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_btn)
        
        # Export button
        export_btn = QPushButton("Export Log")
        export_btn.clicked.connect(self.export_log)
        layout.addWidget(export_btn)
        
        return panel
        
    def create_table_panel(self):
        """Create packet table panel"""
        group = QGroupBox("Packet Log")
        layout = QVBoxLayout(group)
        
        # Packet table
        self.packet_table = QTableWidget()
        self.packet_table.setColumnCount(7)
        self.packet_table.setHorizontalHeaderLabels([
            "Time", "Type", "Source", "Destination", "Size", "Status", "Details"
        ])
        
        # Configure table
        header = self.packet_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        self.packet_table.setAlternatingRowColors(True)
        self.packet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.packet_table.itemSelectionChanged.connect(self.packet_selection_changed)
        
        # Set table styling for better appearance with dark theme
        self.packet_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #444444;
                background-color: #2b2b2b;
                alternate-background-color: #353535;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 6px;
                border: 1px solid #555555;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.packet_table)
        
        return group
        
    def create_details_panel(self):
        """Create packet details panel"""
        group = QGroupBox("Packet Details")
        layout = QVBoxLayout(group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Courier", 9))
        
        # Style the details text area for dark theme
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.details_text)
        
        return group
        
    def update_state(self, state):
        """Update packet log with new simulation state"""
        # Get real packet logs from the simulation state
        packet_logs = state.get('packet_logs', [])
        current_time = state.get('time', 0)
        routers = state.get('routers', {})
        
        # Track how many new packets we're adding
        new_packets_added = 0
        
        # Track existing packet log entries by a unique identifier
        existing_packet_ids = set()
        for existing_packet in self.packet_log:
            # Create unique ID from multiple attributes
            packet_id = (
                existing_packet.get('time', 0),
                existing_packet.get('source', ''),
                existing_packet.get('type', ''),
                existing_packet.get('status', ''),
                existing_packet.get('destination', '')
            )
            existing_packet_ids.add(packet_id)
        
        # Add new packet logs that we haven't seen before
        for packet_log_entry in packet_logs:            
            # Convert router packet log format to our widget format
            packet_time = packet_log_entry.get('time', 0)
            router_name = packet_log_entry.get('router', 'Unknown')
            packet_type = packet_log_entry.get('type', 'Unknown')
            direction = packet_log_entry.get('direction', 'Unknown').title()
            neighbor = packet_log_entry.get('neighbor', 'Broadcast')
            
            # Create unique identifier for this packet log entry
            packet_id = (packet_time, router_name, packet_type, direction, neighbor)
            
            if packet_id not in existing_packet_ids:
                # Convert to our packet format
                packet = {
                    'time': packet_time,
                    'type': packet_type,
                    'source': router_name,
                    'destination': neighbor,
                    'size': 64,  # Default size for protocol packets
                    'status': direction,
                    'details': packet_log_entry.get('details', ''),
                    'data': {
                        'router': router_name,
                        'neighbor': neighbor,
                        'direction': packet_log_entry.get('direction', '')
                    }
                }
                self.packet_log.append(packet)
                existing_packet_ids.add(packet_id)
                new_packets_added += 1
        
        # Only update the table if we added new packets
        if new_packets_added > 0:
            self.apply_filters()
                    
        # Update router lists in filters
        self.update_filter_options(routers)
        
    def create_simulated_packet(self, time, router_ids):
        """Create a simulated packet for demonstration"""
        import random
        
        packet_types = ["Hello", "Update", "Data"]
        packet_type = random.choice(packet_types)
        source = random.choice(router_ids)
        dest = random.choice([r for r in router_ids if r != source])
        
        packet = {
            'time': time,
            'type': packet_type,
            'source': source,
            'destination': dest,
            'size': random.randint(64, 1500),
            'status': random.choice(["Sent", "Received", "Dropped"]),
            'details': f"{packet_type} packet from {source} to {dest}",
            'data': {
                'sequence': random.randint(1, 1000),
                'ttl': random.randint(30, 64),
                'checksum': hex(random.randint(0, 65535))
            }
        }
        
        return packet
        
    def add_packet(self, packet):
        """Add a packet to the log"""
        self.packet_log.append(packet)
        # Only update filters if we have new packets
        if len(self.packet_log) != self.last_packet_count:
            self.apply_filters()
            self.last_packet_count = len(self.packet_log)
        
    def update_filter_options(self, routers):
        """Update filter combo box options"""
        router_ids = sorted(routers.keys())
        
        # Update source combo
        current_source = self.source_combo.currentText()
        self.source_combo.clear()
        self.source_combo.addItem("All")
        self.source_combo.addItems(router_ids)
        if current_source in router_ids or current_source == "All":
            self.source_combo.setCurrentText(current_source)
            
        # Update destination combo
        current_dest = self.dest_combo.currentText()
        self.dest_combo.clear()
        self.dest_combo.addItem("All")
        self.dest_combo.addItems(router_ids)
        if current_dest in router_ids or current_dest == "All":
            self.dest_combo.setCurrentText(current_dest)
            
    def apply_filters(self):
        """Apply current filters to packet log"""
        type_filter = self.type_combo.currentText()
        source_filter = self.source_combo.currentText()
        dest_filter = self.dest_combo.currentText()
        search_text = self.search_edit.text().lower()
        
        self.filtered_packets = []
        
        for packet in self.packet_log:
            # Type filter
            if type_filter != "All" and packet['type'] != type_filter:
                continue
                
            # Source filter
            if source_filter != "All" and packet['source'] != source_filter:
                continue
                
            # Destination filter
            if dest_filter != "All" and packet['destination'] != dest_filter:
                continue
                
            # Search filter
            if search_text:
                searchable_text = (
                    packet['type'] + " " +
                    packet['source'] + " " +
                    packet['destination'] + " " +
                    packet['details']
                ).lower()
                if search_text not in searchable_text:
                    continue
                    
            self.filtered_packets.append(packet)
            
        self.update_table()
        
    def update_table(self):
        """Update the packet table with filtered packets"""
        self.packet_table.setRowCount(len(self.filtered_packets))
        
        for row, packet in enumerate(self.filtered_packets):
            # Time
            time_item = QTableWidgetItem(f"{packet['time']:.3f}")
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            time_item.setForeground(QColor(255, 255, 255))  # White text for dark theme
            self.packet_table.setItem(row, 0, time_item)
            
            # Type
            type_item = QTableWidgetItem(packet['type'])
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color code by type with better contrast for dark theme
            if packet['type'] == "Hello":
                type_item.setBackground(QColor(34, 139, 34))  # Forest Green
                type_item.setForeground(QColor(255, 255, 255))  # White text
            elif packet['type'] == "Update":
                type_item.setBackground(QColor(30, 144, 255))  # Dodger Blue
                type_item.setForeground(QColor(255, 255, 255))  # White text
            else:
                type_item.setBackground(QColor(255, 140, 0))  # Dark Orange
                type_item.setForeground(QColor(0, 0, 0))  # Black text
                
            self.packet_table.setItem(row, 1, type_item)
            
            # Source
            source_item = QTableWidgetItem(packet['source'])
            source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            source_item.setForeground(QColor(255, 255, 255))  # White text for dark theme
            self.packet_table.setItem(row, 2, source_item)
            
            # Destination
            dest_item = QTableWidgetItem(packet['destination'])
            dest_item.setFlags(dest_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            dest_item.setForeground(QColor(255, 255, 255))  # White text for dark theme
            self.packet_table.setItem(row, 3, dest_item)
            
            # Size
            size_item = QTableWidgetItem(f"{packet['size']} B")
            size_item.setFlags(size_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            size_item.setForeground(QColor(255, 255, 255))  # White text for dark theme
            self.packet_table.setItem(row, 4, size_item)
            
            # Status
            status_item = QTableWidgetItem(packet['status'])
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color code by status with better contrast for dark theme
            if packet['status'] == "Sent":
                status_item.setBackground(QColor(46, 125, 50))  # Dark Green
                status_item.setForeground(QColor(255, 255, 255))  # White text
            elif packet['status'] == "Received":
                status_item.setBackground(QColor(25, 118, 210))  # Dark Blue
                status_item.setForeground(QColor(255, 255, 255))  # White text
            else:  # Dropped
                status_item.setBackground(QColor(198, 40, 40))  # Dark Red
                status_item.setForeground(QColor(255, 255, 255))  # White text
                
            self.packet_table.setItem(row, 5, status_item)
            
            # Details
            # Convert dict to formatted string for display
            if isinstance(packet['details'], dict):
                try:
                    details_text = json.dumps(packet['details'], indent=2, separators=(',', ': '))
                except (TypeError, ValueError):
                    details_text = str(packet['details'])
            else:
                details_text = str(packet['details'])
            details_item = QTableWidgetItem(details_text)
            details_item.setFlags(details_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            details_item.setForeground(QColor(255, 255, 255))  # White text for dark theme
            self.packet_table.setItem(row, 6, details_item)
            
        # Auto-scroll to bottom if enabled
        if self.auto_scroll and self.filtered_packets:
            self.packet_table.scrollToBottom()
            
    def packet_selection_changed(self):
        """Handle packet selection change"""
        current_row = self.packet_table.currentRow()
        if 0 <= current_row < len(self.filtered_packets):
            packet = self.filtered_packets[current_row]
            self.show_packet_details(packet)
        else:
            self.details_text.clear()
            
    def show_packet_details(self, packet):
        """Show detailed packet information"""
        details = f"""Packet Details:
        
Time: {packet['time']:.6f} seconds
Type: {packet['type']}
Source: {packet['source']}
Destination: {packet['destination']}
Size: {packet['size']} bytes
Status: {packet['status']}

Description: {packet['details']}

Additional Data:"""
        
        if 'data' in packet:
            for key, value in packet['data'].items():
                details += f"\n  {key}: {value}"
                
        self.details_text.setPlainText(details)
        
    def toggle_auto_scroll(self, enabled):
        """Toggle auto-scroll functionality"""
        self.auto_scroll = enabled
        
    def clear_log(self):
        """Clear the packet log"""
        self.packet_log.clear()
        self.filtered_packets.clear()
        self.packet_table.setRowCount(0)
        self.details_text.clear()
        
    def export_log(self):
        """Export packet log to file"""
        # TODO: Implement export functionality
        print("Export log functionality not yet implemented")
        
    def clear(self):
        """Clear all packet data"""
        self.clear_log()
