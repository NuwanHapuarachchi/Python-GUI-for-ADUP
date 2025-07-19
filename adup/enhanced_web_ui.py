# Enhanced Web UI with Dynamic Network Generation and Real-time Visualization

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import threading
import time
import json
import simpy
from datetime import datetime
from adup.simulation import Simulation
from adup.visualizer import NetworkVisualizer
from adup.router import Router

class EnhancedADUPWebUI:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.simulation = None
        self.visualizer = None
        self.simulation_thread = None
        self.is_running = False
        self.network_config = {
            'num_routers': 3,
            'topology_type': 'linear',
            'custom_links': []
        }
        self.setup_layout()
        self.setup_callbacks()
        
    def setup_layout(self):
        """Setup the enhanced web UI layout"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("ADUP Protocol - Advanced Routing Simulation", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
                html.P("Advanced Diffusing Update Protocol with Multi-Metric Optimization", 
                       style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '16px'})
            ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),
            
            # Main controls row
            html.Div([
                # Network Configuration Panel
                html.Div([
                    html.H3("Network Configuration", style={'color': '#34495e'}),
                    
                    html.Label("Number of Routers:"),
                    dcc.Slider(
                        id='num-routers-slider',
                        min=3, max=10, step=1, value=3,
                        marks={i: str(i) for i in range(3, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    
                    html.Label("Topology Type:", style={'marginTop': '15px'}),
                    dcc.Dropdown(
                        id='topology-dropdown',
                        options=[
                            {'label': 'Linear (R1-R2-R3-...)', 'value': 'linear'},
                            {'label': 'Ring (All connected in circle)', 'value': 'ring'},
                            {'label': 'Star (Central hub)', 'value': 'star'},
                            {'label': 'Mesh (Full connectivity)', 'value': 'mesh'},
                            {'label': 'Custom', 'value': 'custom'}
                        ],
                        value='linear',
                        style={'marginBottom': '15px'}
                    ),
                    
                    html.Button('Generate Network', id='generate-btn', n_clicks=0,
                               style={'backgroundColor': '#3498db', 'color': 'white', 
                                     'border': 'none', 'padding': '10px 20px', 'margin': '5px', 'borderRadius': '5px'}),
                    
                    html.Div(id='network-status', style={'margin': '10px', 'fontSize': '14px'})
                    
                ], className='three columns', style={'border': '1px solid #bdc3c7', 'padding': '15px', 'borderRadius': '5px'}),
                
                # Simulation Controls
                html.Div([
                    html.H3("Simulation Controls", style={'color': '#34495e'}),
                    
                    html.Button('▶️ Start Simulation', id='start-btn', n_clicks=0,
                               style={'backgroundColor': '#27ae60', 'color': 'white', 
                                     'border': 'none', 'padding': '10px 20px', 'margin': '5px', 'borderRadius': '5px'}),
                    html.Button('⏹️ Stop Simulation', id='stop-btn', n_clicks=0,
                               style={'backgroundColor': '#e74c3c', 'color': 'white', 
                                     'border': 'none', 'padding': '10px 20px', 'margin': '5px', 'borderRadius': '5px'}),
                    html.Button('Reset', id='reset-btn', n_clicks=0,
                               style={'backgroundColor': '#f39c12', 'color': 'white', 
                                     'border': 'none', 'padding': '10px 20px', 'margin': '5px', 'borderRadius': '5px'}),
                    
                    html.Div(id='simulation-status', style={'margin': '10px', 'fontSize': '14px'}),
                    
                    html.H4("Simulation Speed", style={'marginTop': '20px'}),
                    dcc.Slider(
                        id='speed-slider',
                        min=0.5, max=5, step=0.5, value=1,
                        marks={i: f"{i}x" for i in [0.5, 1, 2, 3, 4, 5]},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                    
                ], className='three columns', style={'border': '1px solid #bdc3c7', 'padding': '15px', 'borderRadius': '5px'}),
                
                # Live Network Topology
                html.Div([
                    html.H3("Network Topology", style={'color': '#34495e'}),
                    dcc.Graph(id='network-graph', style={'height': '300px'}),
                ], className='six columns', style={'border': '1px solid #bdc3c7', 'padding': '15px', 'borderRadius': '5px'}),
            ], className='row', style={'marginBottom': '20px'}),
            
            # Detailed Information Row
            html.Div([
                # Routing Tables
                html.Div([
                    html.H3("Routing Tables", style={'color': '#34495e'}),
                    html.Div(id='routing-tables-detailed'),
                ], className='four columns', style={'border': '1px solid #bdc3c7', 'padding': '15px', 'borderRadius': '5px'}),
                
                # Packet Flow Visualization
                html.Div([
                    html.H3("Live Packet Flow", style={'color': '#34495e'}),
                    html.Div(id='packet-flow-viz', 
                            style={'height': '300px', 'overflow': 'auto', 
                                   'border': '1px solid #ddd', 'padding': '10px', 'backgroundColor': '#f8f9fa'}),
                ], className='four columns', style={'border': '1px solid #bdc3c7', 'padding': '15px', 'borderRadius': '5px'}),
                
                # Protocol Statistics
                html.Div([
                    html.H3("Protocol Statistics", style={'color': '#34495e'}),
                    dcc.Graph(id='stats-graph', style={'height': '280px'}),
                ], className='four columns', style={'border': '1px solid #bdc3c7', 'padding': '15px', 'borderRadius': '5px'}),
            ], className='row', style={'marginBottom': '20px'}),
            
            # Advanced Monitoring
            html.Div([
                html.H3("Advanced Protocol Monitoring", style={'color': '#34495e'}),
                
                dcc.Tabs(id='monitoring-tabs', value='neighbor-table', children=[
                    dcc.Tab(label='Neighbor Tables', value='neighbor-table'),
                    dcc.Tab(label='Route Changes', value='route-changes'),
                    dcc.Tab(label='Metrics Analysis', value='metrics-analysis'),
                    dcc.Tab(label='DUAL State', value='dual-state'),
                ]),
                
                html.Div(id='monitoring-content', style={'marginTop': '20px'})
            ], style={'border': '1px solid #bdc3c7', 'padding': '15px', 'borderRadius': '5px'}),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=1000,  # Update every 1 second for real-time feel
                n_intervals=0,
                disabled=True
            ),
            
            # Store component for network config
            dcc.Store(id='network-config-store', data=self.network_config)
        ])
    
    def setup_callbacks(self):
        """Setup enhanced dash callbacks"""
        
        @self.app.callback(
            Output('network-config-store', 'data'),
            Output('network-status', 'children'),
            [Input('generate-btn', 'n_clicks')],
            [State('num-routers-slider', 'value'),
             State('topology-dropdown', 'value')]
        )
        def update_network_config(n_clicks, num_routers, topology_type):
            if n_clicks > 0:
                self.network_config = {
                    'num_routers': num_routers,
                    'topology_type': topology_type,
                    'custom_links': []
                }
                
                return self.network_config, html.Div([
                    html.P(f"Network configured: {num_routers} routers, {topology_type} topology", 
                           style={'color': 'green'}),
                    html.P(f"Generated at: {datetime.now().strftime('%H:%M:%S')}", 
                           style={'fontSize': '12px', 'color': '#7f8c8d'})
                ])
            
            return self.network_config, html.P("Ready to generate network...")
        
        @self.app.callback(
            [Output('simulation-status', 'children'),
             Output('network-graph', 'figure'),
             Output('routing-tables-detailed', 'children'),
             Output('packet-flow-viz', 'children'),
             Output('stats-graph', 'figure'),
             Output('interval-component', 'disabled')],
            [Input('interval-component', 'n_intervals'),
             Input('start-btn', 'n_clicks'),
             Input('stop-btn', 'n_clicks'),
             Input('reset-btn', 'n_clicks')],
            [State('network-config-store', 'data')]
        )
        def update_dashboard(n_intervals, start_clicks, stop_clicks, reset_clicks, network_config):
            ctx = callback_context
            
            if ctx.triggered:
                button_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                if button_id == 'start-btn' and not self.is_running:
                    self.start_enhanced_simulation(network_config)
                elif button_id == 'stop-btn' and self.is_running:
                    self.stop_simulation()
                elif button_id == 'reset-btn':
                    self.reset_simulation()
            
            # Update all components
            status = self.get_enhanced_simulation_status()
            network_fig = self.get_enhanced_network_figure()
            routing_tables = self.get_detailed_routing_tables()
            packet_flow = self.get_live_packet_flow()
            stats_fig = self.get_protocol_statistics()
            interval_disabled = not self.is_running
            
            return status, network_fig, routing_tables, packet_flow, stats_fig, interval_disabled
        
        @self.app.callback(
            Output('monitoring-content', 'children'),
            [Input('monitoring-tabs', 'value'),
             Input('interval-component', 'n_intervals')]
        )
        def update_monitoring_tab(active_tab, n_intervals):
            if active_tab == 'neighbor-table':
                return self.get_neighbor_tables_display()
            elif active_tab == 'route-changes':
                return self.get_route_changes_display()
            elif active_tab == 'metrics-analysis':
                return self.get_metrics_analysis()
            elif active_tab == 'dual-state':
                return self.get_dual_state_display()
            
            return html.P("Select a monitoring tab...")
    
    def start_enhanced_simulation(self, network_config):
        """Start enhanced simulation with custom network"""
        if not self.is_running:
            self.simulation = EnhancedSimulation(network_config)
            
            def run_sim():
                self.is_running = True
                try:
                    self.simulation.run(until=120)  # Run for 2 minutes
                except Exception as e:
                    print(f"Simulation error: {e}")
                finally:
                    self.is_running = False
            
            self.simulation_thread = threading.Thread(target=run_sim)
            self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop the current simulation"""
        self.is_running = False
    
    def reset_simulation(self):
        """Reset the simulation"""
        self.stop_simulation()
        self.simulation = None
    
    def get_enhanced_simulation_status(self):
        """Get enhanced simulation status with more details"""
        if self.is_running and self.simulation:
            current_time = self.simulation.env.now
            num_routers = len(self.simulation.routers) if hasattr(self.simulation, 'routers') else 0
            
            # Calculate some statistics
            total_packets = 0
            total_routes = 0
            
            if hasattr(self.simulation, 'routers'):
                for router in self.simulation.routers.values():
                    if hasattr(router, 'packet_log'):
                        total_packets += len(router.packet_log)
                    if hasattr(router, 'fib'):
                        total_routes += len(router.fib)
            
            return html.Div([
                html.P(f"Status: Running", style={'color': 'green', 'fontWeight': 'bold'}),
                html.P(f"Simulation Time: {current_time:.2f}s"),
                html.P(f"Active Routers: {num_routers}"),
                html.P(f"Packets Exchanged: {total_packets}"),
                html.P(f"Active Routes: {total_routes}")
            ])
        else:
            return html.Div([
                html.P("Status: Stopped", style={'color': 'red', 'fontWeight': 'bold'}),
                html.P("Simulation Time: 0.00s"),
                html.P("Active Routers: 0")
            ])
    
    def get_enhanced_network_figure(self):
        """Generate enhanced network topology with real-time packet animation"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return go.Figure().add_annotation(text="No simulation running", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        # Create dynamic positions based on topology type
        positions = self.calculate_router_positions()
        
        # Build the network graph
        edge_x, edge_y = [], []
        node_x, node_y, node_text, node_colors = [], [], [], []
        
        # Add edges (links)
        for name, router in self.simulation.routers.items():
            if name in positions:
                x1, y1 = positions[name]
                node_x.append(x1)
                node_y.append(y1)
                node_text.append(f"{name}<br>State: {getattr(router, 'state', 'UNKNOWN')}")
                
                # Color based on router state
                state = getattr(router, 'state', 'UNKNOWN')
                if state == 'ACTIVE':
                    node_colors.append('lightgreen')
                elif state == 'ADVERTISING':
                    node_colors.append('orange')
                else:
                    node_colors.append('lightblue')
                
                # Add edges to connected routers
                for iface_name, iface_info in router.interfaces.items():
                    if 'link' in iface_info:
                        link = iface_info['link']
                        other_router = link.router1 if link.router2.name == name else link.router2
                        if other_router.name in positions:
                            x2, y2 = positions[other_router.name]
                            edge_x.extend([x1, x2, None])
                            edge_y.extend([y1, y2, None])
        
        # Create the plot
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=2, color='#888'),
                                hoverinfo='none', mode='lines', name='Links'))
        
        # Add nodes
        fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text',
                                hoverinfo='text', text=[t.split('<br>')[0] for t in node_text],
                                hovertext=node_text, textposition="middle center",
                                marker=dict(size=40, color=node_colors, 
                                          line=dict(width=2, color='darkblue')),
                                name='Routers'))
        
        fig.update_layout(
            title='Live Network Topology',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        return fig
    
    def calculate_router_positions(self):
        """Calculate router positions based on topology type"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return {}
        
        routers = list(self.simulation.routers.keys())
        n = len(routers)
        positions = {}
        
        topology_type = self.network_config.get('topology_type', 'linear')
        
        if topology_type == 'linear':
            for i, router in enumerate(routers):
                positions[router] = (i * 2, 0)
        elif topology_type == 'ring':
            import math
            for i, router in enumerate(routers):
                angle = 2 * math.pi * i / n
                positions[router] = (math.cos(angle) * 2, math.sin(angle) * 2)
        elif topology_type == 'star':
            positions[routers[0]] = (0, 0)  # Central hub
            import math
            for i, router in enumerate(routers[1:], 1):
                angle = 2 * math.pi * (i-1) / (n-1)
                positions[router] = (math.cos(angle) * 2, math.sin(angle) * 2)
        else:  # mesh or default
            import math
            for i, router in enumerate(routers):
                positions[router] = ((i % 3) * 2, (i // 3) * 2)
        
        return positions
    
    def get_detailed_routing_tables(self):
        """Generate detailed routing tables with metrics"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return html.Div("No simulation running")
        
        tables = []
        for name, router in self.simulation.routers.items():
            if hasattr(router, 'fib') and router.fib:
                rows = []
                for dest, route_info in router.fib.items():
                    next_hop = route_info['next_hop']
                    cost = route_info['metrics'].get('total_cost', 'N/A')
                    rows.append(html.Tr([
                        html.Td(dest, style={'border': '1px solid #ddd', 'padding': '5px'}),
                        html.Td(next_hop, style={'border': '1px solid #ddd', 'padding': '5px'}),
                        html.Td(f"{cost:.2f}" if isinstance(cost, (int, float)) else str(cost), 
                                style={'border': '1px solid #ddd', 'padding': '5px'})
                    ]))
                
                table = html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Destination", style={'border': '1px solid #ddd', 'padding': '5px', 'backgroundColor': '#f2f2f2'}),
                            html.Th("Next Hop", style={'border': '1px solid #ddd', 'padding': '5px', 'backgroundColor': '#f2f2f2'}),
                            html.Th("Cost", style={'border': '1px solid #ddd', 'padding': '5px', 'backgroundColor': '#f2f2f2'})
                        ])
                    ]),
                    html.Tbody(rows)
                ], style={'borderCollapse': 'collapse', 'width': '100%', 'marginBottom': '15px'})
                
                tables.append(html.Div([
                    html.H5(f"Router {name}", style={'color': '#2980b9', 'marginBottom': '10px'}),
                    table
                ]))
            else:
                tables.append(html.Div([
                    html.H5(f"Router {name}", style={'color': '#2980b9'}),
                    html.P("No routes available", style={'fontStyle': 'italic', 'color': '#7f8c8d'})
                ]))
        
        return html.Div(tables)
    
    def get_live_packet_flow(self):
        """Generate live packet flow visualization"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return html.Div("No simulation running")
        
        # Collect recent packets from all routers
        all_packets = []
        for router in self.simulation.routers.values():
            if hasattr(router, 'packet_log'):
                all_packets.extend(router.packet_log[-10:])  # Last 10 packets per router
        
        # Sort by time (most recent first)
        all_packets.sort(key=lambda x: x['time'], reverse=True)
        
        packet_elements = []
        for packet in all_packets[:20]:  # Show last 20 packets
            direction_icon = "SENT" if packet['direction'] == 'sent' else "RECV"
            type_color = '#e74c3c' if packet['type'] == 'HELLO' else '#3498db'
            
            packet_elements.append(html.Div([
                html.Span(direction_icon, style={'marginRight': '5px'}),
                html.Span(f"{packet['time']:.2f}s", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                html.Span(f"{packet['router']}", style={'color': '#2980b9', 'marginRight': '5px'}),
                html.Span(f"{packet['direction']}", style={'marginRight': '5px'}),
                html.Span(f"{packet['type']}", style={'color': type_color, 'fontWeight': 'bold', 'marginRight': '5px'}),
                html.Span(f"to/from {packet.get('neighbor', 'unknown')}", style={'fontStyle': 'italic'})
            ], style={'margin': '5px 0', 'padding': '5px', 'backgroundColor': '#f8f9fa', 'borderRadius': '3px'}))
        
        if not packet_elements:
            packet_elements = [html.P("No packets exchanged yet...", style={'fontStyle': 'italic', 'color': '#7f8c8d'})]
        
        return html.Div(packet_elements)
    
    def get_protocol_statistics(self):
        """Generate protocol statistics graph"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return go.Figure().add_annotation(text="No data available", 
                                            xref="paper", yref="paper", x=0.5, y=0.5)
        
        # Collect statistics
        router_names = []
        hello_counts = []
        update_counts = []
        neighbor_counts = []
        route_counts = []
        
        for name, router in self.simulation.routers.items():
            router_names.append(name)
            
            # Count packet types
            hellos = updates = 0
            if hasattr(router, 'packet_log'):
                for packet in router.packet_log:
                    if packet['type'] == 'HELLO':
                        hellos += 1
                    elif packet['type'] == 'UPDATE':
                        updates += 1
            
            hello_counts.append(hellos)
            update_counts.append(updates)
            neighbor_counts.append(len(getattr(router, 'neighbor_table', {})))
            route_counts.append(len(getattr(router, 'fib', {})))
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(name='Hello Packets', x=router_names, y=hello_counts, marker_color='lightblue'))
        fig.add_trace(go.Bar(name='Update Packets', x=router_names, y=update_counts, marker_color='lightgreen'))
        fig.add_trace(go.Bar(name='Neighbors', x=router_names, y=neighbor_counts, marker_color='orange'))
        fig.add_trace(go.Bar(name='Routes', x=router_names, y=route_counts, marker_color='pink'))
        
        fig.update_layout(
            title='Protocol Statistics by Router',
            xaxis_title='Routers',
            yaxis_title='Count',
            barmode='group',
            showlegend=True
        )
        
        return fig
    
    def get_neighbor_tables_display(self):
        """Display neighbor tables with detailed metrics"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return html.Div("No simulation running")
        
        tables = []
        for name, router in self.simulation.routers.items():
            if hasattr(router, 'neighbor_table') and router.neighbor_table:
                rows = []
                for neighbor, data in router.neighbor_table.items():
                    metrics = data.get('metrics', {})
                    rows.append(html.Tr([
                        html.Td(neighbor),
                        html.Td(f"{data.get('last_seen', 0):.2f}s"),
                        html.Td(f"{metrics.get('delay', 0)}ms"),
                        html.Td(f"{metrics.get('jitter', 0)}ms"),
                        html.Td(f"{metrics.get('packet_loss', 0)}%"),
                        html.Td(f"{metrics.get('congestion', 0)}%")
                    ]))
                
                table = dash_table.DataTable(
                    columns=[
                        {'name': 'Neighbor', 'id': 'neighbor'},
                        {'name': 'Last Seen', 'id': 'last_seen'},
                        {'name': 'Delay', 'id': 'delay'},
                        {'name': 'Jitter', 'id': 'jitter'},
                        {'name': 'Loss', 'id': 'loss'},
                        {'name': 'Congestion', 'id': 'congestion'}
                    ],
                    data=[
                        {
                            'neighbor': neighbor,
                            'last_seen': f"{data.get('last_seen', 0):.2f}s",
                            'delay': f"{data.get('metrics', {}).get('delay', 0)}ms",
                            'jitter': f"{data.get('metrics', {}).get('jitter', 0)}ms",
                            'loss': f"{data.get('metrics', {}).get('packet_loss', 0)}%",
                            'congestion': f"{data.get('metrics', {}).get('congestion', 0)}%"
                        }
                        for neighbor, data in router.neighbor_table.items()
                    ],
                    style_cell={'textAlign': 'center'},
                    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                )
                
                tables.append(html.Div([
                    html.H5(f"Router {name} - Neighbor Table"),
                    table,
                    html.Br()
                ]))
        
        return html.Div(tables) if tables else html.P("No neighbor data available")
    
    def get_route_changes_display(self):
        """Display route changes over time"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return html.Div("No simulation running")
        
        all_changes = []
        for router in self.simulation.routers.values():
            if hasattr(router, 'route_changes'):
                all_changes.extend(router.route_changes)
        
        all_changes.sort(key=lambda x: x['time'], reverse=True)
        
        if not all_changes:
            return html.P("No route changes recorded yet")
        
        changes_data = [
            {
                'Time': f"{change['time']:.2f}s",
                'Router': change['router'],
                'Destination': change['destination'],
                'Old Route': change['old_route'],
                'New Route': change['new_route']
            }
            for change in all_changes[:20]  # Show last 20 changes
        ]
        
        return dash_table.DataTable(
            columns=[{'name': col, 'id': col} for col in changes_data[0].keys()] if changes_data else [],
            data=changes_data,
            style_cell={'textAlign': 'center'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ]
        )
    
    def get_metrics_analysis(self):
        """Display metrics analysis"""
        return html.Div([
            html.H4("Network Metrics Analysis"),
            html.P("This would show detailed analysis of network performance metrics like delay, jitter, packet loss, and congestion over time."),
            html.P("Implementation coming soon...")
        ])
    
    def get_dual_state_display(self):
        """Display DUAL algorithm state"""
        return html.Div([
            html.H4("DUAL Algorithm State"),
            html.P("This would show the internal state of the DUAL algorithm including feasible successors, feasible distances, and topology table."),
            html.P("Implementation coming soon...")
        ])
    
    def run(self, debug=True, port=8050):
        """Run the enhanced web application"""
        print(f"Starting Enhanced ADUP Web UI on http://localhost:{port}")
        print("Features:")
        print("  Dynamic network generation")
        print("  Real-time packet visualization")
        print("  Multi-metric routing display")
        print("  Advanced protocol monitoring")
        self.app.run(debug=debug, port=port)


# Enhanced Simulation class with configurable topology
class EnhancedSimulation:
    def __init__(self, network_config):
        self.env = simpy.Environment()
        self.routers = {}
        self.network_config = network_config
        
    def create_topology(self):
        """Create topology based on configuration"""
        num_routers = self.network_config.get('num_routers', 3)
        topology_type = self.network_config.get('topology_type', 'linear')
        
        # Create routers
        for i in range(num_routers):
            router_name = f"R{i+1}"
            network = f"192.168.{i+1}.0"
            
            # Determine number of interfaces based on topology
            if topology_type == 'linear':
                if i == 0 or i == num_routers - 1:
                    interfaces = {'eth0': {}}
                else:
                    interfaces = {'eth0': {}, 'eth1': {}}
            elif topology_type == 'star':
                if i == 0:  # Central router
                    interfaces = {f'eth{j}': {} for j in range(num_routers - 1)}
                else:
                    interfaces = {'eth0': {}}
            else:  # ring, mesh, or custom
                interfaces = {f'eth{j}': {} for j in range(min(num_routers - 1, 3))}
            
            router = Router(self.env, router_name, interfaces, networks=[network])
            self.routers[router_name] = router
        
        # Create links based on topology type
        from adup.simulation import Link
        
        if topology_type == 'linear':
            for i in range(num_routers - 1):
                r1 = self.routers[f"R{i+1}"]
                r2 = self.routers[f"R{i+2}"]
                link = Link(self.env, r1, r2)
                
                # Connect interfaces
                if i == 0:
                    r1.interfaces['eth0']['link'] = link
                    r2.interfaces['eth0']['link'] = link
                else:
                    r1.interfaces['eth1']['link'] = link
                    r2.interfaces['eth0']['link'] = link
        
        elif topology_type == 'ring':
            for i in range(num_routers):
                r1 = self.routers[f"R{i+1}"]
                r2 = self.routers[f"R{((i+1) % num_routers)+1}"]
                link = Link(self.env, r1, r2)
                
                r1.interfaces['eth0']['link'] = link
                r2.interfaces['eth1']['link'] = link if i < num_routers - 1 else link
        
        elif topology_type == 'star':
            central = self.routers['R1']
            for i in range(1, num_routers):
                edge_router = self.routers[f"R{i+1}"]
                link = Link(self.env, central, edge_router)
                
                central.interfaces[f'eth{i-1}']['link'] = link
                edge_router.interfaces['eth0']['link'] = link
        
        print(f"Enhanced topology created: {num_routers} routers in {topology_type} configuration")
    
    def run(self, until=60):
        print("Starting Enhanced ADUP simulation...")
        self.create_topology()
        self.env.run(until=until)
        print("Enhanced simulation finished.")


if __name__ == "__main__":
    ui = EnhancedADUPWebUI()
    ui.run()
