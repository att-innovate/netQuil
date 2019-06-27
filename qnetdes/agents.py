import inspect
import sys
import threading

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
        self.qconnections = {}
        self.cconnections = {}

        # Define qubits, corresponding classical memory and program
        self.qubits = qubits 
        self.cmem = cmem 
        self.program = program

        # Define Agent Devices
        self.target_devices = []
        self.source_devices = []

    def _manageAgentQubits(self):
        '''
            Starts tracking agent activity.
        '''
        threading.settrace(self._tracer)

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

    @property
    def cmem(self): 
        return self.__cmem

    @cmem.setter
    def cmem(self, cmem):
        if len(cmem) >= 0 and all(bit == 0 or bit == 1 for bit in cmem):
            self.__cmem = cmem
        else:  
            raise Exception('Classical bits must be either 0 or 1')

    def add_cmem(self, cbits):
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
        :param Packet packet: packet to send to destination
        '''
        # Raise exception if agent sends qubits they do no have
        if not set(qubits).issubset(set(self.qubits)): 
            raise Exception('Agent cannot send qubits they do not have')
            
        # Removing qubits being sent
        self.qubits = list(set(self.qubits) - set(qubits))
        connection = self.qconnections[target]
        connection.put(self.name, target, qubits)

    def qrecv(self, source):
        '''
        Self receives qubits from source. Adds qubits to self's list of qubits and
        add time delay. Return qubits
        
        :param String source: name of source of qubits agent is attempting to retrieve from. 
        '''
        connection = self.qconnections[source]
        qubits, delay = connection.get(self.name)
        self.qubits = list(set(qubits + self.qubits))
        self.time += delay
        return qubits
        
    def csend(self, target, cbits):
        '''
        Sends classical bits from self to target.
        :param String target: name of agent self is sending cbits to
        :param Array cbits: indicies of cbits self is sending to target
        '''
        connection = self.cconnections[target]
        connection.put(target, cbits)
        
    def crecv(self, source):
        '''
        Self receives cbits from source. 
        
        :param String source: name of agent where cbits are from.
        '''
        connection = self.cconnections[source]
        cbits = connection.get(self.name)
        return cbits

    def run(self):
        '''Runtime logic for the Agent; this method should be overridden in child classes.'''
        pass

    # def done():  May need to add agent.terminate() if multithreading is broken