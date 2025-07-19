"""
Advanced Packet Visualization and Path Analysis Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QCheckBox, QSlider, QFrame,
                            QTableWidget, QTableWidgetItem, QTabWidget,
                            QTextEdit, QSplitter, QGroupBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
import math
import random
from collections import defaultdict, deque


class PacketTraceWidget(QWidget):
    """Advanced packet tracing and path analysis"""
    
    def __init__(self):
        super().__init__()
        self.packets = []
        self.active_paths = {}
        self.path_history = []
        self.metric_trends = defaultdict(list)
        self.convergence_data = []
        
        self.init_ui()
        self.setup_animation_timer()
        
    def init_ui(self):
        """Initialize the advanced analysis UI"""
        layout = QVBoxLayout(self)
        
        # Control panel for analysis options
        control_panel = self.create_analysis_controls()
        layout.addWidget(control_panel)
        
        # Create tabbed interface for different analysis views
        self.tab_widget = QTabWidget()
        
        # Real-time packet flow visualization with proper canvas
        self.flow_widget = PacketFlowCanvas()
        self.tab_widget.addTab(self.flow_widget, "Packet Flow")
        
        # Path selection analysis with proper canvas
        self.path_analysis_widget = PathAnalysisCanvas()
        self.tab_widget.addTab(self.path_analysis_widget, "Path Selection")
        
        # Metrics and convergence analysis
        self.metrics_widget = MetricsAnalysisWidget()
        self.tab_widget.addTab(self.metrics_widget, "Metrics Analysis")
        
        # Network state timeline
        self.timeline_widget = NetworkTimelineWidget()
        self.tab_widget.addTab(self.timeline_widget, "Network Timeline")
        
        layout.addWidget(self.tab_widget)
        
    def create_analysis_controls(self):
        """Create controls for advanced analysis"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                color: #ffffff;
            }
        """)
        panel.setMaximumHeight(50)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(15)
        
        # Packet visualization controls
        viz_label = QLabel("Visualization:")
        viz_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
        layout.addWidget(viz_label)
        
        self.show_packets_cb = QCheckBox("Show Packets")
        self.show_packets_cb.setChecked(True)
        self.show_packets_cb.setStyleSheet("color: #ffffff; font-size: 11px;")
        layout.addWidget(self.show_packets_cb)
        
        self.show_paths_cb = QCheckBox("Show Paths")
        self.show_paths_cb.setChecked(True)
        self.show_paths_cb.setStyleSheet("color: #ffffff; font-size: 11px;")
        layout.addWidget(self.show_paths_cb)
        
        self.show_metrics_cb = QCheckBox("Live Metrics")
        self.show_metrics_cb.setChecked(True)
        self.show_metrics_cb.setStyleSheet("color: #ffffff; font-size: 11px;")
        layout.addWidget(self.show_metrics_cb)
        
        separator = QLabel("|")
        separator.setStyleSheet("color: #888888;")
        layout.addWidget(separator)
        
        # Clear metrics button
        clear_button = QPushButton("Clear Metrics")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                border: 1px solid #f44336;
                color: #ffffff;
                font-size: 11px;
                padding: 2px 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        clear_button.clicked.connect(self.clear_metrics)
        layout.addWidget(clear_button)
        
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #888888;")
        layout.addWidget(separator2)
        
        # Analysis controls
        analysis_label = QLabel("Analysis:")
        analysis_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
        layout.addWidget(analysis_label)
        
        self.analysis_mode = QComboBox()
        self.analysis_mode.addItems(['Real-time', 'Historical', 'Comparative', 'Predictive'])
        self.analysis_mode.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                border: 1px solid #666666;
                color: #ffffff;
                font-size: 11px;
                padding: 2px 6px;
            }
        """)
        layout.addWidget(self.analysis_mode)
        
        # Speed control
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
        layout.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_slider.setMaximumWidth(80)
        layout.addWidget(self.speed_slider)
        
        layout.addStretch()
        
        return panel
        
    def setup_animation_timer(self):
        """Setup smooth 30 FPS animation timer for trailing dots"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_visualization)
        self.animation_active = False
        # 30 FPS for super smooth trailing dot animation
        
    def update_state(self, state):
        """Update with new simulation state"""
        # Store state for access by child widgets
        self.state = state
        
        # Extract and analyze packet data
        self.analyze_packets(state.get('packet_logs', []))
        self.analyze_paths(state.get('routers', {}))
        self.analyze_metrics(state.get('routers', {}))
        
        # Update all visualization widgets with proper canvas methods and full state
        self.flow_widget.update_data(self.packets, state.get('routers', {}), state.get('links', []), state)
        self.path_analysis_widget.update_data(self.active_paths, self.path_history)
        self.metrics_widget.update_data(self.metric_trends, state.get('routers', {}))
        self.timeline_widget.update_data(state.get('time', 0), self.convergence_data)
        
    def analyze_packets(self, packet_logs):
        """Advanced packet analysis with smart animation management"""
        # Keep existing packets that are still animating
        active_packets = [p for p in self.packets if p.get('progress', 0) < 1.0]
        
        # Group packets by type and analyze patterns
        packet_types = defaultdict(list)
        new_packets = []
        
        for log in packet_logs[-20:]:  # Last 20 packets
            packet_types[log.get('type', 'UNKNOWN')].append(log)
            
            # Create visual packet representation for sent packets
            if log.get('direction') == 'sent':
                packet_id = f"{log.get('router')}_{log.get('time', 0)}"
                
                # Check if this packet is already being tracked
                existing_packet = next((p for p in self.packets if p['id'] == packet_id), None)
                if not existing_packet:
                    packet = {
                        'id': packet_id,
                        'source': log.get('router'),
                        'destination': log.get('neighbor'),
                        'type': log.get('type', 'UNKNOWN'),
                        'time': log.get('time', 0),
                        'details': log.get('details', {}),
                        'progress': 0.0,
                        'path': [],
                        'metrics': log.get('details', {}),
                        'created_time': log.get('time', 0)
                    }
                    new_packets.append(packet)
        
        # Update packet list
        self.packets = active_packets + new_packets
        
        # Manage animation timer based on packet activity
        self._manage_animation_timer()
                
    def analyze_paths(self, routers):
        """Analyze path selection and changes"""
        current_paths = {}
        
        for router_id, router_info in routers.items():
            routing_table = router_info.get('routing_table', {})
            for dest, route_info in routing_table.items():
                path_key = f"{router_id}->{dest}"
                next_hop = route_info.get('next_hop', '')
                cost = route_info.get('cost', float('inf'))
                
                current_paths[path_key] = {
                    'source': router_id,
                    'destination': dest,
                    'next_hop': next_hop,
                    'cost': cost,
                    'timestamp': 0  # Will be set by simulation
                }
                
        # Detect path changes
        for path_key, new_path in current_paths.items():
            old_path = self.active_paths.get(path_key)
            if old_path and old_path['next_hop'] != new_path['next_hop']:
                # Path changed - record for analysis
                change = {
                    'time': 0,  # Will be set by simulation
                    'path': path_key,
                    'old_next_hop': old_path['next_hop'],
                    'new_next_hop': new_path['next_hop'],
                    'old_cost': old_path['cost'],
                    'new_cost': new_path['cost'],
                    'reason': self.determine_change_reason(old_path, new_path)
                }
                self.path_history.append(change)
                
        self.active_paths = current_paths
        
    def determine_change_reason(self, old_path, new_path):
        """Determine why a path changed"""
        old_cost = old_path['cost']
        new_cost = new_path['cost']
        
        if new_cost < old_cost * 0.8:
            return "Better path found"
        elif new_cost > old_cost * 1.2:
            return "Path degraded"
        elif old_path['next_hop'] == '':
            return "Link failure"
        else:
            return "Load balancing"
            
    def analyze_metrics(self, routers):
        """Analyze network metrics trends using actual routing data"""
        current_time = getattr(self, 'current_sim_time', 0)
        
        # Track unique links processed in this update to avoid duplicates
        processed_links = set()
        
        # Debug: Count how many routers and routes we're processing
        total_routes = 0
        metrics_added = 0
        
        print(f"[METRICS DEBUG] Starting analyze_metrics at time {current_time:.3f}")
        
        for router_id, router_info in routers.items():
            # Get routing data from both routing_table and fib
            routing_table = router_info.get('routing_table', {})
            fib = router_info.get('fib', {})
            
            # Combine both sources, prioritizing routing_table if available
            all_routes = dict(fib)
            all_routes.update(routing_table)
            
            total_routes += len(all_routes)
            
            print(f"[METRICS DEBUG] Router {router_id} has {len(all_routes)} routes: {list(all_routes.keys())}")
            
            # Extract actual metrics from routing data
            for dest, route_info in all_routes.items():
                if dest != router_id:  # Don't include self
                    print(f"[METRICS DEBUG] Route from {router_id} to {dest}: {route_info}")
                    
                    # Extract cost from various possible locations
                    if isinstance(route_info, dict):
                        if 'cost' in route_info:
                            cost = route_info.get('cost', 0)
                        elif 'metrics' in route_info:
                            metrics = route_info.get('metrics', {})
                            cost = metrics.get('total_cost', metrics.get('cost', 0))
                        else:
                            cost = 0
                    else:
                        cost = 0
                    
                    next_hop = route_info.get('next_hop', '') if isinstance(route_info, dict) else ''
                    
                    # Process routes that have a valid next_hop and cost
                    if next_hop and cost > 0:
                        # Create link key based on router to next_hop (the actual link)
                        link_key = f"{router_id}-{next_hop}"
                        
                        # Skip if already processed in this update cycle
                        if link_key in processed_links:
                            continue
                        processed_links.add(link_key)
                        
                        print(f"[METRICS DEBUG] Processing route from {router_id} to {dest} via {next_hop}, cost={cost:.3f}")
                        
                        # Check if we should add new metrics (only if cost changed)
                        should_add_metric = False
                        
                        if link_key not in self.metric_trends or len(self.metric_trends[link_key]) == 0:
                            # No data for this link yet
                            should_add_metric = True
                            print(f"[METRICS] First data point for {link_key}: cost = {cost:.3f}")
                        else:
                            # Check if cost has changed significantly
                            last_metric = self.metric_trends[link_key][-1]
                            last_cost = last_metric.get('cost', 0)
                            
                            # Only add if cost changed by more than 10% or more than 1 unit
                            cost_diff = abs(cost - last_cost)
                            significant_change = cost_diff > max(last_cost * 0.10, 1.0)
                            
                            if significant_change:
                                should_add_metric = True
                                print(f"[METRICS] Significant change for {link_key}: {last_cost:.3f} -> {cost:.3f} (diff: {cost_diff:.3f})")
                            else:
                                print(f"[METRICS] Small change ignored for {link_key}: {last_cost:.3f} -> {cost:.3f} (diff: {cost_diff:.3f})")
                        
                        if should_add_metric:
                            metrics_added += 1
                            
                            # Create metrics based on actual routing cost
                            metrics = {
                                'cost': cost,
                                'delay': min(cost * 2, 120),  # Derive delay from cost
                                'jitter': min(cost * 0.1, 20),  # Derive jitter from cost
                                'packet_loss': min(cost * 0.05, 8),  # Derive loss from cost
                                'congestion': min(cost * 0.8, 80),  # Derive congestion from cost
                                'timestamp': current_time
                            }
                            
                            if link_key not in self.metric_trends:
                                self.metric_trends[link_key] = []
                            self.metric_trends[link_key].append(metrics)
                            
                            # Keep only recent data (last 30 samples to prevent memory bloat)
                            if len(self.metric_trends[link_key]) > 30:
                                self.metric_trends[link_key] = self.metric_trends[link_key][-30:]
        
        # Debug summary
        if total_routes > 0:
            print(f"[METRICS SUMMARY] Processed {total_routes} total routes, added {metrics_added} new metric points, tracking {len(self.metric_trends)} links")
    
    def clear_metrics(self):
        """Clear all accumulated metrics data"""
        self.metric_trends.clear()
        print("Metrics data cleared - fresh start for metrics analysis")
        
        # Force update of metrics widget
        if hasattr(self, 'metrics_widget'):
            self.metrics_widget.update_data({}, getattr(self, 'state', {}).get('routers', {}))
                    
    def update_visualization(self):
        """Update trailing dot animations at smooth 30 FPS"""
        if not self.packets:
            # No packets to animate
            return
            
        # Update packet progress with smooth animation
        speed_multiplier = self.speed_slider.value()
        packets_to_remove = []
        
        # Smooth 30 FPS animation step (1/30 = 0.033 per frame)
        animation_step = 0.01 * speed_multiplier  # Slower for smoother trails
        
        for i, packet in enumerate(self.packets):
            packet['progress'] += animation_step
            if packet['progress'] >= 1.0:
                packet['progress'] = 1.0
                packets_to_remove.append(i)
                
        # Remove completed packets
        for i in reversed(packets_to_remove):
            del self.packets[i]
            
        # Check if we should stop animation
        self._manage_animation_timer()
        
        # Update the packet flow canvas for smooth trailing dots
        if hasattr(self, 'flow_widget'):
            self.flow_widget.update()
        
    def _manage_animation_timer(self):
        """Start/stop 30 FPS animation timer based on packet activity"""
        has_active_packets = any(p.get('progress', 0) < 1.0 for p in self.packets)
        
        if has_active_packets and not self.animation_active:
            # Start smooth 30 FPS animation for trailing dots
            self.animation_timer.start(33)  # 33ms = 30 FPS for super smooth trails
            self.animation_active = True
            print(f"Starting 30 FPS trailing dot animation - {len([p for p in self.packets if p.get('progress', 0) < 1.0])} packets active")
        elif not has_active_packets and self.animation_active:
            # Stop animation
            self.animation_timer.stop()
            self.animation_active = False
            print("⏹️ Stopping trailing dot animation - no active packets")
            
            # Clean up completed packets
            self.packets = [p for p in self.packets if p.get('progress', 0) < 1.0]
            
    def update_analysis_displays(self):
        """Update the analysis display widgets with current data"""
        # Update packet flow widget
        if hasattr(self, 'flow_widget'):
            packet_count = len(self.packets)
            active_count = len([p for p in self.packets if p.get('progress', 0) < 1.0])
            status_text = f"""Packet Animation Status
            
