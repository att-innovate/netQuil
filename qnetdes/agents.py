import inspect
import sys
import threading
import tqdm
import time

__all__ = ["Agent"]

class Agent(threading.Thread):
    def __init__(self, program, qubits=[], cmem=[], name=None):
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

    def start_network_monitor(self, is_notebook):
        '''
            Starts tracking agent activity.
        '''
        if is_notebook:
            self.pbar_recv = tqdm.tqdm_notebook(desc='Qubits received by {}'.format(self.name), unit=' qubits')
            self.pbar_sent = tqdm.tqdm_notebook(desc='Qubits sent by {}'.format(self.name), unit=' qubits')
        else: 
            self.pbar_recv = tqdm.tqdm(desc='Qubits received by {}'.format(self.name), unit=' qubits')
            self.pbar_sent = tqdm.tqdm(desc='Qubits sent by {}'.format(self.name), unit=' qubits')
        threading.settrace(self._tracer)

    def stop_network_monitor(self): 
        '''
        Stop progress bars
        ''' 
        self.pbar_recv.close()
        self.pbar_sent.close()
 
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
    
    def add_target_devices(self, new_target_devices):
        '''
            Add self target devices

            :param List new_target_devices: Agent new target devices
        '''
        self.target_devices.extend(new_target_devices)

    def add_source_devices(self, new_source_devices):
        '''
            Add self source devices

            :param List new_source_devices: Agent new source devices
        '''
        self.source_devices.extend(new_source_devices)

    @property
    def cmem(self): 
        return self.__cmem

    @cmem.setter
    def cmem(self, cmem):
        '''
            Set classical memory

            :param List cmem: Classical memory
        '''
        if len(cmem) >= 0 and all(bit == 0 or bit == 1 for bit in cmem):
            self.__cmem = cmem
        else:  
            raise Exception('Classical bits must be either 0 or 1')

    def add_cmem(self, cbits):
        '''
            Add more classical memory

            :param List cbits: classical memory to extend
        '''
        self.cmem = self.__cmem.extend(cbits) 

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
        Send packet from self to target. Connection will place packet on queue 
        for target to retrieve. 

        :param String target: name of destination for packet
        :param List qubits: packet to send to destination
        '''
        # Raise exception if agent sends qubits they do no have
        if not set(qubits).issubset(set(self.qubits)): 
            raise Exception('Agent cannot send qubits they do not have')
            
        connection = self.qconnections[target]
        source_delay = connection.put(self.name, target, qubits)
        
        # Removing qubits being sent
        self.qubits = list(set(self.qubits) - set(qubits))

        # Update Agent's Time
        self.time += source_delay

        # Update network monitor 
        self.update_network_monitor(qubits, self.pbar_sent)

    def qrecv(self, source):
        '''
        Self receives qubits from source. Adds qubits to self's list of qubits and
        add time delay. Return qubits
        
        :param String source: name of source of qubits agent is attempting to retrieve from. 
        '''
        connection = self.qconnections[source]
        qubits, delay = connection.get(self)
        self.time += delay

        # Update network monitor 
        self.update_network_monitor(qubits, self.pbar_recv)

        return qubits
        
    def csend(self, target, cbits):
        '''
        Sends classical bits from self to target.

        :param String target: name of agent self is sending cbits to
        :param List cbits: indicies of cbits self is sending to target
        '''
        connection = self.cconnections[target]
        csource_delay  = connection.put(target, cbits)
        self.time += csource_delay
        
    def crecv(self, source):
        '''
        Self receives cbits from source. 
        
        :param String source: name of agent where cbits are from.
        '''
        connection = self.cconnections[source]
        cbits, delay = connection.get(self.name)
        self.time += delay
        return cbits

    def run(self):
        '''Runtime logic for the Agent; this method should be overridden in child classes.'''
        pass