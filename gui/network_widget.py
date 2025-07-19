"""
Network Visualization Widget for ADUP with Advanced Packet Analysis
"""

import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QCheckBox, QSlider, QFrame,
                            QTabWidget, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
import math
import random
from gui.advanced_packet_viz import PacketTraceWidget


class NetworkVisualizationWidget(QWidget):
    """Enhanced widget for network visualization with advanced packet analysis"""
    
    def __init__(self):
        super().__init__()
        self.routers = {}
        self.links = []
        self.packets = []
        self.router_positions = {}
        self.last_state_hash = None
        
        self.init_ui()
        self.setup_animation_timer()
        
    def init_ui(self):
        """Initialize the user interface with advanced features"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Create splitter for main view and advanced analysis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - traditional network view
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Control panel - compact
        control_panel = self.create_control_panel()
        left_layout.addWidget(control_panel)
        
        # Visualization area
        self.viz_area = NetworkCanvas()
        left_layout.addWidget(self.viz_area)
        
        splitter.addWidget(left_widget)
        
        # Right side - advanced packet analysis
        self.advanced_analysis = PacketTraceWidget()
        splitter.addWidget(self.advanced_analysis)
        
        # Set splitter proportions (70% traditional, 30% advanced)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
        
        # Connect signals
        self.viz_area.router_clicked.connect(self.on_router_clicked)
        
    def create_control_panel(self):
        """Create compact control panel for visualization options"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px;
                color: #ffffff;
            }
        """)
        panel.setMaximumHeight(40)  # Limit the height
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 4, 8, 4)  # Reduce margins
        layout.setSpacing(10)  # Reduce spacing between elements
        
        # View controls - more compact
        view_label = QLabel("View:")
        view_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        layout.addWidget(view_label)
        
        self.show_labels_cb = QCheckBox("Labels")
        self.show_labels_cb.setChecked(True)
        self.show_labels_cb.toggled.connect(self.update_view_options)
        self.show_labels_cb.setStyleSheet("font-size: 11px; color: #ffffff;")
        layout.addWidget(self.show_labels_cb)
        
        self.show_metrics_cb = QCheckBox("Metrics")
        self.show_metrics_cb.toggled.connect(self.update_view_options)
        self.show_metrics_cb.setStyleSheet("font-size: 11px; color: #ffffff;")
        layout.addWidget(self.show_metrics_cb)
        
        self.show_tooltips_cb = QCheckBox("Hover Info")
        self.show_tooltips_cb.setChecked(True)  # Enable by default
        self.show_tooltips_cb.toggled.connect(self.update_view_options)
        self.show_tooltips_cb.setStyleSheet("font-size: 11px; color: #ffffff;")
        layout.addWidget(self.show_tooltips_cb)
        
        self.show_packets_cb = QCheckBox("Packets")
        self.show_packets_cb.setChecked(True)
        self.show_packets_cb.toggled.connect(self.update_view_options)
        self.show_packets_cb.setStyleSheet("font-size: 11px; color: #ffffff;")
        layout.addWidget(self.show_packets_cb)
        
        separator = QLabel("|")
        separator.setStyleSheet("color: #888888;")
        layout.addWidget(separator)  # Visual separator
        
        layout_label = QLabel("Layout:")
        layout_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        layout.addWidget(layout_label)
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(['Auto', 'Circle', 'Grid', 'Force'])
        self.layout_combo.currentTextChanged.connect(self.layout_changed)
        self.layout_combo.setStyleSheet("""
            QComboBox {
                font-size: 11px;
                padding: 2px 6px;
                max-height: 24px;
                background-color: #404040;
                border: 1px solid #666666;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.layout_combo)
        
        layout.addStretch()
        
        # Zoom controls - more compact
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        self.zoom_slider.setMaximumWidth(80)  # Make slider more compact
        self.zoom_slider.setMaximumHeight(20)
        layout.addWidget(self.zoom_slider)
        
        return panel
        
    def setup_animation_timer(self):
        """Setup timer for packet animations"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_packets)
        self.animation_timer.start(200)  # 5 FPS for packet animation (reduced from 20 FPS)
        
    def update_state(self, state):
        """Update visualization with new simulation state and advanced analysis"""
        # Simple optimization: check if the router/link structure has changed
        new_routers = state.get('routers', {})
        new_links = state.get('links', [])
        
        # Create a simple hash of the structure
        import hashlib
        state_str = f"{sorted(new_routers.keys())}_{len(new_links)}"
        state_hash = hashlib.md5(state_str.encode()).hexdigest()
        
        # Only update if structure changed or this is the first update
        structure_changed = state_hash != self.last_state_hash
        self.last_state_hash = state_hash
        
        self.routers = new_routers
        self.links = new_links
        
        # Convert packet logs to animated packets for visualization
        self.packets = self._convert_packet_logs_to_packets(state.get('packet_logs', []))
        
        # Only update positions if structure changed
        if structure_changed and self.routers:
            self.update_router_positions()
            # Share positions with router data for advanced visualization
            for router_id, position in self.router_positions.items():
                if router_id in self.routers:
                    self.routers[router_id]['position'] = position
            
        # Update main canvas
        self.viz_area.update_network(self.routers, self.links, self.packets, self.router_positions)
        
        # Create synchronized state for advanced analysis
        synchronized_state = state.copy()
        synchronized_state['routers'] = self.routers.copy()  # Include positions
        synchronized_state['router_positions'] = self.router_positions.copy()
        
        # Update advanced analysis with synchronized positions
        self.advanced_analysis.update_state(synchronized_state)
        
        # Only force repaint if structure changed (packets will animate via timer)
        if structure_changed:
            self.viz_area.update()
            
    def _convert_packet_logs_to_packets(self, packet_logs):
        """Convert packet logs to animated packet objects. Robustly visualize all HELLO packets."""
        animated_packets = []
        current_time = time.time()

        # Only create animated packets for recent 'sent' packets (last 5 seconds)
        recent_sent_packets = [
            log for log in packet_logs
            if log.get('direction') == 'sent' and (current_time - log.get('time', 0)) < 5.0
        ]

        # Debug: Print all links
        print("[DEBUG] Current links:")
        for link in self.links:
            print(f"  Link: {link}")

        # Debug: Print all recent HELLO sent events
        print("[DEBUG] Recent HELLO 'sent' events:")
        for log in recent_sent_packets:
            if log.get('type') == 'HELLO':
                print(f"  HELLO from {log.get('router')} to {log.get('neighbor')} at {log.get('time', 0)}")

        seen_transmissions = set()
        for log in recent_sent_packets:
            source = log.get('router')
            destination = log.get('neighbor')
            packet_type = log.get('type', 'UNKNOWN')
            packet_time = log.get('time', 0)
            transmission_id = f"{source}_{destination}_{packet_type}_{packet_time}"

            # For HELLO packets, always animate every event (no duplicate suppression)
            if packet_type == 'HELLO' and source and destination:
                # Debug: Check if link exists for this pair
                link_exists = any(
                    (link.get('router1') == source and link.get('router2') == destination) or
                    (link.get('router1') == destination and link.get('router2') == source)
                    for link in self.links
                )
                if not link_exists:
                    print(f"[DEBUG] No link found between {source} and {destination} for HELLO packet!")
                
                # Always create HELLO packet animation regardless of current progress
                # The animate_packets method will handle progress updates and removal
                time_elapsed = current_time - packet_time
                progress = min(time_elapsed / 2.0, 1.0)
                packet = {
                    'id': transmission_id,
                    'source': source,
                    'destination': destination,
                    'type': packet_type,
                    'progress': progress,
                    'time_created': packet_time,
                    'details': log.get('details', {}),
                    'color': self._get_packet_color(packet_type)
                }
                animated_packets.append(packet)
                print(f"[DEBUG] Added HELLO packet {source}->{destination} with progress {progress:.2f}")
            # For other packet types, avoid duplicates
            elif source and destination and transmission_id not in seen_transmissions:
                seen_transmissions.add(transmission_id)
                time_elapsed = current_time - packet_time
                progress = min(time_elapsed / 2.0, 1.0)
                # Create packet animation regardless of current progress
                # The animate_packets method will handle progress updates and removal
                packet = {
                    'id': transmission_id,
                    'source': source,
                    'destination': destination,
                    'type': packet_type,
                    'progress': progress,
                    'time_created': packet_time,
                    'details': log.get('details', {}),
                    'color': self._get_packet_color(packet_type)
                }
                animated_packets.append(packet)
        return animated_packets
        
    def _get_packet_color(self, packet_type):
        """Get color for packet type"""
        colors = {
            'HELLO': '#e74c3c',  # Red for hello packets
            'UPDATE': '#3498db', # Blue for update packets
            'DATA': '#2ecc71',   # Green for data packets
            'QUERY': '#f39c12',  # Orange for query packets
            'REPLY': '#9b59b6'   # Purple for reply packets
        }
        return colors.get(packet_type, '#95a5a6')  # Default gray
        
    def update_router_positions(self):
        """Calculate router positions based on topology"""
        if not self.routers:
            return
            
        num_routers = len(self.routers)
        router_ids = list(self.routers.keys())
        
        # Only regenerate positions for routers that don't have them
        new_routers = [rid for rid in router_ids if rid not in self.router_positions]
        
        if new_routers or len(self.router_positions) == 0:
            print(f"Generating positions for routers: {router_ids}")
            
            # Clear all positions if we need to regenerate layout
            if len(self.router_positions) == 0:
                self.router_positions.clear()
                
                # Generate positions based on layout type
                layout_type = self.layout_combo.currentText()
                print(f"Using layout type: {layout_type}")
                
                if layout_type == 'Circle':
                    self.generate_circle_layout(router_ids)
                elif layout_type == 'Grid':
                    self.generate_grid_layout(router_ids)
                elif layout_type == 'Force':
                    self.generate_force_layout(router_ids)
                else:  # Auto
                    self.generate_auto_layout(router_ids)
            else:
                # Just add positions for new routers using current layout
                layout_type = self.layout_combo.currentText()
                if layout_type == 'Circle':
                    self.add_router_positions_circle(new_routers)
                else:
                    self.add_router_positions(new_routers)
                
            print(f"Current positions: {self.router_positions}")
            
    def add_router_positions_circle(self, new_router_ids):
        """Add positions for new routers in circular pattern"""
        existing_count = len(self.router_positions)
        total_count = existing_count + len(new_router_ids)
        
        for i, router_id in enumerate(new_router_ids):
            # Place new routers in the circle pattern
            angle = 2 * math.pi * (existing_count + i) / total_count
            x = 150 * math.cos(angle)
            y = 150 * math.sin(angle)
            self.router_positions[router_id] = (x, y)
            
    def add_router_positions(self, new_router_ids):
        """Add positions for new routers without disrupting existing ones"""
        for i, router_id in enumerate(new_router_ids):
            # Place new routers in a simple pattern around origin
            angle = 2 * math.pi * len(self.router_positions) / (len(self.router_positions) + len(new_router_ids))
            x = 150 * math.cos(angle)
            y = 150 * math.sin(angle)
            self.router_positions[router_id] = (x, y)
            
    def generate_circle_layout(self, router_ids):
        """Generate circular layout"""
        num_routers = len(router_ids)
        # Use normalized coordinates that will be centered later
        center_x, center_y = 0, 0
        radius = 150
        
        for i, router_id in enumerate(router_ids):
            angle = 2 * math.pi * i / num_routers
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.router_positions[router_id] = (x, y)
            
    def generate_grid_layout(self, router_ids):
        """Generate grid layout"""
        num_routers = len(router_ids)
        cols = int(math.ceil(math.sqrt(num_routers)))
        rows = int(math.ceil(num_routers / cols))
        
        spacing_x, spacing_y = 150, 120
        # Center the grid around origin
        start_x = -(cols - 1) * spacing_x / 2
        start_y = -(rows - 1) * spacing_y / 2
        
        for i, router_id in enumerate(router_ids):
            row = i // cols
            col = i % cols
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            self.router_positions[router_id] = (x, y)
            
    def generate_force_layout(self, router_ids):
        """Generate force-directed layout"""
        # Simple spring layout centered around origin
        if not hasattr(self, '_force_positions'):
            self._force_positions = {}
            for router_id in router_ids:
                self._force_positions[router_id] = (
                    random.uniform(-200, 200), 
                    random.uniform(-150, 150)
                )
        
        # Update positions based on forces (simplified)
        self.router_positions = self._force_positions.copy()
        
    def generate_auto_layout(self, router_ids):
        """Generate automatic layout based on topology"""
        # For now, use circle layout
        self.generate_circle_layout(router_ids)
        
    def update_view_options(self):
        """Update view options"""
        self.viz_area.show_labels = self.show_labels_cb.isChecked()
        self.viz_area.show_metrics = self.show_metrics_cb.isChecked()
        self.viz_area.show_packets = self.show_packets_cb.isChecked()
        self.viz_area.show_tooltips = self.show_tooltips_cb.isChecked()
        self.viz_area.update()
        
    def layout_changed(self, layout):
        """Handle layout change"""
        print(f"DEBUG: Layout changed to: {layout}")
        # Clear existing positions to force regeneration
        self.router_positions.clear()
        # Clear any cached force positions
        if hasattr(self, '_force_positions'):
            delattr(self, '_force_positions')
        # Regenerate positions with new layout
        if self.routers:
            print(f"DEBUG: Regenerating positions for {len(self.routers)} routers")
            self.update_router_positions()
            self.viz_area.update_network(self.routers, self.links, self.packets, self.router_positions)
        self.viz_area.update()
        
    def zoom_changed(self, value):
        """Handle zoom change"""
        scale = value / 100.0
        self.viz_area.set_scale(scale)
        
    def animate_packets(self):
        """Animate packet movements with realistic timing"""
        current_time = time.time()
        packets_to_remove = []
        
        # Update packet positions based on real time elapsed
        for i, packet in enumerate(self.packets):
            time_created = packet.get('time_created', current_time)
            time_elapsed = current_time - time_created
            
            # 2-second animation duration for packets
            new_progress = min(time_elapsed / 2.0, 1.0)
            packet['progress'] = new_progress
            
            # Mark completed packets for removal
            if new_progress >= 1.0:
                packets_to_remove.append(i)
        
        # Remove completed packets
        for i in reversed(packets_to_remove):
            del self.packets[i]
                
        self.viz_area.update()
        
    def on_router_clicked(self, router_id):
        """Handle router click"""
        print(f"Router {router_id} clicked")
        # Could show router details dialog
        
    def clear(self):
        """Clear the visualization"""
        self.routers = {}
        self.links = []
        self.packets = []
        self.router_positions = {}
        self.viz_area.clear()


class NetworkCanvas(QWidget):
    """Canvas widget for drawing the network"""
    
    router_clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.routers = {}
        self.links = []
        self.packets = []
        self.positions = {}
        self.scale = 1.0
        self.show_labels = True
        self.show_metrics = False
        self.show_packets = True
        self.show_tooltips = True  # Enable tooltips by default
        
        # Add hover functionality
        self.setMouseTracking(True)
        self.hovered_router = None
        self.hovered_link = None
        self.tooltip_pos = None
        
        self.setMinimumSize(600, 400)
        
    def update_network(self, routers, links, packets, positions):
        """Update network data"""
        self.routers = routers
        self.links = links
        self.packets = packets
        self.positions = positions
        self.update()
        
    def set_scale(self, scale):
        """Set display scale"""
        self.scale = scale
        self.update()
        
    def clear(self):
        """Clear the canvas"""
        self.routers = {}
        self.links = []
        self.packets = []
        self.positions = {}
        self.update()
        
    def paintEvent(self, event):
        """Paint the network visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background with dark theme color
        painter.fillRect(self.rect(), QColor(43, 43, 43))  # Dark background #2b2b2b
        
        # If no routers, show helpful message
        if not self.routers:
            painter.setPen(QPen(QColor(200, 200, 200), 1))  # Light gray text for dark theme
            font = QFont("Arial", 14)
            painter.setFont(font)
            
            # Center the text
            rect = self.rect()
            text = "No network topology loaded. Start a simulation to see routers."
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            return
        
        # Calculate the bounding box of all router positions
        if self.positions:
            x_coords = [pos[0] for pos in self.positions.values()]
            y_coords = [pos[1] for pos in self.positions.values()]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            # Calculate the center of the network
            network_center_x = (min_x + max_x) / 2
            network_center_y = (min_y + max_y) / 2
            
            # Calculate the center of the canvas
            canvas_center_x = self.width() / 2
            canvas_center_y = self.height() / 2
            
            # Calculate translation to center the network
            translate_x = canvas_center_x / self.scale - network_center_x
            translate_y = canvas_center_y / self.scale - network_center_y
            
            # Apply scaling and centering transformation
            painter.scale(self.scale, self.scale)
            painter.translate(translate_x, translate_y)
        else:
            # Apply only scaling if no positions
            painter.scale(self.scale, self.scale)
        
        # Draw links first (so they appear behind routers)
        self.draw_links(painter)
        
        # Draw routers
        self.draw_routers(painter)
        
        # Draw packets
        if self.show_packets:
            self.draw_packets(painter)
            
        # Reset transformation for tooltip drawing in screen coordinates
        painter.resetTransform()
        
        # Draw tooltips for hovered elements
        self.draw_tooltips(painter)
    
    def draw_tooltips(self, painter):
        """Draw tooltips for hovered routers and links"""
        if not self.show_tooltips:
            return
            
        if self.hovered_router and self.tooltip_pos:
            router_info = self.routers[self.hovered_router]
            
            # Prepare enhanced router tooltip with metrics and path costs
            tooltip_lines = [f"Router: {self.hovered_router}"]
            
            # Add router state and basic info
            state = router_info.get('state', 'Unknown')
            tooltip_lines.append(f"State: {state}")
            
            # Add routing table info (path costs)
            routing_table = router_info.get('routing_table', {})
            if routing_table:
                tooltip_lines.append("── Path Costs ──")
                for dest, info in list(routing_table.items())[:4]:  # Limit to 4 entries
                    cost = info.get('cost', 0)
                    next_hop = info.get('next_hop', 'Direct')
                    selection_reason = info.get('metrics', {}).get('selection_reason', 'Best path')
                    tooltip_lines.append(f"→ {dest}: {cost:.2f} via {next_hop}")
                    if selection_reason != 'Best path':
                        tooltip_lines.append(f"    ({selection_reason})")
            
            # Add neighbor metrics
            neighbor_metrics = router_info.get('neighbor_metrics', {})
            if neighbor_metrics:
                tooltip_lines.append("── Neighbors ──")
                for neighbor, metrics in list(neighbor_metrics.items())[:3]:
                    if isinstance(metrics, dict):
                        delay = metrics.get('delay', 0)
                        jitter = metrics.get('jitter', 0)
                        packet_loss = metrics.get('packet_loss', 0)
                        tooltip_lines.append(f"  {neighbor}:")
                        tooltip_lines.append(f"    delay={delay:.1f}ms, loss={packet_loss:.2f}%")
            
            self.draw_tooltip_box(painter, self.tooltip_pos, tooltip_lines)
            
        elif self.hovered_link and self.tooltip_pos:
            link = self.hovered_link
            
            # Prepare enhanced link tooltip
            router1 = link.get('router1', 'Unknown')
            router2 = link.get('router2', 'Unknown')
            delay = link.get('delay', 0)
            packet_loss = link.get('packet_loss', 0)
            congestion = link.get('congestion', 0)
            jitter = link.get('jitter', 0)
            bandwidth = link.get('bandwidth', 100)
            
            # Calculate composite path cost (using same weights as router)
            composite_cost = (
                delay * 0.4 +                    # 40% delay weight
                jitter * 0.2 +                   # 20% jitter weight
                packet_loss * 1000 * 0.25 +      # 25% packet loss weight (scaled)
                congestion * 100 * 0.15          # 15% congestion weight (scaled)
            )
            
            tooltip_lines = [
                f"Link: {router1} ↔ {router2}",
                f"Composite Cost: {composite_cost:.2f}",
                "── Link Metrics ──",
                f"Delay: {delay:.2f}ms",
                f"Jitter: {jitter:.2f}ms", 
                f"Packet Loss: {packet_loss:.3f}%",
                f"Congestion: {congestion:.1f}%",
                f"Bandwidth: {bandwidth} Mbps"
            ]
            
            self.draw_tooltip_box(painter, self.tooltip_pos, tooltip_lines)
    
    def draw_tooltip_box(self, painter, pos, lines):
        """Draw a tooltip box with given lines at position"""
        if not lines:
            return
            
        # Calculate tooltip size
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        max_width = 0
        line_height = 16
        padding = 8
        
        # Calculate required width
        for line in lines:
            metrics = painter.fontMetrics()
            width = metrics.horizontalAdvance(line)
            max_width = max(max_width, width)
        
        tooltip_width = max_width + 2 * padding
        tooltip_height = len(lines) * line_height + 2 * padding
        
        # Position tooltip
        x, y = pos
        x += 15  # Offset from cursor
        y -= tooltip_height // 2
        
        # Keep tooltip on screen
        if x + tooltip_width > self.width():
            x = self.width() - tooltip_width - 5
        if y < 0:
            y = 5
        if y + tooltip_height > self.height():
            y = self.height() - tooltip_height - 5
        
        # Draw tooltip background
        painter.setBrush(QBrush(QColor(40, 40, 40, 240)))  # Semi-transparent dark
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRoundedRect(x, y, tooltip_width, tooltip_height, 5, 5)
        
        # Draw text
        painter.setPen(QPen(QColor(255, 255, 255)))
        for i, line in enumerate(lines):
            text_y = y + padding + (i + 1) * line_height - 3
            painter.drawText(x + padding, text_y, line)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if not self.positions:
            return
            
        # Get click position in widget coordinates
        click_x = event.position().x()
        click_y = event.position().y()
        
        # Calculate the same transformation used in paintEvent
        x_coords = [pos[0] for pos in self.positions.values()]
        y_coords = [pos[1] for pos in self.positions.values()]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        network_center_x = (min_x + max_x) / 2
        network_center_y = (min_y + max_y) / 2
        
        canvas_center_x = self.width() / 2
        canvas_center_y = self.height() / 2
        
        translate_x = canvas_center_x / self.scale - network_center_x
        translate_y = canvas_center_y / self.scale - network_center_y
        
        # Transform click coordinates back to network space
        x = (click_x / self.scale) - translate_x
        y = (click_y / self.scale) - translate_y
        
        # Check if click is on a router
        for router_id, (rx, ry) in self.positions.items():
            distance = math.sqrt((x - rx)**2 + (y - ry)**2)
            if distance <= 25:  # Router radius
                self.router_clicked.emit(router_id)
                break
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for hover functionality"""
        if not self.positions:
            return
            
        # Get mouse position
        mouse_x = event.position().x()
        mouse_y = event.position().y()
        
        # Calculate transformation (same as in paintEvent)
        x_coords = [pos[0] for pos in self.positions.values()]
        y_coords = [pos[1] for pos in self.positions.values()]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        network_center_x = (min_x + max_x) / 2
        network_center_y = (min_y + max_y) / 2
        
        canvas_center_x = self.width() / 2
        canvas_center_y = self.height() / 2
        
        translate_x = canvas_center_x / self.scale - network_center_x
        translate_y = canvas_center_y / self.scale - network_center_y
        
        # Transform mouse coordinates to network space
        x = (mouse_x / self.scale) - translate_x
        y = (mouse_y / self.scale) - translate_y
        
        # Check for router hover
        old_hovered_router = self.hovered_router
        old_hovered_link = self.hovered_link
        self.hovered_router = None
        self.hovered_link = None
        self.tooltip_pos = None
        
        # Check routers
        for router_id, router_info in self.routers.items():
            if router_id in self.positions:
                rx, ry = self.positions[router_id]
                radius = 15  # Same as in draw_routers
                distance = math.sqrt((x - rx) ** 2 + (y - ry) ** 2)
                if distance <= radius:
                    self.hovered_router = router_id
                    self.tooltip_pos = (mouse_x, mouse_y)
                    break
        
        # Check links if no router is hovered
        if not self.hovered_router:
            for link in self.links:
                router1_id = link.get('router1')
                router2_id = link.get('router2')
                
                if router1_id in self.positions and router2_id in self.positions:
                    x1, y1 = self.positions[router1_id]
                    x2, y2 = self.positions[router2_id]
                    
                    # Check if point is near the link line
                    line_distance = self.point_to_line_distance(x, y, x1, y1, x2, y2)
                    if line_distance <= 5:  # 5 pixel tolerance
                        self.hovered_link = link
                        self.tooltip_pos = (mouse_x, mouse_y)
                        break
        
        # Update if hover state changed
        if (old_hovered_router != self.hovered_router or 
            old_hovered_link != self.hovered_link):
            self.update()
    
    def point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """Calculate distance from point to line segment"""
        A = px - x1
        B = py - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B)
        
        param = dot / len_sq
        
        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D
        
        dx = px - xx
        dy = py - yy
        return math.sqrt(dx * dx + dy * dy)
    
    def paintEvent(self, event):
        """Paint the network visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background with dark theme color
        painter.fillRect(self.rect(), QColor(43, 43, 43))  # Dark background #2b2b2b
        
        # If no routers, show helpful message
        if not self.routers:
            painter.setPen(QPen(QColor(200, 200, 200), 1))  # Light gray text for dark theme
            font = QFont("Arial", 14)
            painter.setFont(font)
            
            # Center the text
            rect = self.rect()
            text = "No network topology loaded. Start a simulation to see routers."
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            return
        
        # Calculate the bounding box of all router positions
        if self.positions:
            x_coords = [pos[0] for pos in self.positions.values()]
            y_coords = [pos[1] for pos in self.positions.values()]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            # Calculate the center of the network
            network_center_x = (min_x + max_x) / 2
            network_center_y = (min_y + max_y) / 2
            
            # Calculate the center of the canvas
            canvas_center_x = self.width() / 2
            canvas_center_y = self.height() / 2
            
            # Calculate translation to center the network
            translate_x = canvas_center_x / self.scale - network_center_x
            translate_y = canvas_center_y / self.scale - network_center_y
            
            # Apply scaling and centering transformation
            painter.scale(self.scale, self.scale)
            painter.translate(translate_x, translate_y)
        else:
            # Apply only scaling if no positions
            painter.scale(self.scale, self.scale)
        
        # Draw links first (so they appear behind routers)
        self.draw_links(painter)
        
        # Draw routers
        self.draw_routers(painter)
        
        # Draw packets
        if self.show_packets:
            self.draw_packets(painter)
        
        # Draw tooltip for hovered router
        if self.hovered_router and self.hovered_router in self.positions:
            router_pos = self.positions[self.hovered_router]
            self.draw_tooltip(painter, router_pos, f"Router: {self.hovered_router}")
            
    def draw_links(self, painter):
        """Draw network links"""
        pen = QPen(QColor(150, 150, 150), 2)  # Light gray for dark theme
        painter.setPen(pen)
        
        for link in self.links:
            router1_id = link.get('router1')
            router2_id = link.get('router2')
            
            if (router1_id in self.positions and 
                router2_id in self.positions):
                
                x1, y1 = self.positions[router1_id]
                x2, y2 = self.positions[router2_id]
                
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                
                # Draw link metrics if enabled
                if self.show_metrics:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    delay = link.get('delay', 0)
                    painter.setPen(QPen(QColor(255, 150, 150)))  # Light red for dark theme
                    painter.drawText(int(mid_x), int(mid_y), f"{delay:.1f}ms")
                    painter.setPen(pen)
                    
    def draw_routers(self, painter):
        """Draw network routers with better visibility"""
        
        for router_id, router_info in self.routers.items():
            if router_id in self.positions:
                x, y = self.positions[router_id]
                
                # Router circle with better contrast
                brush = QBrush(QColor(70, 130, 255))  # Nice blue
                painter.setBrush(brush)
                painter.setPen(QPen(QColor(30, 80, 180), 3))  # Darker blue border
                
                radius = 25
                painter.drawEllipse(int(x - radius), int(y - radius), 
                                  radius * 2, radius * 2)
                
                # Router label with better visibility on dark background
                if self.show_labels:
                    painter.setPen(QPen(QColor(255, 255, 255)))  # White text for dark theme
                    font = QFont("Arial", 10, QFont.Weight.Bold)
                    painter.setFont(font)
                    
                    # Draw text directly - no background needed on dark canvas
                    text = str(router_id)
                    text_rect = painter.fontMetrics().boundingRect(text)
                    text_x = int(x - text_rect.width() / 2)
                    text_y = int(y + text_rect.height() / 4)
                    
                    painter.drawText(text_x, text_y, text)
                
                # Show router metrics if enabled (neighbors count removed)
                if self.show_metrics:
                    # Remove the neighbors count display
                    pass
                
                # Highlight hovered router
                if router_id == self.hovered_router:
                    painter.setPen(QPen(QColor(255, 255, 0), 2))  # Yellow border
                    painter.drawEllipse(int(x - radius), int(y - radius), 
                                      radius * 2, radius * 2)
                    painter.setPen(QPen(QColor(255, 255, 255)))  # Reset to white for text
                    text = str(router_id)
                    text_rect = painter.fontMetrics().boundingRect(text)
                    text_x = int(x - text_rect.width() / 2)
                    text_y = int(y + text_rect.height() / 4)
                    painter.drawText(text_x, text_y, text)
                    
    def draw_packets(self, painter):
        """Draw animated packets with proper colors and types"""
        for packet in self.packets:
            # Get packet position along link
            router1_id = packet.get('source')
            router2_id = packet.get('destination')
            progress = packet.get('progress', 0.0)
            packet_type = packet.get('type', 'UNKNOWN')
            color = packet.get('color', '#95a5a6')
            
            if (router1_id in self.positions and 
                router2_id in self.positions):
                
                x1, y1 = self.positions[router1_id]
                x2, y2 = self.positions[router2_id]
                
                # Calculate current position
                x = x1 + (x2 - x1) * progress
                y = y1 + (y2 - y1) * progress
                
                # Convert hex color to QColor
                if color.startswith('#'):
                    color_val = int(color[1:], 16)
                    r = (color_val >> 16) & 255
                    g = (color_val >> 8) & 255
                    b = color_val & 255
                    packet_color = QColor(r, g, b)
                else:
                    packet_color = QColor(150, 150, 150)  # Default gray
                
                # Draw packet with type-specific visualization
                brush = QBrush(packet_color)
                painter.setBrush(brush)
                painter.setPen(QPen(packet_color.darker(150), 2))
                
                # Different sizes and shapes for different packet types
                if packet_type == 'HELLO':
                    packet_size = 10
                    # Draw as circle for HELLO packets
                    painter.drawEllipse(int(x - packet_size/2), int(y - packet_size/2),
                                      packet_size, packet_size)
                elif packet_type == 'UPDATE':
                    packet_size = 12
                    # Draw as square for UPDATE packets
                    painter.drawRect(int(x - packet_size/2), int(y - packet_size/2),
                                   packet_size, packet_size)
                else:
                    packet_size = 8
                    # Draw as diamond for other packets
                    points = [
                        QPointF(x, y - packet_size/2),
                        QPointF(x + packet_size/2, y),
                        QPointF(x, y + packet_size/2),
                        QPointF(x - packet_size/2, y)
                    ]
                    painter.drawPolygon(points)
                
                # Add a glowing effect for active packets
                glow_color = QColor(packet_color)
                glow_color.setAlpha(50)
                painter.setBrush(QBrush(glow_color))
                painter.setPen(QPen(glow_color, 1))
                glow_size = packet_size + 4
                painter.drawEllipse(int(x - glow_size/2), int(y - glow_size/2),
                                  glow_size, glow_size)
                                  
    def draw_tooltip(self, painter, position, text):
        """Draw tooltip at given position"""
        painter.save()
        
        # Tooltip background
        tooltip_rect = QRectF(position[0] + 10, position[1] - 30, 100, 25)
        painter.setBrush(QBrush(QColor(50, 50, 50, 200)))  # Semi-transparent dark background
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawRoundedRect(tooltip_rect, 5, 5)
        
        # Tooltip text
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(tooltip_rect, Qt.AlignmentFlag.AlignCenter, text)
        
        painter.restore()
