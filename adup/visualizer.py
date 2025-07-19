# Network Visualization Module

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
import numpy as np
from collections import deque
import time

class NetworkVisualizer:
    def __init__(self, simulation):
        self.simulation = simulation
        self.graph = nx.Graph()
        self.packet_queue = deque()  # Store packets for animation
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.positions = {}
        
    def setup_topology(self):
        """Build the network graph from the simulation topology"""
        # Add nodes (routers)
        for name, router in self.simulation.routers.items():
            self.graph.add_node(name, router=router)
        
        # Add edges (links) - we'll detect them from router interfaces
        edges_added = set()
        for name, router in self.simulation.routers.items():
            for iface_name, iface_info in router.interfaces.items():
                if 'link' in iface_info:
                    link = iface_info['link']
                    # Find the other router connected to this link
                    other_router = link.router1 if link.router2.name == name else link.router2
                    edge = tuple(sorted([name, other_router.name]))
                    if edge not in edges_added:
                        self.graph.add_edge(name, other_router.name, link=link)
                        edges_added.add(edge)
        
        # Set positions for the nodes
        self.positions = nx.spring_layout(self.graph, k=3, iterations=50)
        
    def add_packet_event(self, time, source, dest, packet_type, packet_data=None):
        """Add a packet event to the animation queue"""
        self.packet_queue.append({
            'time': time,
            'source': source,
            'dest': dest,
            'type': packet_type,
            'data': packet_data
        })
    
    def animate_network(self, interval=500):
        """Create an animated visualization of the network"""
        self.setup_topology()
        
        # Create the animation
        ani = animation.FuncAnimation(
            self.fig, self.update_plot, frames=200, 
            interval=interval, blit=False, repeat=True
        )
        
        plt.title("ADUP Protocol Network Visualization")
        plt.axis('off')
        return ani
    
    def update_plot(self, frame):
        """Update the plot for each animation frame"""
        self.ax.clear()
        
        # Draw the basic network topology
        nx.draw_networkx_nodes(
            self.graph, self.positions, 
            node_color='lightblue', 
            node_size=2000,
            ax=self.ax
        )
        
        nx.draw_networkx_labels(
            self.graph, self.positions, 
            font_size=12, font_weight='bold',
            ax=self.ax
        )
        
        nx.draw_networkx_edges(
            self.graph, self.positions, 
            edge_color='gray', width=2,
            ax=self.ax
        )
        
        # Simulate packet movement (this would be enhanced with real packet data)
        if frame % 20 == 0:  # Show packet movement every 20 frames
            # Add some visual effects for packet transmission
            for edge in self.graph.edges():
                x_coords = [self.positions[edge[0]][0], self.positions[edge[1]][0]]
                y_coords = [self.positions[edge[0]][1], self.positions[edge[1]][1]]
                
                # Add a moving dot to represent packet
                t = (frame % 20) / 20.0
                packet_x = x_coords[0] + t * (x_coords[1] - x_coords[0])
                packet_y = y_coords[0] + t * (y_coords[1] - y_coords[0])
                
                self.ax.plot(packet_x, packet_y, 'ro', markersize=8, alpha=0.7)
        
        # Add routing table information as text
        info_text = self.get_routing_info()
        self.ax.text(0.02, 0.98, info_text, transform=self.ax.transAxes, 
                    fontsize=9, verticalalignment='top', 
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        self.ax.set_title(f"ADUP Network - Frame {frame}")
        
    def get_routing_info(self):
        """Get current routing table information for display"""
        info_lines = ["Routing Tables:"]
        for name, router in self.simulation.routers.items():
            info_lines.append(f"\n{name}:")
            if hasattr(router, 'fib') and router.fib:
                for dest, route_info in router.fib.items():
                    next_hop = route_info['next_hop']
                    cost = route_info['metrics']['total_delay']
                    info_lines.append(f"  {dest} -> {next_hop} (cost: {cost})")
            else:
                info_lines.append("  No routes")
        return '\n'.join(info_lines)
    
    def show_static_topology(self):
        """Show a static view of the network topology"""
        self.setup_topology()
        
        plt.figure(figsize=(10, 8))
        
        # Draw nodes with different colors based on their role
        node_colors = []
        for node in self.graph.nodes():
            router = self.simulation.routers[node]
            if len(router.interfaces) > 1:
                node_colors.append('lightcoral')  # Core routers
            else:
                node_colors.append('lightblue')   # Edge routers
        
        nx.draw_networkx_nodes(
            self.graph, self.positions, 
            node_color=node_colors, 
            node_size=2000
        )
        
        nx.draw_networkx_labels(
            self.graph, self.positions, 
            font_size=12, font_weight='bold'
        )
        
        nx.draw_networkx_edges(
            self.graph, self.positions, 
            edge_color='gray', width=2
        )
        
        # Add network information
        for i, (name, router) in enumerate(self.simulation.routers.items()):
            if hasattr(router, 'networks') and router.networks:
                networks_text = ', '.join(router.networks)
                plt.text(self.positions[name][0], self.positions[name][1] - 0.15, 
                        f"Networks: {networks_text}", 
                        ha='center', fontsize=8, 
                        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        plt.title("ADUP Network Topology")
        plt.axis('off')
        plt.tight_layout()
        plt.show()

class SimulationLogger:
    """Logger to capture simulation events for visualization"""
    def __init__(self):
        self.events = []
    
    def log_packet(self, time, source, dest, packet_type, details=None):
        """Log a packet transmission event"""
        self.events.append({
            'time': time,
            'source': source,
            'dest': dest,
            'type': packet_type,
            'details': details
        })
    
    def log_route_change(self, time, router, destination, old_route, new_route):
        """Log a routing table change"""
        self.events.append({
            'time': time,
            'router': router,
            'destination': destination,
            'old_route': old_route,
            'new_route': new_route,
            'type': 'route_change'
        })
    
    def get_events_at_time(self, time_range):
        """Get events within a specific time range"""
        return [event for event in self.events 
                if time_range[0] <= event['time'] <= time_range[1]]
