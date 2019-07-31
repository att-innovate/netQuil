import inspect
import sys
import threading
import tqdm
import time

__all__ = ["Agent"]

class Agent(threading.Thread):
    def __init__(self, program=None, qubits=[], cmem=[], name=None):
        '''
        Agents are codified versions of Alice and Bob (i.e. single nodes in a quantum network) 
        that can send a receive classical and quantum information over connections. 
        Agents have the following properties: 

        * Run-time logic is in the form of an Agent.run() method
        * Connections to other Agents are by default ingress and egress 
        * Agents' manage their own target and source devices for noise and local time tracking
        * A network monitor to records traffic of a single Agent

        :param PyQuil<Program> program: program
        :param List qubits: list of qubits owned by Agent
        :param List cmem: list of cbits owned by Agent
        :param String name: name of Agent, defaults to name of class
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
        Return master time
        '''
        return self.master_clock.get_time()

    def _start_network_monitor(self, is_notebook, network_monitor):
        '''
            Starts tracking agent activity.
        '''
        if network_monitor: 
            self.network_monitor_running = True
            if is_notebook:
                self.pbar_recv = tqdm.tqdm_notebook(desc='Qubits received by {}'.format(self.name), unit=' qubits')
                self.pbar_sent = tqdm.tqdm_notebook(desc='Qubits sent by {}'.format(self.name), unit=' qubits')
            else: 
                self.pbar_recv = tqdm.tqdm(desc='Qubits received by {}'.format(self.name), unit=' qubits')
                self.pbar_sent = tqdm.tqdm(desc='Qubits sent by {}'.format(self.name), unit=' qubits')
        
        # start tracer
        threading.settrace(self._tracer)

    def _stop_network_monitor(self): 
        '''
        Stop progress bars and break source devices noise to signal ratios
        ''' 
        if self.network_monitor_running: 
            self.pbar_recv.close()
            self.pbar_sent.close()
            # Print source device signal to noise ratio
            for device in self.source_devices: 
                device.get_success()
 
    def update_network_monitor(self, qubits, bar):
        for _ in qubits: 
            time.sleep(0.05)
            bar.update(1)

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
                    raise Exception('Agent cannot modify qubits they do not own')

        return self._tracer
    
    def set_program(self, program):
        '''
        Set Agent's program

        :param PyQuil<Program> program: Agent's new program
        '''
        self.program = program

    def add_target_devices(self, new_target_devices):
        '''
            Add target devices. Every qubit sent to Agent will pass through these devices, 
            and, if set, the device's noise will be applied

            :param List new_target_devices: Agent new target devices
        '''
        self.target_devices.extend(new_target_devices)

    def add_source_devices(self, new_source_devices):
        '''
            Add source devices. Every qubit sent by Agent will pass through these devices, 
            and, if set, the device's noise will be applied 

            :param List new_source_devices: Agent new source devices
        '''
        self.source_devices.extend(new_source_devices)

    @property
    def cmem(self): 
        return self.__cmem

    @cmem.setter
    def cmem(self, cmem):
        '''
            Set classical memory as list of 0s and 1s

            :param List cmem: Classical memory
        '''
        if len(cmem) >= 0 and all(bit == 0 or bit == 1 for bit in cmem):
            self.__cmem = cmem
        else:  
            raise Exception('Classical bits must be in list and either 0 or 1')

    def add_cmem(self, cbits):
        '''
            Add more classical memory in the form of a list of 0s and 1s

            :param List cbits: classical memory to extend
        '''
        self.__cmem.extend(cbits) 

    def add_device(self, device_type, device):
        ''' 
            Add device to agent node.

            :param String device_type: category of device
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
        Send qubits from Agent to target. Connection will place qubits on queue 
        for target to retrieve. 

        :param String target: name of destination for packet
        :param List qubits: packet to send to destination
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
        Agent receives qubits from source. Adds qubits to Agent's list of qubits and
        add time delay. Return qubits
        
        :param String source: name of Agent where qubits are from. 
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
        Sends classical bits from Agent to target.

        :param String target: name of target Agent
        :param List cbits: indicies of cbits source is sending to target
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