import queue
import multiprocessing
import itertools
import sys

__all__ = ["QConnect", "CConnect"]

pulse_length_default = 10 * 10 ** -12 # 10 ps photon pulse length
signal_speed = 2.998 * 10 ** 5 #speed of light in km/s
fiber_length_default = 0.0

class QConnect: 
    def __init__(self, *args, transit_devices=[]):
        '''
        This is the base class for a quantum connection between multiple agents. 

        :param agents \*args: list of agents to connect
        :param List<Devices> transit_devices: list of devices qubits travel through 
        '''
        agents = list(args)
        self.agents = {}
        self.source_devices = {}
        self.target_devices = {}
        self.transit_devices = {}

        '''
        Create queue to keep track of multiple requests. Name of queue is name of
        target agent.  
        '''
        self.queues = {}
        for agent in agents:
            self.agents.update({agent.name: agent})
            self.source_devices.update({agent.name: agent.source_devices})
            self.target_devices.update({agent.name: agent.target_devices})
            self.transit_devices.update({agent.name: transit_devices})
            self.queues.update({agent.name: queue.Queue()})

            for agentConnect in agents:
                if agentConnect != agent:
                    agent.qconnections[agentConnect.name] = self

    def put(self, source, target, qubits, source_time):
        ''' 
        Constructs full list of devices that each qubit must travel through. Sends the qubits
        through source devices. Places qubits and a list of transit and target 
        devices on the queue. Queue is keyed on the target agent's name.
        
        :param String source: name of agent where the qubits being sent originated
        :param String target: name of agent receiving qubits
        :param Array qubits: array of numbers corresponding to qubits the source is sending 
        :param Float source_time: time of source agent before sending qubits
        :returns: time qubits took to pass through source devices
        '''
        source_devices = self.source_devices[source]
        transit_devices = self.transit_devices[source]
        target_devices = self.target_devices[target]

        non_source_devices = {
            "transit": transit_devices,
            "target": target_devices,
        }

        program = self.agents[source].program
        source_delay = 0

        # Keep track of qubits remaining
        traveling_qubits = qubits

        if not source_devices:
            source_delay += pulse_length_default
        else:
            # Keep track of qubits lost by each device
            total_lost_qubits = []
            for device in source_devices:
                # If qubits are still remaining 
                if traveling_qubits:
                    res = device.apply(program, traveling_qubits)
                    if 'lost_qubits' in res.keys(): 
                        lost_qubits = res['lost_qubits']
                        # Remove lost qubits from traveling qubits
                        traveling_qubits = list(set(traveling_qubits) - set(lost_qubits))
                        # Add lost_qubits lost from current device to total_lost_qubits
                        total_lost_qubits += lost_qubits
                    if 'delay' in res.keys(): source_delay += res['delay']

                else: break

            # Invert lost qubits and add to traveling qubits
            for q in total_lost_qubits: 
                if q == 0: total_lost_qubits.append(float("-inf"))
                else: total_lost_qubits.append(-q)
            traveling_qubits += total_lost_qubits

        # Scale source delay time according to number of qubits sent
        scaled_source_delay = source_delay*len(qubits) 

        self.queues[target].put((traveling_qubits, non_source_devices, scaled_source_delay, source_time))
        return scaled_source_delay

    def get(self, agent): 
        '''
        Pops qubits off of the agent's queue. Sends qubit through transit and target devices,
        simulating a quantum network. Return an array of the qubits that have been altered, as well as
        the time it took the qubit to travel through the network. Some qubits may be lost during transmission. If lost,
        their value will switch to negative, or, in the case of 0, be set to -inf

        :param Agent agent: agent receiving the qubits 
        :returns: list of qubits, time to pass through transit and target devices, and the source agent's time
        '''
        traveling_qubits, devices, source_delay, source_time = self.queues[agent.name].get()

        agent.qubits = list(set(traveling_qubits + agent.qubits))

        program = self.agents[agent.name].program
       
        transit_devices = devices["transit"]
        target_devices = devices["target"]

        # Number of qubits before any are lost 
        num_travel_qubits = len(traveling_qubits)
        travel_delay = 0

        if not transit_devices:
            travel_delay += fiber_length_default/signal_speed
        if not target_devices:
            travel_delay += 0
        
        total_lost_qubits = [q for q in traveling_qubits if q < 0 or q == float("-inf")] 
        remaining_qubits = [q for q in traveling_qubits if q >= 0]

        for device in list(itertools.chain(transit_devices, target_devices)):
            # If qubits are remaining 
            if remaining_qubits: 
                res = device.apply(program, traveling_qubits)
                if 'lost_qubits' in res.keys(): 
                    lost_qubits = res['lost_qubits']
                    # Remove lost qubits from traveling qubits
                    remaining_qubits = list(set(remaining_qubits) - set(lost_qubits))
                    # Add lost_qubits lost from current device to total_lost_qubits
                    total_lost_qubits += lost_qubits
                if 'delay' in res.keys(): travel_delay += res['delay']
            else: break

        # Remove traveling_qubits
        agent.qubits = list(set(agent.qubits) - set(traveling_qubits))   

        lost_qubits_flipped = []
        for q in total_lost_qubits: 
            if q == 0: lost_qubits_flipped.append(float("-inf"))
            else:
                lost_qubits_flipped.append(-q)

        # Add inverted lost qubits to remaining qubits
        traveling_qubits = remaining_qubits + lost_qubits_flipped
        agent.qubits += traveling_qubits
        scaled_delay = travel_delay*num_travel_qubits + source_delay
        return traveling_qubits, scaled_delay, source_time

class CConnect: 
    def __init__(self, *args, length=0.0):
        '''
        This is the base class for a classical connection between multiple agents. 

        :param agents \*args: list of agents to connect
        :param Float length: distance between first and second agent
        '''
        agents = list(args)
        self.agents = {}

        '''
        Create queue to keep track of multiple requests. Name of queue is name of
        target agent.  
        '''
        self.queues = {}

        for agent in agents:
            self.agents.update({agent.name: agent})
            self.queues.update({agent.name: queue.Queue()})

            for agentConnect in agents:
                if agentConnect != agent:
                    agent.cconnections[agentConnect.name] = self

        self.length = length

    def put(self, target, cbits):
        ''' 
        Places cbits on queue keyed on the target Agent's name

        :param String target: name of recipient of program
        :param Array cbits: array of numbers corresponding to cbits agent is sending
        :returns: time for cbits to travel
        '''
        csource_delay = pulse_length_default * 8 * sys.getsizeof(cbits)
        self.queues[target].put((cbits, csource_delay))
        return csource_delay

    def get(self, agent): 
        ''' 
        Pops cbits off of the agent's queue and adds travel delay

        :param String agent: name of the agent receiving the cbits
        :returns: cbits from source and time they took to travel
        '''
        cbits, source_delay = self.queues[agent].get()
        travel_delay = self.length/signal_speed
        
        scaled_delay = travel_delay*len(cbits) + source_delay

        return cbits, scaled_delay