import inspect
import sys
import threading
import time

__all__ = ["Agent"]

class Agent(threading.Thread):
    def __init__(self, program=None, qubits=[], cmem=[], name=None):
        '''
        Agents are codified versions of Alice and Bob (i.e. single nodes in a quantum network) 
        that can send and receive classical and quantum information over connections. 
        Agents have the following properties: 

        * Their run-time logic is in the form of an Agent.run() method
        * Their connections to other agents are by default ingress and egress 
        * Agents' manage their own target and source devices for noise and local time tracking
        * Agents have a network monitor to record the traffic they see

        :param PyQuil<Program> program: program
        :param List<int> qubits: list of qubits owned by agent
        :param List<int> cmem: list of cbits owned by agent
        :param String name: name of agent, defaults to name of class
        '''
        threading.Thread.__init__(self)

        # Name of the agent, e.g. "Alice". Defaults to the name of the class.
        if name is not None:
            self.name = name
        else:
            self.name = self.__class__.__name__

        self.time = 0.0
        self.pulse_length = 10 * 10 ** -12 # 10 ps default photon pulse length
        self.qconnections = {}
        self.cconnections = {}

        # Define qubits, corresponding classical memory and program
        self.qubits = qubits 
        self.cmem = cmem 
        self.program = program

        # Define Agent Devices
        self.target_devices = []
        self.source_devices = []

        self.master_clock = None
        self.network_monitor_running = False
        self.using_distributed_gate = False

    def get_master_time(self): 
        '''
        :return: master time
        '''
        return self.master_clock.get_time()

    def _start_tracer(self):
        threading.settrace(self._tracer)

    def _get_device_results(self):
        '''
        Get results for source and target devices
        '''
        devices = self.source_devices + self.target_devices
        for device in devices: 
            if device.verbose:
                device.get_results()
 
    def update_network_monitor(self, qubits, bar):
        for _ in qubits: 
            time.sleep(0.05)
            bar.update()

    def _tracer(self, frame, event, arg):
        '''
        Prevents agent from modifying qubits that it does not own and manage by
        examining the frame and intercepting all pyquil.gates calls 
        '''
        if event == "call":
            if self.using_distributed_gate: 
                return self._tracer
            if frame.f_globals['__name__'] == 'pyquil.gates':
                # Returns dictionary of parameter names and their values
                argsToGate = inspect.getargvalues(frame)
                # Extract parameter values 
                argValues = list(argsToGate.locals.values())
                # Extract parameter values that are integers (ignore iterator arguments)
                qubits = [q for q in argValues if type(q) == int]
                # Check that qubits are a subset of the Agent's qubits
                if not all(q in self.qubits for q in qubits):
                    raise Exception('Agent cannot modify qubits they do not own (including qubits that have been lost)')

        return self._tracer
    
    def set_program(self, program):
        '''
        Set agent's program

        :param PyQuil<Program> program: agent's program
        '''
        self.program = program

    def add_target_devices(self, new_target_devices):
        '''
            Add target devices. Every qubit sent to agent will pass through these devices, 
            and, if set, the device's effect and time-delay will be applied

            :param List<Device> new_target_devices: list of target devices
        '''
        self.target_devices.extend(new_target_devices)

    def add_source_devices(self, new_source_devices):
        '''
            Add source devices. Every qubit sent by Agent will pass through these devices, 
            and, if set, the device's effect and time-delay will be applied 

            :param List<Device> new_source_devices: list of source devices
        '''
        self.source_devices.extend(new_source_devices)

    @property
    def cmem(self): 
        return self.__cmem

    @cmem.setter
    def cmem(self, cmem):
        '''
            Set classical memory as list of 0s and 1s

            :param List<int> cmem: classical memory
        '''
        if len(cmem) >= 0 and all(bit == 0 or bit == 1 for bit in cmem):
            self.__cmem = cmem
        else:  
            raise Exception('Classical bits must be in list and either 0 or 1')

    def add_cmem(self, cbits):
        '''
            Add more classical memory in the form of a list of 0s and 1s

            :param List<int> cbits: classical memory to extend
        '''
        self.__cmem.extend(cbits) 

    def add_device(self, device_type, device):
        ''' 
            Add a device to an agent.

            :param String device_type: may be either `source` or `target`
            :param Device device: instance of device added
        '''
        if device_type == 'source': 
            self.source_devices.append(device)
        elif device_type == 'target':
            self.target_devices.append(device)
        else: 
            raise Exception('Invalid device type (e.g. \'source\' or \'target\'')

    def __hash__(self):
        '''
        Agents are hashed by their (unique) names
        '''
        return hash(self.name)
    
    def __eq__(self, other):
        '''
        Agents are compared for equality by their names.
        '''
        return self.name == other.name

    def __ne__(self, other):
        '''
        Agents are compared for inequality by their names
        '''
        return not (self == other)

    def qsend(self, target, qubits):
        '''
        Send qubits from agent to target. Connection will place qubits on queue 
        for target to retrieve. 

        :param String target: name of destination for qubits 
        :param List<int> qubits: list of qubits to send to destination
        '''
        # Raise exception if agent sends qubits they do no have
        if not set(qubits).issubset(set(self.qubits)): 
            raise Exception('Agent cannot send qubits they do not have')
            
        connection = self.qconnections[target]
        source_delay = connection.put(self.name, target, qubits, self.time)
    
        # Removing qubits being sent
        self.qubits = list(set(self.qubits) - set(qubits))

        # Update Agent's Time
        self.time += source_delay

        # Update Master Clock
        self.master_clock.record_qtransaction(self.time, 'sent', self.name, target, qubits)

        # Update network monitor 
        if self.network_monitor_running: 
            self.update_network_monitor(qubits, self.pbar_sent)

    def qrecv(self, source):
        '''
        Agent receives qubits from source. Adds qubits to agent's list of qubits and
        add time delay. Return list of qubits
        
        :param String source: name of agent who sent qubits.
        :return: list of qubits sent from source
        '''
        connection = self.qconnections[source]
        qubits, delay, source_time = connection.get(self)
        self.time = max(source_time + delay, self.time) 

        # Update Master Clock
        self.master_clock.record_qtransaction(self.time, 'received', source, self.name, qubits)
        # Update network monitor 
        if self.network_monitor_running: 
            self.update_network_monitor(qubits, self.pbar_recv)

        return qubits
        
    def csend(self, target, cbits):
        '''
        Sends classical bits from agent to target.

        :param String target: name of target agent
        :param List<int> cbits: indices of cbits source is sending to target
        '''
        connection = self.cconnections[target]
        source_delay  = connection.put(target, cbits)
        scaled_source_delay = source_delay*len(cbits)
        self.time += scaled_source_delay
        
        #Update Master Clock
        self.master_clock.record_ctransaction(self.time, 'sent', self.name, target, cbits)
        
    def crecv(self, source):
        '''
        Get cbits from source. 
        
        :param String source: name of Agent where cbits originated from.
        :return: list of cbits sent from source
        '''
        connection = self.cconnections[source]
        cbits, delay = connection.get(self.name)
        self.time += delay

        #Update Master Clock
        self.master_clock.record_ctransaction(self.time, 'received', source, self.name, cbits)

        return cbits

    def run(self):
        '''Run-time logic for the Agent; this method should be overridden in child classes.'''
        pass
