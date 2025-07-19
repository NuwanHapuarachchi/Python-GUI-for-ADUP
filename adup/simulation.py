# Network Simulation

import simpy
from adup.router import Router

class Link:
    """A simple communication link between two routers."""
    def __init__(self, env, router1, router2):
        self.env = env
        self.store = simpy.Store(env)
        self.router1 = router1
        self.router2 = router2
        self.env.process(self.run())

    def run(self):
        while True:
            sender, pkt = yield self.store.get()
            if sender == self.router1:
                print(f"{self.env.now}: Link transferring packet from {self.router1.name} to {self.router2.name}")
                yield self.router2.inbox.put((sender, pkt))
            else:
                print(f"{self.env.now}: Link transferring packet from {self.router2.name} to {self.router1.name}")
                yield self.router1.inbox.put((sender, pkt))

    def put(self, pkt):
        return self.store.put(pkt)

class Simulation:
    def __init__(self):
        self.env = simpy.Environment()
        self.routers = {}
        self.running = False

    def create_topology(self):
        """Creates a simple 3-router topology: R1 <-> R2 <-> R3"""
        # Create routers with directly connected networks
        r1 = Router(self.env, 'R1', {'eth0': {}}, networks=['192.168.1.0'])
        r2 = Router(self.env, 'R2', {'eth0': {}, 'eth1': {}}, networks=['192.168.2.0'])
        r3 = Router(self.env, 'R3', {'eth0': {}}, networks=['192.168.3.0'])
        
        self.routers = {'R1': r1, 'R2': r2, 'R3': r3}

        # Create links
        link1 = Link(self.env, r1, r2)
        link2 = Link(self.env, r2, r3)

        # Connect interfaces to links
        r1.interfaces['eth0']['link'] = link1
        r2.interfaces['eth0']['link'] = link1
        r2.interfaces['eth1']['link'] = link2
        r3.interfaces['eth0']['link'] = link2
        
        print("Topology created: R1 <-> R2 <-> R3")

    def create_linear_topology(self, node_count=5):
        """Create a linear topology with specified number of nodes"""
        self.routers = {}
        links = []
        
        # Create routers
        for i in range(node_count):
            router_name = f'R{i+1}'
            interfaces = {}
            networks = [f'192.168.{i+1}.0']
            
            # Determine number of interfaces
            if i == 0 or i == node_count - 1:  # End nodes
                interfaces = {'eth0': {}}
            else:  # Middle nodes
                interfaces = {'eth0': {}, 'eth1': {}}
            
            router = Router(self.env, router_name, interfaces, networks=networks)
            self.routers[router_name] = router
        
        # Create links between adjacent routers
        router_list = list(self.routers.values())
        for i in range(len(router_list) - 1):
            r1, r2 = router_list[i], router_list[i + 1]
            link = Link(self.env, r1, r2)
            links.append(link)
            
            # Connect interfaces
            if i == 0:  # First router
                r1.interfaces['eth0']['link'] = link
            else:
                r1.interfaces['eth1']['link'] = link
            
            r2.interfaces['eth0']['link'] = link
        
        print(f"Linear topology created with {node_count} routers")

    def create_ring_topology(self, node_count=5):
        """Create a ring topology with specified number of nodes"""
        self.routers = {}
        links = []
        
        # Create routers
        for i in range(node_count):
            router_name = f'R{i+1}'
            interfaces = {'eth0': {}, 'eth1': {}}
            networks = [f'192.168.{i+1}.0']
            
            router = Router(self.env, router_name, interfaces, networks=networks)
            self.routers[router_name] = router
        
        # Create links in a ring
        router_list = list(self.routers.values())
        for i in range(node_count):
            r1 = router_list[i]
            r2 = router_list[(i + 1) % node_count]  # Wrap around for ring
            
            link = Link(self.env, r1, r2)
            links.append(link)
            
            # Connect interfaces
            r1.interfaces['eth1']['link'] = link
            r2.interfaces['eth0']['link'] = link
        
        print(f"Ring topology created with {node_count} routers")

    def create_star_topology(self, node_count=5):
        """Create a star topology with specified number of nodes"""
        self.routers = {}
        links = []
        
        # Create central router
        central_interfaces = {f'eth{i}': {} for i in range(node_count - 1)}
        central_router = Router(self.env, 'R1', central_interfaces, networks=['192.168.1.0'])
        self.routers['R1'] = central_router
        
        # Create edge routers
        for i in range(1, node_count):
            router_name = f'R{i+1}'
            interfaces = {'eth0': {}}
            networks = [f'192.168.{i+1}.0']
            
            router = Router(self.env, router_name, interfaces, networks=networks)
            self.routers[router_name] = router
            
            # Create link to central router
            link = Link(self.env, central_router, router)
            links.append(link)
            
            # Connect interfaces
            central_router.interfaces[f'eth{i-1}']['link'] = link
            router.interfaces['eth0']['link'] = link
        
        print(f"Star topology created with {node_count} routers")

    def create_mesh_topology(self, node_count=4):
        """Create a full mesh topology with specified number of nodes"""
        if node_count > 6:
            node_count = 6  # Limit mesh size for performance
            
        self.routers = {}
        links = []
        
        # Create routers
        for i in range(node_count):
            router_name = f'R{i+1}'
            # Each router needs (node_count - 1) interfaces for full mesh
            interfaces = {f'eth{j}': {} for j in range(node_count - 1)}
            networks = [f'192.168.{i+1}.0']
            
            router = Router(self.env, router_name, interfaces, networks=networks)
            self.routers[router_name] = router
        
        # Create links between all pairs of routers
        router_list = list(self.routers.values())
        interface_counters = {router.name: 0 for router in router_list}
        
        for i in range(len(router_list)):
            for j in range(i + 1, len(router_list)):
                r1, r2 = router_list[i], router_list[j]
                link = Link(self.env, r1, r2)
                links.append(link)
                
                # Connect interfaces
                r1_iface = f'eth{interface_counters[r1.name]}'
                r2_iface = f'eth{interface_counters[r2.name]}'
                
                r1.interfaces[r1_iface]['link'] = link
                r2.interfaces[r2_iface]['link'] = link
                
                interface_counters[r1.name] += 1
                interface_counters[r2.name] += 1
        
        print(f"Mesh topology created with {node_count} routers")

    def create_custom_topology(self, node_count=5, connection_factor=0.3):
        """Create a custom topology with specified connection density (0.1 to 1.0)"""
        self.routers = {}
        links = []
        
        # Ensure reasonable parameters
        if node_count > 20:
            node_count = 20
        if connection_factor < 0.1:
            connection_factor = 0.1
        if connection_factor > 1.0:
            connection_factor = 1.0
            
        # Create routers with adequate interfaces
        max_possible_connections = node_count - 1  # Maximum connections per router
        target_connections_per_router = max(1, int(max_possible_connections * connection_factor))
        
        for i in range(node_count):
            router_name = f'R{i+1}'
            # Create enough interfaces for potential connections
            interfaces = {f'eth{j}': {} for j in range(max_possible_connections)}
            networks = [f'192.168.{i+1}.0']
            
            router = Router(self.env, router_name, interfaces, networks=networks)
            self.routers[router_name] = router
        
        # Calculate total possible connections in the network
        total_possible_connections = (node_count * (node_count - 1)) // 2
        target_total_connections = max(node_count - 1, int(total_possible_connections * connection_factor))
        
        print(f"Creating custom topology: {node_count} nodes, {connection_factor:.1%} density")
        print(f"Target connections: {target_total_connections} out of {total_possible_connections} possible")
        
        # Create connections
        router_list = list(self.routers.values())
        interface_counters = {router.name: 0 for router in router_list}
        created_links = set()
        
        import random
        random.seed(42)  # For reproducible layouts
        
        # Step 1: Ensure connectivity with minimum spanning tree approach
        connected_routers = {router_list[0].name}
        unconnected_routers = set(r.name for r in router_list[1:])
        
        while unconnected_routers:
            # Pick random connected router and random unconnected router
            connected_router_name = random.choice(list(connected_routers))
            unconnected_router_name = random.choice(list(unconnected_routers))
            
            connected_router = next(r for r in router_list if r.name == connected_router_name)
            unconnected_router = next(r for r in router_list if r.name == unconnected_router_name)
            
            # Create connection
            link = Link(self.env, connected_router, unconnected_router)
            links.append(link)
            created_links.add(tuple(sorted([connected_router.name, unconnected_router.name])))
            
            # Connect interfaces
            c_iface = f'eth{interface_counters[connected_router.name]}'
            u_iface = f'eth{interface_counters[unconnected_router.name]}'
            
            connected_router.interfaces[c_iface]['link'] = link
            unconnected_router.interfaces[u_iface]['link'] = link
            
            interface_counters[connected_router.name] += 1
            interface_counters[unconnected_router.name] += 1
            
            # Move router to connected set
            connected_routers.add(unconnected_router_name)
            unconnected_routers.remove(unconnected_router_name)
        
        # Step 2: Add additional random connections to reach target density
        connections_created = len(created_links)
        while connections_created < target_total_connections:
            # Try to find a valid random connection
            attempts = 0
            while attempts < 100:  # Prevent infinite loop
                r1 = random.choice(router_list)
                r2 = random.choice(router_list)
                
                if (r1 != r2 and 
                    interface_counters[r1.name] < len(r1.interfaces) and 
                    interface_counters[r2.name] < len(r2.interfaces)):
                    
                    link_id = tuple(sorted([r1.name, r2.name]))
                    if link_id not in created_links:
                        # Create the connection
                        link = Link(self.env, r1, r2)
                        links.append(link)
                        created_links.add(link_id)
                        
                        # Connect interfaces
                        r1_iface = f'eth{interface_counters[r1.name]}'
                        r2_iface = f'eth{interface_counters[r2.name]}'
                        
                        r1.interfaces[r1_iface]['link'] = link
                        r2.interfaces[r2_iface]['link'] = link
                        
                        interface_counters[r1.name] += 1
                        interface_counters[r2.name] += 1
                        connections_created += 1
                        break
                
                attempts += 1
            
            if attempts >= 100:
                break  # Can't find more valid connections
        
        print(f"Custom topology created: {node_count} routers, {len(links)} links ({len(links)/total_possible_connections:.1%} density)")

    def stop(self):
        """Stop the simulation"""
        self.running = False
        print("Simulation stopped")

    def reset(self):
        """Reset the simulation"""
        self.env = simpy.Environment()
        self.routers = {}
        self.running = False
        print("Simulation reset")

    def run(self, until=30, speed_multiplier=1.0):
        """Run the simulation with optional speed control"""
        print("Starting ADUP simulation...")
        if not self.routers:
            self.create_topology()
        
        self.running = True
        
        # Adjust simulation time based on speed multiplier
        actual_until = until / speed_multiplier if speed_multiplier > 0 else until
        
        try:
            self.env.run(until=actual_until)
        except simpy.Interrupt:
            print("Simulation interrupted")
        
        self.running = False
        print("Simulation finished.")
        
        # Print final results
        self._print_final_results()

    def _print_final_results(self):
        """Print final neighbor and routing tables"""
        # Print final neighbor tables
        for name, router in self.routers.items():
            print(f"\n--- {name} Neighbor Table ---")
            for neighbor, data in router.neighbor_table.items():
                print(f"  - {neighbor}: Last seen at {data['last_seen']:.2f}")
        
        # Print final routing tables (FIB)
        for name, router in self.routers.items():
            print(f"\n--- {name} Routing Table (FIB) ---")
            if hasattr(router, 'fib') and router.fib:
                for dest, route_info in router.fib.items():
                    next_hop = route_info['next_hop']
                    cost = route_info['metrics'].get('total_cost', route_info['metrics'].get('total_delay', 'N/A'))
                    print(f"  - {dest} via {next_hop} (cost: {cost})")
            else:
                print("  - No routes available")


if __name__ == "__main__":
    sim = Simulation()
    sim.run()