Active Packets: {active_count}
Total Tracked: {packet_count}
Animation: {'Running' if self.animation_active else 'Paused'}
Speed: {self.speed_slider.value()}/10

Recent Packets:"""
            
            for packet in self.packets[-5:]:  # Show last 5 packets
                progress_bar = "█" * int(packet.get('progress', 0) * 10) + "░" * (10 - int(packet.get('progress', 0) * 10))
                status_text += f"\n  {packet.get('type', 'UNK')} {packet.get('source', '?')}→{packet.get('destination', '?')}: [{progress_bar}] {int(packet.get('progress', 0)*100)}%"
            
            self.flow_widget.setText(status_text)
        
        # Update path analysis
        if hasattr(self, 'path_analysis_widget') and hasattr(self.path_analysis_widget, 'setPlainText'):
            path_text = "Path Selection Analysis\n\n"
            if self.active_paths:
                for path_key, path_info in list(self.active_paths.items())[:10]:  # Show first 10 paths
                    path_text += f"{path_key}: via {path_info.get('next_hop', 'N/A')} (cost: {path_info.get('cost', '∞')})\n"
            else:
                path_text += "No active paths detected yet..."
            self.path_analysis_widget.setPlainText(path_text)
        
        # Update metrics analysis
        if hasattr(self, 'metrics_widget') and hasattr(self.metrics_widget, 'setPlainText'):
            metrics_text = "Network Metrics Analysis\n\n"
            if self.metric_trends:
                for metric_name, values in self.metric_trends.items():
                    if values:
                        avg = sum(values) / len(values)
                        metrics_text += f"{metric_name}: avg={avg:.2f}, samples={len(values)}\n"
            else:
                metrics_text += "Collecting metrics data..."
            self.metrics_widget.setPlainText(metrics_text)
        
        # Update timeline
        if hasattr(self, 'timeline_widget') and hasattr(self.timeline_widget, 'setPlainText'):
            timeline_text = "Network Timeline\n\n"
            if self.convergence_data:
                for event in self.convergence_data[-10:]:  # Show last 10 events
                    timeline_text += f"{event.get('time', '?')}: {event.get('description', 'Unknown event')}\n"
            else:
                timeline_text += "Monitoring network events..."
            self.timeline_widget.setPlainText(timeline_text)


class PacketFlowCanvas(QWidget):
    """Canvas for real-time packet flow visualization with beautiful animations"""
    
    def __init__(self):
        super().__init__()
        self.packets = []
        self.routers = {}
        self.links = []
        self.state = {}  # Store full state for access in paint
        self.packet_trails = defaultdict(list)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #555555;
                border-radius: 3px;
            }
        """)
        
    def update_data(self, packets, routers, links, state=None):
        """Update with new packet and network data"""
        self.packets = packets
        self.routers = routers
        self.links = links
        if state:
            self.state = state
        self.update()
        
    def paintEvent(self, event):
        """Paint beautiful packet flow visualization using SAME network as main view"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dark background
        painter.fillRect(self.rect(), QColor(26, 26, 26))
        
        if not self.routers:
            # Show status message
            painter.setPen(QPen(QColor(200, 200, 200)))
            font = QFont("Arial", 12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           "Waiting for packet data...")
            return
            
        # USE THE SAME ROUTER POSITIONS AS MAIN NETWORK VIEW
        # Get positions directly from shared state
        router_positions = self.state.get('router_positions', {})
        
        # If no shared positions, try to extract from router data
        if not router_positions:
            for router_id, router_info in self.routers.items():
                position = router_info.get('position')
                if position:
                    router_positions[router_id] = position
        
        # Scale positions to fit this canvas if needed
        if router_positions:
            canvas_width = self.width()
            canvas_height = self.height()
            padding = 50
            
            # Find bounds of current positions
            x_coords = [pos[0] for pos in router_positions.values()]
            y_coords = [pos[1] for pos in router_positions.values()]
            
            if x_coords and y_coords:
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                
                # Scale to fit canvas
                pos_width = max_x - min_x if max_x > min_x else 300
                pos_height = max_y - min_y if max_y > min_y else 200
                
                scale_x = (canvas_width - 2 * padding) / pos_width
                scale_y = (canvas_height - 2 * padding) / pos_height
                scale = min(scale_x, scale_y, 1.0)  # Don't scale up
                
                # Center the network
                center_x = canvas_width / 2
                center_y = canvas_height / 2
                pos_center_x = (min_x + max_x) / 2
                pos_center_y = (min_y + max_y) / 2
                
                # Apply scaling and centering
                scaled_positions = {}
                for router_id, (x, y) in router_positions.items():
                    scaled_x = center_x + (x - pos_center_x) * scale
                    scaled_y = center_y + (y - pos_center_y) * scale
                    scaled_positions[router_id] = (scaled_x, scaled_y)
                
                router_positions = scaled_positions
        
        # Draw links using ACTUAL topology links (not full mesh)
        for link in self.links:
            router1_id = link.get('router1')
            router2_id = link.get('router2')
            
            if router1_id in router_positions and router2_id in router_positions:
                x1, y1 = router_positions[router1_id]
                x2, y2 = router_positions[router2_id]
                
                # Draw glow effect for actual links only
                for width in [6, 4, 2]:
                    alpha = 30 if width == 6 else (60 if width == 4 else 100)
                    painter.setPen(QPen(QColor(100, 150, 255, alpha), width))
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw routers with beautiful styling
        for router_id, router_info in self.routers.items():
            if router_id in router_positions:
                x, y = router_positions[router_id]
                
                # Router glow effect
                for radius_offset in [15, 10, 5]:
                    alpha = 20 if radius_offset == 15 else (40 if radius_offset == 10 else 80)
                    painter.setBrush(QBrush(QColor(70, 130, 255, alpha)))
                    painter.setPen(QPen(QColor(70, 130, 255, alpha), 1))
                    painter.drawEllipse(int(x - radius_offset), int(y - radius_offset), 
                                      radius_offset * 2, radius_offset * 2)
                
                # Main router circle
                painter.setBrush(QBrush(QColor(70, 130, 255)))
                painter.setPen(QPen(QColor(30, 80, 180), 2))
                painter.drawEllipse(int(x - 20), int(y - 20), 40, 40)
                
                # Router label
                painter.setPen(QPen(QColor(255, 255, 255)))
                font = QFont("Arial", 9, QFont.Weight.Bold)
                painter.setFont(font)
                text_rect = painter.fontMetrics().boundingRect(str(router_id))
                text_x = int(x - text_rect.width() / 2)
                text_y = int(y + text_rect.height() / 2)
                painter.drawText(text_x, text_y, str(router_id))
        
        # Draw beautiful trailing dot animations
        for packet in self.packets:
            source = packet.get('source')
            destination = packet.get('destination')
            progress = packet.get('progress', 0.0)
            packet_type = packet.get('type', 'UNKNOWN')
            
            if source in router_positions and destination in router_positions:
                x1, y1 = router_positions[source]
                x2, y2 = router_positions[destination]
                
                # Calculate current packet position
                x = x1 + (x2 - x1) * progress
                y = y1 + (y2 - y1) * progress
                
                # Create trailing dots effect - more dots for smoother trail
                trail_key = f"{source}->{destination}"
                self.packet_trails[trail_key].append((x, y))
                if len(self.packet_trails[trail_key]) > 15:  # More dots for longer trail
                    self.packet_trails[trail_key].pop(0)
                
                # Draw smooth trailing dots with fade effect
                for i, (trail_x, trail_y) in enumerate(self.packet_trails[trail_key]):
                    # Calculate fade alpha for smooth trailing effect
                    trail_position = (i + 1) / len(self.packet_trails[trail_key])
                    alpha = int(255 * trail_position * 0.8)  # Fade from 0 to 80% opacity
                    
                    # Size gradually increases towards the front
                    dot_size = 2 + (trail_position * 4)  # 2px to 6px
                    
                    # Color based on packet type with trailing effect
                    if packet_type == 'HELLO':
                        trail_color = QColor(100, 255, 100, alpha)  # Green trail
                    elif packet_type == 'UPDATE':
                        trail_color = QColor(255, 100, 100, alpha)  # Red trail
                    elif packet_type == 'QUERY':
                        trail_color = QColor(255, 255, 100, alpha)  # Yellow trail
                    elif packet_type == 'REPLY':
                        trail_color = QColor(100, 100, 255, alpha)  # Blue trail
                    else:
                        trail_color = QColor(255, 255, 255, alpha)  # White trail
                    
                    painter.setBrush(QBrush(trail_color))
                    painter.setPen(QPen(trail_color, 1))
                    painter.drawEllipse(int(trail_x - dot_size/2), int(trail_y - dot_size/2), 
                                      int(dot_size), int(dot_size))
                
                # Draw main packet (larger and brighter than trail)
                if packet_type == 'HELLO':
                    packet_color = QColor(100, 255, 100)  # Green for hello
                elif packet_type == 'UPDATE':
                    packet_color = QColor(255, 100, 100)  # Red for updates
                elif packet_type == 'QUERY':
                    packet_color = QColor(255, 255, 100)  # Yellow for queries
                elif packet_type == 'REPLY':
                    packet_color = QColor(100, 100, 255)  # Blue for replies
                else:
                    packet_color = QColor(255, 255, 255)  # White for unknown
                
                # Main packet with glow
                painter.setBrush(QBrush(packet_color))
                painter.setPen(QPen(packet_color.darker(120), 2))
                main_packet_size = 8
                painter.drawEllipse(int(x - main_packet_size/2), int(y - main_packet_size/2), 
                                  main_packet_size, main_packet_size)
                
                # Packet type indicator (small text)
                painter.setPen(QPen(QColor(255, 255, 255)))
                font = QFont("Arial", 6, QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(int(x - 8), int(y + 15), packet_type[:3])


class PathAnalysisCanvas(QWidget):
    """Canvas for path selection analysis visualization"""
    
    def __init__(self):
        super().__init__()
        self.active_paths = {}
        self.path_history = []
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #555555;
                border-radius: 3px;
            }
        """)
        
    def update_data(self, active_paths, path_history):
        """Update with path analysis data"""
        self.active_paths = active_paths
        self.path_history = path_history
        self.update()
        
    def paintEvent(self, event):
        """Paint path analysis visualization"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dark background
        painter.fillRect(self.rect(), QColor(26, 26, 26))
        
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = QFont("Arial", 12)
        painter.setFont(font)
        
        if not self.active_paths:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           "Path analysis data will appear here...")
        else:
            # Draw path analysis info
            y_offset = 30
            painter.drawText(20, y_offset, f"Active Paths: {len(self.active_paths)}")
            y_offset += 25
            painter.drawText(20, y_offset, f"History Events: {len(self.path_history)}")


class MetricsAnalysisWidget(QWidget):
    """Widget for metrics analysis and trends"""
    
    def __init__(self):
        super().__init__()
        self.metrics_data = {}
        self.routers = {}
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #555555;
                border-radius: 3px;
            }
        """)
        
    def update_data(self, metrics_data, routers):
        """Update metrics data"""
        self.metrics_data = metrics_data
        self.routers = routers
        self.update()
        
    def paintEvent(self, event):
        """Paint metrics analysis with actual data"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dark background
        painter.fillRect(self.rect(), QColor(26, 26, 26))
        
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        if not self.metrics_data:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                           "Collecting metrics data...")
            return
        
        # Display metrics data
        y_offset = 30
        painter.drawText(20, y_offset, "Network Metrics Analysis")
        y_offset += 30
        
        for link_name, metric_samples in list(self.metrics_data.items())[:8]:  # Show top 8 links
            if metric_samples:
                # Show current cost vs. initial cost instead of accumulating average
                current_cost = metric_samples[-1].get('cost', 0)  # Latest cost
                initial_cost = metric_samples[0].get('cost', 0)   # First recorded cost
                
                current_delay = metric_samples[-1].get('delay', 0)
                current_loss = metric_samples[-1].get('packet_loss', 0)
                
                # Calculate change from initial
                cost_change = current_cost - initial_cost
                change_percent = (cost_change / initial_cost * 100) if initial_cost > 0 else 0
                
                painter.drawText(20, y_offset, f"{link_name}:")
                y_offset += 20
                painter.drawText(40, y_offset, f"Current Cost: {current_cost:.2f} (Initial: {initial_cost:.2f})")
                y_offset += 15
                
                # Show change with color indication (conceptually)
                change_text = f"Change: {cost_change:+.2f} ({change_percent:+.1f}%)"
                painter.drawText(40, y_offset, change_text)
                y_offset += 15
                
                painter.drawText(40, y_offset, f"Delay: {current_delay:.1f}ms, Loss: {current_loss:.1f}%")
                y_offset += 15
                
                painter.drawText(40, y_offset, f"Updates: {len(metric_samples)} (significant changes only)")
                y_offset += 25
                
                if y_offset > self.height() - 50:
                    break


class NetworkTimelineWidget(QWidget):
    """Widget for network state timeline"""
    
    def __init__(self):
        super().__init__()
        self.timeline_data = []
        self.current_time = 0
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #555555;
                border-radius: 3px;
            }
        """)
        
    def update_data(self, current_time, timeline_data):
        """Update timeline data"""
        self.current_time = current_time
        self.timeline_data = timeline_data
        self.update()
        
    def paintEvent(self, event):
        """Paint network timeline"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dark background
        painter.fillRect(self.rect(), QColor(26, 26, 26))
        
        painter.setPen(QPen(QColor(200, 200, 200)))
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 
                       f"⏰ Network timeline - Time: {self.current_time:.2f}s")
