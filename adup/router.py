# Router Implementation

import simpy
import random
import math
# Import only what we need from scapy to avoid libpcap warning
from scapy.packet import Packet
from adup.packets import ADUP_Hello, ADUP_Update, ADUP_Route_Entry, ADUP_Query, ADUP_Reply, ADUP_Ack

class Router:
    def __init__(self, env, name, interfaces, networks=None):
        self.env = env
        self.name = name
        self.interfaces = interfaces # e.g., {'eth0': {'neighbor': None, 'link': link_object}}
        self.routing_table = {} # {dest: {next_hop: metric_info}}
        self.neighbor_table = {} # {neighbor_name: {last_seen: time, metrics: {}}}
        self.networks = networks if networks else [] # Networks directly connected
        self.fib = {} # Forwarding Information Base (Successors)
        self.topology_table = {} # {dest: {neighbor: reported_cost}}
        
        # Initialize the inbox immediately
        self.inbox = simpy.Store(env)
        
        # Start the router processes
        self.action = env.process(self.run())
        
        # Multi-metric weights for composite cost calculation
        self.metric_weights = {
            'delay': 0.4,        # 40% weight
            'jitter': 0.2,       # 20% weight  
            'packet_loss': 0.25, # 25% weight
            'congestion': 0.15   # 15% weight
        }
        
        # Protocol state tracking
        self.state = 'INITIALIZING'
        self.packet_log = []  # For visualization
        self.route_changes = []  # Track routing changes

        # Dynamic metric variation for realistic path selection
        self.metric_variation = {
            'delay_base': 15,                # Increased base delay
            'jitter_base': 8,                # Increased base jitter
            'packet_loss_base': 0.005,       # Increased base: 0.5% instead of 0.2%
            'congestion_base': 0.08          # Increased congestion base to 8%
        }
        
        # Start dynamic metric updates
        self.env.process(self.update_dynamic_metrics())
        
        # Start cost monitoring and reset process
        self.env.process(self.monitor_and_reset_costs())
        
        # Start cost decay process to prevent long-term accumulation
        self.env.process(self.apply_cost_decay())

        # Convergence tracking
        self.convergence_start_time = None
        self.last_route_change_time = 0
        self.is_converged = False

    def calculate_composite_cost(self, metrics):
        """Calculate composite cost using weighted metrics"""
        try:
            cost = (
                self.metric_weights['delay'] * metrics.get('delay', 0) +
                self.metric_weights['jitter'] * metrics.get('jitter', 0) +
                self.metric_weights['packet_loss'] * metrics.get('packet_loss', 0) * 10 +  # Scale packet loss
                self.metric_weights['congestion'] * metrics.get('congestion', 0)
            )
            return cost
        except Exception as e:
            print(f"Error calculating composite cost: {e}")
            return float('inf')

    def log_packet(self, packet_type, direction, neighbor=None, details=None):
        """Log packet for advanced visualization"""
        log_entry = {
            'time': self.env.now,
            'router': self.name,
            'type': packet_type,
            'direction': direction,  # 'sent' or 'received'
            'neighbor': neighbor,
            'details': details,
            'routing_table_size': len(self.routing_table),
            'neighbor_count': len(self.neighbor_table),
            'path_selection_reason': self.get_path_selection_reason(neighbor),
            'composite_cost': self.calculate_neighbor_cost(neighbor) if neighbor else None
        }
        self.packet_log.append(log_entry)
        
        # Keep only last 100 entries for detailed analysis
        if len(self.packet_log) > 100:
            self.packet_log = self.packet_log[-100:]

    def get_path_selection_reason(self, neighbor):
        """Determine why this neighbor was selected for packet transmission"""
        if not neighbor or neighbor not in self.neighbor_table:
            return "Unknown"
            
        neighbor_metrics = self.neighbor_table[neighbor].get('metrics', {})
        cost = self.calculate_composite_cost(neighbor_metrics)
        
        # Compare with other neighbors
        best_cost = float('inf')
        for other_neighbor, info in self.neighbor_table.items():
            other_cost = self.calculate_composite_cost(info.get('metrics', {}))
            if other_cost < best_cost:
                best_cost = other_cost
                
        if cost == best_cost:
            return "Best path (lowest composite cost)"
        elif cost < best_cost * 1.1:
            return "Load balancing"
        else:
            return "Backup path"

    def calculate_neighbor_cost(self, neighbor):
        """Calculate composite cost to a specific neighbor"""
        if not neighbor or neighbor not in self.neighbor_table:
            return float('inf')
            
        metrics = self.neighbor_table[neighbor].get('metrics', {})
        return self.calculate_composite_cost(metrics)

    def log_route_change(self, destination, old_route, new_route, path_info=None):
        """Log routing table changes with detailed analysis"""
        change_entry = {
            'time': self.env.now,
            'router': self.name,
            'destination': destination,
            'old_route': old_route,
            'new_route': new_route,
            'path_info': path_info,
            'change_type': self.classify_route_change(old_route, new_route, path_info)
        }
        self.route_changes.append(change_entry)
        
        if len(self.route_changes) > 50:
            self.route_changes = self.route_changes[-50:]

    def classify_route_change(self, old_route, new_route, path_info):
        """Classify the type of route change"""
        if old_route == 'None':
            return "New route discovered"
        elif new_route == 'None':
            return "Route lost"
        elif old_route != new_route:
            if path_info and path_info.get('total_cost', 0) < 50:
                return "Better path found"
            else:
                return "Path switched due to failure"
        else:
            return "Route updated"

    def run(self):
        # Start all the router processes
        print(f"{self.env.now}: {self.name} starting up...")
        
        # Start processes in order
        self.env.process(self.listen())
        yield self.env.timeout(1)  # Brief delay
        
        self.env.process(self.send_hellos())
        yield self.env.timeout(1)  # Brief delay
        
        # Announce directly connected networks after a brief delay
        self.env.process(self.initial_advertisement())
        
        # Keep running
        while True:
            yield self.env.timeout(60)  # Check every minute

    def initial_advertisement(self):
        """Announce directly connected networks at startup"""
        yield self.env.timeout(random.uniform(1, 3))  # Stagger initial updates
        self.state = 'ADVERTISING'
        print(f"{self.env.now}: {self.name} performing initial advertisement")
        self.trigger_update()  # Advertise all directly connected networks
        self.state = 'ACTIVE'

    def send_hellos(self):
        # Send initial Hello packets immediately
        yield self.env.timeout(random.uniform(0.5, 2.0))  # Stagger initial hellos
        
        while True:
            try:
                for iface_name, iface_info in self.interfaces.items():
                    link = iface_info.get('link')
                    if link:
                        # Simulate realistic network conditions with dynamic variation
                        # Create time-based and network condition factors with more variation
                        time_factor = 1 + 0.6 * math.sin(self.env.now / 15) + 0.3 * math.cos(self.env.now / 10)
                        network_load = random.uniform(0.5, 2.0)
                        congestion_spike = random.uniform(0.8, 1.5) if random.random() > 0.7 else 1.0
                        
                        # Generate more realistic and varied packet loss
                        base_loss = random.uniform(0.1, 2.5)  # Base loss 0.1-2.5%
                        dynamic_loss = base_loss * abs(time_factor) * network_load * congestion_spike
                        # Add occasional packet loss spikes (simulating network congestion)
                        if random.random() > 0.85:  # 15% chance of spike
                            dynamic_loss += random.uniform(1.0, 4.0)
                        
                        hello_pkt = ADUP_Hello(
                            delay=max(5, min(120, int(random.randint(10, 80) * time_factor))),
                            jitter=max(1, min(20, int(random.randint(2, 15) * network_load))),
                            packet_loss=max(0.05, min(8.0, dynamic_loss)),  # 0.05-8% packet loss with spikes
                            congestion=max(0, min(50, int(random.randint(5, 35) * network_load))),    # 0-50% congestion
                            link_stability=max(70, min(100, int(random.randint(80, 98) / time_factor))) # 70-100% stability
                        )
                        
                        # Determine the neighbor router name
                        neighbor_name = None
                        if link.router1.name == self.name:
                            neighbor_name = link.router2.name
                        else:
                            neighbor_name = link.router1.name
                        
                        # Log the packet for visualization
                        self.log_packet('HELLO', 'sent', neighbor=neighbor_name,
                                      details={'delay': hello_pkt.delay, 'jitter': hello_pkt.jitter})
                        
                        print(f"{self.env.now}: {self.name} sending Hello to {neighbor_name} on {iface_name} (delay:{hello_pkt.delay}ms, jitter:{hello_pkt.jitter}ms, loss:{hello_pkt.packet_loss:.3f}%)")
                        yield self.env.process(self._send_packet_on_link(link, hello_pkt))
                    else:
                        print(f"{self.env.now}: {self.name} interface {iface_name} has no link configured")

                yield self.env.timeout(5) # Send hellos every 5 seconds
            except Exception as e:
                print(f"Error in send_hellos for {self.name}: {e}")
                yield self.env.timeout(2)  # Wait before retrying

    def listen(self):
        # Listen for incoming packets using the inbox that was created in __init__
        print(f"{self.env.now}: {self.name} starting to listen for packets")
        while True:
            try:
                print(f"{self.env.now}: {self.name} waiting for packet...")
                sender, pkt = yield self.inbox.get()
                print(f"{self.env.now}: {self.name} got packet from inbox")
                self.handle_packet(sender, pkt)
            except Exception as e:
                print(f"Error in listen method for {self.name}: {e}")
                yield self.env.timeout(1)  # Brief pause before continuing

    def handle_packet(self, sender, pkt):
        try:
            print(f"{self.env.now}: {self.name} received packet from {sender.name} - Type: {type(pkt).__name__}")
            
            if pkt.haslayer(ADUP_Hello):
                neighbor_name = sender.name
                now = self.env.now
                
                # Update neighbor table
                self.neighbor_table[neighbor_name] = {
                    'last_seen': now,
                    'metrics': {
                        'delay': pkt[ADUP_Hello].delay,
                        'jitter': pkt[ADUP_Hello].jitter,
                        'packet_loss': pkt[ADUP_Hello].packet_loss,
                        'congestion': pkt[ADUP_Hello].congestion,
                        'link_stability': pkt[ADUP_Hello].link_stability,
                    }
                }
                
                # Log the received packet
                self.log_packet('HELLO', 'received', neighbor_name, 
                              {'delay': pkt[ADUP_Hello].delay, 'jitter': pkt[ADUP_Hello].jitter})
                
                print(f"{now}: {self.name} received Hello from {neighbor_name} (delay:{pkt[ADUP_Hello].delay}ms, loss:{pkt[ADUP_Hello].packet_loss:.3f}%)")
                # Prune old neighbors (e.g., if not seen for 15 seconds)
                self.prune_neighbors()
            elif pkt.haslayer(ADUP_Update):
                print(f"{self.env.now}: {self.name} received Update packet from {sender.name}")
                self.handle_update(sender, pkt)
            else:
                print(f"{self.env.now}: {self.name} received unknown packet type from {sender.name}")
        except Exception as e:
            print(f"Error handling packet in {self.name}: {e}")
            import traceback
            traceback.print_exc()

    def handle_update(self, sender, update_pkt):
        try:
            neighbor_name = sender.name
            if neighbor_name not in self.neighbor_table:
                return # Ignore updates from unknown neighbors

            print(f"{self.env.now}: {self.name} received Update from {neighbor_name}")

            for route in update_pkt.routes:
                dest = route.dest_network
                reported_cost = route.total_delay
                
                # CRITICAL FIX: Prevent routing loops and cost accumulation
                # Don't process updates about networks we advertise to this neighbor
                if (dest in self.fib and 
                    self.fib[dest].get('next_hop') == neighbor_name):
                    print(f"  Ignoring update for {dest} from {neighbor_name} (split horizon)")
                    continue
                
                # ENHANCED FIX: Much stricter cost limits to prevent accumulation
                # Ignore any cost over 100 (reasonable for most networks)
                if reported_cost > 100:
                    print(f"  Ignoring excessive cost {reported_cost} for {dest} from {neighbor_name}")
                    continue
                
                # ADDITIONAL FIX: Prevent rapid cost increases
                if dest in self.topology_table and neighbor_name in self.topology_table[dest]:
                    old_cost = self.topology_table[dest][neighbor_name]
                    # Don't allow cost to more than double in one update
                    if reported_cost > old_cost * 2.0:
                        capped_cost = min(old_cost * 1.5, 80)  # Cap at 50% increase or 80, whichever is lower
                        print(f"  Capping rapid cost increase for {dest} from {neighbor_name}: {reported_cost} -> {capped_cost}")
                        reported_cost = capped_cost

                # Update topology table with potentially capped cost
                if dest not in self.topology_table:
                    self.topology_table[dest] = {}
                self.topology_table[dest][neighbor_name] = reported_cost

                # Recalculate best path for the destination
                self.recalculate_dual(dest)
        except Exception as e:
            print(f"Error handling update in {self.name}: {e}")

    def recalculate_dual(self, dest):
        try:
            # Enhanced DUAL using advanced path selection
            best_neighbor, path_info = self.advanced_path_selection(dest)
            
            if best_neighbor is None:
                return
                
            # Check if the new best path is different from the current one
            current_route = self.fib.get(dest, {})
            current_next_hop = current_route.get('next_hop', 'None')
            current_cost = current_route.get('metrics', {}).get('total_cost', float('inf'))
            
            new_cost = path_info['total_cost']
            
            # Update path usage tracking
            if not hasattr(self, 'path_usage'):
                self.path_usage = {}
            path_key = f"{best_neighbor}->{dest}"
            self.path_usage[path_key] = self.path_usage.get(path_key, 0) + 1
            
            # Only update if there's a significant improvement or change
            if current_next_hop != best_neighbor or abs(new_cost - current_cost) > 0.1:
                old_route = current_next_hop
                
                # Track route changes for convergence
                self.last_route_change_time = self.env.now
                if self.convergence_start_time is None:
                    self.convergence_start_time = self.env.now
                
                print(f"{self.env.now}: {self.name} selected path for {dest} via {best_neighbor}")
                print(f"  Reason: {path_info['selection_reason']}")
                print(f"  Cost: {new_cost:.2f}, Stability: {path_info['stability']}")
                print(f"  Congestion: {path_info['congestion']:.1f}%, Loss: {path_info['packet_loss']:.1f}%")
                
                self.fib[dest] = {
                    'next_hop': best_neighbor,
                    'metrics': {
                        'total_cost': new_cost,
                        'stability': path_info['stability'],
                        'congestion': path_info['congestion'],
                        'packet_loss': path_info['packet_loss'],
                        'selection_reason': path_info['selection_reason']
                    }
                }
                
                # Log the route change with detailed information
                self.log_route_change(dest, old_route, best_neighbor, path_info)
                
                # Trigger an update to our neighbors about this new path
                self.trigger_update(dest)
                
        except Exception as e:
            print(f"Error in enhanced DUAL calculation for {self.name}: {e}")

    def trigger_update(self, dest=None):
        try:
            if dest:
                # Send update for a specific destination
                self.env.process(self._send_update_proc(dest))
            else:
                # Send updates for all self-connected networks
                for net in self.networks:
                     # CRITICAL FIX: Directly connected networks have ZERO cost
                    self.fib[net] = {
                        'next_hop': 'self', 
                        'metrics': {
                            'total_delay': 0,  # Zero cost for directly connected
                            'total_cost': 0    # Zero cost for directly connected
                        }
                    }
                    self.env.process(self._send_update_proc(net))
        except Exception as e:
            print(f"Error triggering update in {self.name}: {e}")

    def _send_update_proc(self, destination):
        # Stagger the update slightly to avoid packet storms
        yield self.env.timeout(random.uniform(0.1, 0.5))
        self.send_update(destination)

    def send_update(self, destination):
        """Send update packet - this will be called from a generator process"""
        try:
            # In a full DUAL implementation, updates are more targeted.
            # For now, we broadcast our best route to a destination to all neighbors.
            if destination not in self.fib:
                return # No route to advertise

            best_route_info = self.fib[destination]
            
            # Get the cost from either new or old format
            total_cost = best_route_info['metrics'].get('total_cost', 
                        best_route_info['metrics'].get('total_delay', 0))
            
            # ENHANCED FIX: Don't advertise excessively high costs
            # This prevents propagating accumulated costs to neighbors
            if total_cost > 70:  # Don't advertise routes with very high costs
                print(f"{self.env.now}: {self.name} suppressing high-cost update for {destination} (cost: {total_cost})")
                return
            
            route_entry = ADUP_Route_Entry(
                prefix_len=24, # Assuming /24 for simplicity
                dest_network=destination,
                total_delay=int(total_cost),  # Convert to int for packet
                total_bandwidth=100000,  # Default values
                total_jitter=0,
                total_packet_loss=0,
                total_congestion=0
            )
            
            update_pkt = ADUP_Update(routes=[route_entry])

            # Start a process to send the update on all interfaces
            self.env.process(self._send_update_on_all_interfaces(update_pkt, destination))
            
        except Exception as e:
            print(f"Error sending update from {self.name}: {e}")
            
    def _send_update_on_all_interfaces(self, update_pkt, destination):
        """Helper to send update packet on all interfaces with proper yielding"""
        for iface_name, iface_info in self.interfaces.items():
            if iface_info.get('link'):
                print(f"{self.env.now}: {self.name} sending Update for {destination} on {iface_name}")
                yield self.env.process(self._send_packet_on_link(iface_info['link'], update_pkt))

    def prune_neighbors(self):
        now = self.env.now
        dead_neighbors = [
            name for name, data in self.neighbor_table.items()
            if now - data['last_seen'] > 15
        ]
        for name in dead_neighbors:
            print(f"{now}: {self.name} timing out neighbor {name}")
            del self.neighbor_table[name]

    def advanced_path_selection(self, dest):
        """Advanced path selection using multiple criteria and machine learning concepts"""
        try:
            candidates = []
            
            # Collect all possible paths to destination
            if dest in self.topology_table:
                for neighbor, reported_cost in self.topology_table[dest].items():
                    if neighbor in self.neighbor_table:
                        neighbor_metrics = self.neighbor_table[neighbor]['metrics']
                        
                        # Calculate link cost to this neighbor
                        link_cost = self.calculate_composite_cost(neighbor_metrics)
                        
                        # ENHANCED FIX: More conservative cost calculation to prevent accumulation
                        # Total cost = link cost + neighbor's cost to destination
                        total_cost = link_cost + reported_cost
                        
                        # ENHANCED: Check for cost loops before accepting the cost
                        if self.detect_cost_loop(dest, neighbor, total_cost):
                            print(f"  {self.name}: Rejecting cost {total_cost} for {dest} via {neighbor} due to suspected loop")
                            continue  # Skip this candidate
                        
                        # CRITICAL: Apply aggressive cost ceiling to prevent runaway costs
                        total_cost = min(total_cost, 80)  # Much lower maximum cost (was 500)
                        
                        # ENHANCED: Apply exponential damping for high costs
                        if total_cost > 50:
                            # Apply exponential damping to high costs
                            damping_factor = 0.7  # Reduce high costs by 30%
                            total_cost = 50 + (total_cost - 50) * damping_factor
                        
                        # Apply cost stabilization to prevent oscillation
                        total_cost = self.stabilize_cost(dest, neighbor, total_cost)
                        
                        # Advanced metrics for path selection
                        stability_score = self.calculate_link_stability(neighbor)
                        congestion_level = neighbor_metrics.get('congestion', 0)
                        packet_loss_rate = neighbor_metrics.get('packet_loss', 0)
                        
                        # Multi-Armed Bandit inspired selection
                        exploration_bonus = self.calculate_exploration_bonus(neighbor, dest)
                        
                        # Combined score for path selection
                        combined_score = (
                            total_cost * 0.6 +  # Primary cost (increased weight)
                            (100 - stability_score) * 0.15 +  # Stability (lower is better)
                            congestion_level * 0.1 +  # Congestion
                            packet_loss_rate * 10 * 0.1 +  # Packet loss (scaled)
                            exploration_bonus * 0.05  # Exploration
                        )
                        
                        candidates.append({
                            'neighbor': neighbor,
                            'total_cost': total_cost,
                            'combined_score': combined_score,
                            'stability': stability_score,
                            'congestion': congestion_level,
                            'packet_loss': packet_loss_rate,
                            'exploration_bonus': exploration_bonus,
                            'selection_reason': self.determine_selection_reason(
                                total_cost, stability_score, congestion_level, packet_loss_rate
                            )
                        })
            
            if not candidates:
                return None, None
                
            # Sort by combined score (lower is better)
            candidates.sort(key=lambda x: x['combined_score'])
            
            # Log path selection analysis
            self.log_path_analysis(dest, candidates)
            
            return candidates[0]['neighbor'], candidates[0]
            
        except Exception as e:
            print(f"Error in advanced path selection for {self.name}: {e}")
            return None, None

    def calculate_link_stability(self, neighbor):
        """Calculate link stability based on historical metrics"""
        if neighbor not in self.neighbor_table:
            return 0
            
        # Simulate stability calculation based on neighbor history
        last_seen = self.neighbor_table[neighbor].get('last_seen', 0)
        time_since_contact = self.env.now - last_seen
        
        # Stability decreases with time since last contact
        if time_since_contact < 20:  # 20 seconds (hello interval)
            return 100  # Very stable
        elif time_since_contact < 40:  # 2x hello interval
            return 75   # Good stability
        elif time_since_contact < 80:  # 4x hello interval
            return 50   # Fair stability
        else:
            return 25   # Poor stability

    def calculate_exploration_bonus(self, neighbor, dest):
        """Calculate exploration bonus for multi-armed bandit style path selection"""
        # Encourage exploration of less-used paths
        path_key = f"{neighbor}->{dest}"
        
        # Simulate usage tracking
        if not hasattr(self, 'path_usage'):
            self.path_usage = {}
            
        usage_count = self.path_usage.get(path_key, 0)
        
        # Higher bonus for less-used paths (exploration)
        if usage_count == 0:
            return 10  # High exploration bonus
        elif usage_count < 3:
            return 5   # Medium bonus
        elif usage_count < 10:
            return 2   # Low bonus
        else:
            return 0   # No bonus for heavily used paths

    def determine_selection_reason(self, total_cost, stability, congestion, packet_loss):
        """Determine the primary reason for path selection"""
        if total_cost < 50 and stability > 80:
            return "Optimal path (low cost, high stability)"
        elif congestion < 20:
            return "Low congestion path"
        elif packet_loss < 2:
            return "Low packet loss path"
        elif stability > 90:
            return "High stability path"
        else:
            return "Best available path"

    def log_path_analysis(self, dest, candidates):
        """Log detailed path analysis for visualization"""
        analysis_entry = {
            'time': self.env.now,
            'router': self.name,
            'destination': dest,
            'candidates': candidates,
            'selection_criteria': 'multi-metric-with-exploration',
            'total_candidates': len(candidates)
        }
        
        if not hasattr(self, 'path_analysis_log'):
            self.path_analysis_log = []
            
        self.path_analysis_log.append(analysis_entry)
        
        # Keep only recent analysis
        if len(self.path_analysis_log) > 50:
            self.path_analysis_log = self.path_analysis_log[-50:]

    def stabilize_cost(self, dest, neighbor, new_cost):
        """Stabilize cost to prevent rapid oscillations and accumulation"""
        # Initialize cost history if not exists
        if not hasattr(self, 'cost_history'):
            self.cost_history = {}
        
        cost_key = f"{dest}-{neighbor}"
        
        if cost_key not in self.cost_history:
            self.cost_history[cost_key] = []
        
        # Keep only recent history (last 5 calculations)
        history = self.cost_history[cost_key]
        history.append(new_cost)
        if len(history) > 5:
            history.pop(0)
        
        # If we have enough history, apply smoothing
        if len(history) >= 3:
            # Use exponential moving average for stability
            alpha = 0.5  # Increased smoothing factor for more stability
            smoothed_cost = history[-1]
            for i in range(len(history) - 2, -1, -1):
                smoothed_cost = alpha * history[i] + (1 - alpha) * smoothed_cost
            
            # CRITICAL FIX: Prevent dramatic increases (limit to 20% increase per update)
            if len(history) > 1:
                prev_cost = history[-2]
                max_increase = prev_cost * 1.2  # Only 20% increase allowed
                if smoothed_cost > max_increase:
                    smoothed_cost = max_increase
                    print(f"  {self.name}: Cost increase capped for {dest} via {neighbor}: {new_cost:.1f} -> {smoothed_cost:.1f}")
            
            # ENHANCED FIX: Much lower absolute maximum cost ceiling
            smoothed_cost = min(smoothed_cost, 80)  # Reduced from 200 to 80
            
            return smoothed_cost
        else:
            # For new paths, apply conservative maximum ceiling
            return min(new_cost, 60)  # Even lower for new paths

    def detect_cost_loop(self, dest, neighbor, new_cost):
        """Detect potential cost loops and prevent them"""
        try:
            # Initialize loop detection history
            if not hasattr(self, 'loop_detection'):
                self.loop_detection = {}
            
            key = f"{dest}-{neighbor}"
            if key not in self.loop_detection:
                self.loop_detection[key] = []
            
            # Keep track of recent costs
            history = self.loop_detection[key]
            history.append((self.env.now, new_cost))
            
            # Keep only recent history (last 10 updates)
            if len(history) > 10:
                history.pop(0)
            
            # Check for rapid cost oscillations (sign of a loop)
            if len(history) >= 5:
                recent_costs = [cost for _, cost in history[-5:]]
                cost_variance = max(recent_costs) - min(recent_costs)
                
                # If costs are varying wildly, suspect a loop
                if cost_variance > 30:
                    print(f"{self.env.now}: {self.name} detected cost oscillation for {dest} via {neighbor}")
                    print(f"  Recent costs: {recent_costs}")
                    return True  # Loop detected
            
            # Check for consistent cost increases (accumulation)
            if len(history) >= 4:
                increases = 0
                for i in range(1, len(history)):
                    if history[i][1] > history[i-1][1]:
                        increases += 1
                
                # If costs are consistently increasing, suspect accumulation
                if increases >= 3:
                    print(f"{self.env.now}: {self.name} detected cost accumulation for {dest} via {neighbor}")
                    return True  # Accumulation detected
            
            return False  # No loop detected
            
        except Exception as e:
            print(f"Error in loop detection for {self.name}: {e}")
            return False

    def apply_cost_decay(self):
        """Apply cost decay to prevent long-term accumulation and encourage route optimization"""
        while True:
            try:
                # Wait for decay interval
                yield self.env.timeout(120)  # Apply decay every 2 minutes
                
                # Apply decay to all non-directly-connected routes
                decay_factor = 0.95  # Reduce costs by 5% each cycle
                routes_updated = False
                
                for dest, route_info in list(self.fib.items()):
                    if route_info.get('next_hop') != 'self':  # Only decay learned routes
                        current_cost = route_info['metrics'].get('total_cost', 0)
                        if current_cost > 10:  # Only decay significant costs
                            decayed_cost = current_cost * decay_factor
                            route_info['metrics']['total_cost'] = decayed_cost
                            routes_updated = True
                            
                            # Also decay in topology table
                            if dest in self.topology_table:
                                for neighbor in self.topology_table[dest]:
                                    if self.topology_table[dest][neighbor] > 10:
                                        self.topology_table[dest][neighbor] *= decay_factor
                
                # If we updated routes, trigger recalculation
                if routes_updated:
                    print(f"{self.env.now}: {self.name} applied cost decay to prevent accumulation")
                    # Trigger updates for modified routes
                    for dest in self.fib.keys():
                        if self.fib[dest].get('next_hop') != 'self':
                            self.env.process(self._send_update_proc(dest))
                
            except Exception as e:
                print(f"Error in cost decay for {self.name}: {e}")
                yield self.env.timeout(30)

    def update_dynamic_metrics(self):
        """Continuously update link metrics to simulate real network conditions"""
        while True:
            try:
                # Update metrics for each neighbor
                for neighbor_name, neighbor_info in self.neighbor_table.items():
                    if 'metrics' not in neighbor_info:
                        neighbor_info['metrics'] = {}
                    
                    # Generate dynamic metrics with realistic variation and bounds
                    base_delay = self.metric_variation['delay_base']
                    base_jitter = self.metric_variation['jitter_base']
                    base_loss = self.metric_variation['packet_loss_base']
                    base_congestion = self.metric_variation['congestion_base']
                    
                    # Add time-based and random variation (more significant for packet loss)
                    time_factor = 1 + 0.4 * math.sin(self.env.now / 25) + 0.2 * math.cos(self.env.now / 18)  # More complex variation
                    random_factor = random.uniform(0.3, 2.5)  # Much wider variation (70% reduction to 150% increase)
                    congestion_factor = random.uniform(0.8, 2.0)  # Congestion can double packet loss
                    
                    # Add occasional network events (spikes in packet loss)
                    spike_factor = 1.0
                    if random.random() > 0.9:  # 10% chance of network event
                        spike_factor = random.uniform(2.0, 5.0)  # 2x to 5x packet loss spike
                    
                    # Update metrics with proper bounds to prevent accumulation
                    new_delay = max(1, min(80, base_delay * abs(time_factor) * random_factor))
                    new_jitter = max(0.1, min(15, base_jitter * random_factor))
                    # More realistic packet loss: 0.01% to 8% with occasional spikes
                    new_loss_raw = base_loss * 100 * abs(time_factor) * random_factor * congestion_factor * spike_factor  # Convert to percentage
                    new_loss = max(0.01, min(8.0, new_loss_raw))  # 0.01% to 8%
                    new_congestion = max(0, min(50, base_congestion * 100 * abs(time_factor) * random_factor))  # Max 50%
                    
                    neighbor_info['metrics'].update({
                        'delay': new_delay,
                        'jitter': new_jitter,
                        'packet_loss': new_loss,  # This is now in percentage (0.01% to 8%)
                        'congestion': new_congestion,
                        'link_stability': max(50, min(100, 100 - abs(time_factor - 1) * 30)),
                        'bandwidth_utilization': max(10, min(90, 50 * abs(time_factor) * random_factor))
                    })
                
                # Wait before next update (longer intervals for more stability)
                yield self.env.timeout(random.uniform(20, 40))
                
            except Exception as e:
                print(f"Error in dynamic metrics update for {self.name}: {e}")
                yield self.env.timeout(10)

    def monitor_and_reset_costs(self):
        """Monitor routing costs and reset if they become unreasonable"""
        while True:
            try:
                # Wait for monitoring interval (more frequent monitoring)
                yield self.env.timeout(30)  # Check every 30 seconds (was 60)
                
                # Check all FIB entries for unreasonable costs
                reset_needed = False
                for dest, route_info in list(self.fib.items()):
                    if route_info.get('next_hop') != 'self':  # Don't reset directly connected
                        total_cost = route_info['metrics'].get('total_cost', 0)
                        if total_cost > 60:  # Much lower reset threshold (was 150)
                            print(f"{self.env.now}: {self.name} resetting high cost {total_cost} for {dest}")
                            reset_needed = True
                            
                            # Remove from FIB and topology table to force recalculation
                            del self.fib[dest]
                            if dest in self.topology_table:
                                del self.topology_table[dest]
                
                # Reset cost history if needed
                if reset_needed:
                    if hasattr(self, 'cost_history'):
                        self.cost_history.clear()
                    print(f"{self.env.now}: {self.name} cleared cost history due to high costs")
                    
                    # Re-trigger updates for directly connected networks
                    self.trigger_update()
                    
            except Exception as e:
                print(f"Error in cost monitoring for {self.name}: {e}")
                yield self.env.timeout(10)

    def _send_packet_on_link(self, link, packet):
        """Helper method to send packet on link with proper yielding"""
        try:
            print(f"{self.env.now}: {self.name} putting packet on link")
            yield link.put((self, packet))
        except Exception as e:
            print(f"Error sending packet on link from {self.name}: {e}")
