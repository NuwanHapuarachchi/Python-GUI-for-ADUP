#!/usr/bin/env python3
"""
ADUP Protocol Implementation - Main Entry Point

This is the main entry point for the Advanced Diffusing Update Protocol (ADUP) implementation.
You can run the simulation in different modes:

1. Command-line simulation: python main.py --mode simulation
2. Web UI: python main.py --mode web
3. Visualization: python main.py --mode visualize

"""

import argparse
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adup.simulation import Simulation
from adup.visualizer import NetworkVisualizer
# Temporarily comment out web UI imports to test simulation
# from adup.web_ui import ADUPWebUI
# from adup.enhanced_web_ui import EnhancedADUPWebUI

def run_simulation():
    """Run the command-line simulation"""
    print("=" * 60)
    print("ADVANCED DIFFUSING UPDATE PROTOCOL (ADUP) SIMULATION")
    print("=" * 60)
    
    sim = Simulation()
    sim.run(until=60)  # Run for 60 seconds
    
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETED")
    print("=" * 60)

def run_visualization():
    """Run the matplotlib visualization"""
    print("Starting ADUP Network Visualization...")
    
    sim = Simulation()
    visualizer = NetworkVisualizer(sim)
    
    # Show static topology first
    visualizer.show_static_topology()
    
    # Then show animated version
    try:
        import matplotlib.pyplot as plt
        ani = visualizer.animate_network(interval=1000)
        plt.show()
    except KeyboardInterrupt:
        print("Visualization stopped by user.")

def run_web_ui():
    """Run the enhanced web-based UI"""
    ui = EnhancedADUPWebUI()
    ui.run(debug=False, port=8050)

def main():
    parser = argparse.ArgumentParser(
        description="ADUP Protocol Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode simulation    # Run command-line simulation
  python main.py --mode web          # Start web UI
  python main.py --mode visualize    # Show network visualization
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['simulation', 'web', 'visualize'],
        default='simulation',
        help='Mode to run the application in (default: simulation)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Simulation duration in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8050,
        help='Port for web UI (default: 8050)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'simulation':
            run_simulation()
        elif args.mode == 'web':
            run_web_ui()
        elif args.mode == 'visualize':
            run_visualization()
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
