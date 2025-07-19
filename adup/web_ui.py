# Web-based UI for ADUP Protocol Simulation

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import threading
import time
from adup.simulation import Simulation
from adup.visualizer import NetworkVisualizer

class ADUPWebUI:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.simulation = None
        self.visualizer = None
        self.simulation_thread = None
        self.is_running = False
        self.setup_layout()
        self.setup_callbacks()
        
    def setup_layout(self):
        """Setup the web UI layout"""
        self.app.layout = html.Div([
            html.H1("ADUP Protocol Simulation Dashboard", 
                   style={'textAlign': 'center', 'color': '#2c3e50'}),
            
            html.Div([
                html.Div([
                    html.H3("Simulation Controls"),
                    html.Button('Start Simulation', id='start-btn', n_clicks=0,
                               style={'backgroundColor': '#27ae60', 'color': 'white', 
                                     'border': 'none', 'padding': '10px', 'margin': '5px'}),
                    html.Button('Stop Simulation', id='stop-btn', n_clicks=0,
                               style={'backgroundColor': '#e74c3c', 'color': 'white', 
                                     'border': 'none', 'padding': '10px', 'margin': '5px'}),
                    html.Button('Reset', id='reset-btn', n_clicks=0,
                               style={'backgroundColor': '#f39c12', 'color': 'white', 
                                     'border': 'none', 'padding': '10px', 'margin': '5px'}),
                    html.Div(id='simulation-status', style={'margin': '10px'}),
                ], className='four columns'),
                
                html.Div([
                    html.H3("Network Topology"),
                    dcc.Graph(id='network-graph'),
                ], className='eight columns'),
            ], className='row'),
            
            html.Div([
                html.Div([
                    html.H3("Routing Tables"),
                    html.Div(id='routing-tables'),
                ], className='six columns'),
                
                html.Div([
                    html.H3("Protocol Statistics"),
                    dcc.Graph(id='stats-graph'),
                ], className='six columns'),
            ], className='row'),
            
            html.Div([
                html.H3("Packet Flow Log"),
                html.Div(id='packet-log', 
                        style={'height': '300px', 'overflow': 'auto', 
                               'border': '1px solid #ddd', 'padding': '10px'}),
            ]),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=2*1000,  # Update every 2 seconds
                n_intervals=0
            )
        ])
    
    def setup_callbacks(self):
        """Setup dash callbacks for interactivity"""
        
        @self.app.callback(
            [Output('simulation-status', 'children'),
             Output('network-graph', 'figure'),
             Output('routing-tables', 'children'),
             Output('packet-log', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('start-btn', 'n_clicks'),
             Input('stop-btn', 'n_clicks'),
             Input('reset-btn', 'n_clicks')]
        )
        def update_dashboard(n_intervals, start_clicks, stop_clicks, reset_clicks):
            ctx = dash.callback_context
            
            if ctx.triggered:
                button_id = ctx.triggered[0]['prop_id'].split('.')[0]
                
                if button_id == 'start-btn' and not self.is_running:
                    self.start_simulation()
                elif button_id == 'stop-btn' and self.is_running:
                    self.stop_simulation()
                elif button_id == 'reset-btn':
                    self.reset_simulation()
            
            # Update all components
            status = self.get_simulation_status()
            network_fig = self.get_network_figure()
            routing_tables = self.get_routing_tables_display()
            packet_log = self.get_packet_log()
            
            return status, network_fig, routing_tables, packet_log
    
    def start_simulation(self):
        """Start the ADUP simulation in a separate thread"""
        if not self.is_running:
            self.simulation = Simulation()
            self.visualizer = NetworkVisualizer(self.simulation)
            
            def run_sim():
                self.is_running = True
                self.simulation.run(until=60)  # Run for 60 seconds
                self.is_running = False
            
            self.simulation_thread = threading.Thread(target=run_sim)
            self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop the current simulation"""
        self.is_running = False
        if hasattr(self.simulation, 'env'):
            # In a real implementation, we'd need a way to stop the simpy environment
            pass
    
    def reset_simulation(self):
        """Reset the simulation"""
        self.stop_simulation()
        self.simulation = None
        self.visualizer = None
    
    def get_simulation_status(self):
        """Get current simulation status"""
        if self.is_running:
            current_time = self.simulation.env.now if self.simulation else 0
            return html.Div([
                html.P(f"Status: Running", style={'color': 'green'}),
                html.P(f"Simulation Time: {current_time:.2f}s")
            ])
        else:
            return html.Div([
                html.P("Status: Stopped", style={'color': 'red'})
            ])
    
    def get_network_figure(self):
        """Generate network topology figure"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return go.Figure()
        
        # Create a simple network graph
        node_x = []
        node_y = []
        node_text = []
        
        # Position nodes in a line for simplicity
        positions = {'R1': (0, 0), 'R2': (1, 0), 'R3': (2, 0)}
        
        for name in self.simulation.routers.keys():
            if name in positions:
                x, y = positions[name]
                node_x.append(x)
                node_y.append(y)
                node_text.append(name)
        
        # Create edges
        edge_x = []
        edge_y = []
        
        # R1-R2 edge
        edge_x.extend([0, 1, None])
        edge_y.extend([0, 0, None])
        
        # R2-R3 edge
        edge_x.extend([1, 2, None])
        edge_y.extend([0, 0, None])
        
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=2, color='#888'),
                               hoverinfo='none',
                               mode='lines')
        
        node_trace = go.Scatter(x=node_x, y=node_y,
                               mode='markers+text',
                               hoverinfo='text',
                               text=node_text,
                               textposition="middle center",
                               marker=dict(size=50,
                                         color='lightblue',
                                         line=dict(width=2, color='darkblue')))
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                            title='Network Topology',
                            titlefont_size=16,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20,l=5,r=5,t=40),
                            annotations=[ dict(
                                text="ADUP Protocol Network",
                                showarrow=False,
                                xref="paper", yref="paper",
                                x=0.005, y=-0.002 ) ],
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        return fig
    
    def get_routing_tables_display(self):
        """Generate routing tables display"""
        if not self.simulation or not hasattr(self.simulation, 'routers'):
            return html.Div("No simulation running")
        
        tables = []
        for name, router in self.simulation.routers.items():
            if hasattr(router, 'fib') and router.fib:
                routes = []
                for dest, route_info in router.fib.items():
                    next_hop = route_info['next_hop']
                    cost = route_info['metrics']['total_delay']
                    routes.append(html.Li(f"{dest} → {next_hop} (cost: {cost})"))
                
                tables.append(html.Div([
                    html.H4(f"Router {name}"),
                    html.Ul(routes)
                ]))
            else:
                tables.append(html.Div([
                    html.H4(f"Router {name}"),
                    html.P("No routes")
                ]))
        
        return html.Div(tables)
    
    def get_packet_log(self):
        """Generate packet transmission log"""
        # This would be populated with actual packet events
        log_entries = [
            "10:30:15 - R1 → R2: Hello packet",
            "10:30:16 - R2 → R3: Hello packet", 
            "10:30:17 - R1 → R2: Update packet for 192.168.1.0",
            "10:30:18 - R3 → R2: Update packet for 192.168.3.0",
        ]
        
        return html.Div([html.P(entry) for entry in log_entries[-10:]])  # Show last 10 entries
    
    def run(self, debug=True, port=8050):
        """Run the web application"""
        print(f"Starting ADUP Web UI on http://localhost:{port}")
        self.app.run_server(debug=debug, port=port)

if __name__ == "__main__":
    ui = ADUPWebUI()
    ui.run()
