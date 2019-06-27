import multiprocessing

__all__ = ["QConnect", "CConnect"]

class QConnect(): 
    def __init__(self, agent_one, agent_two, transit_devices):
        '''
            Get devices from source node (e.g. laser, intensity modulator, etc...), 
            target node (e.g. sensor, beam splitter), and transit devices (e.g. fiber optics, free space)

            :param: Agent agent_one: first agent in connection
            :param: Agent agent_two: second agent in connection
            :param  Array transit_devices: array of devices packets travel through - assumed order: agent_one -> agent_two
        '''
        agent_one_name = agent_one.name 
        agent_two_name = agent_two.name
        
        self.source_devices = {
            agent_one_name: agent_one.source_devices if hasattr(agent_one, 'source_devices') else None,
            agent_two_name: agent_two.source_devices if hasattr(agent_two, 'source_devices') else None,
        }

        self.target_devices = {
            agent_one_name: agent_one.target_devices if hasattr(agent_one, 'target_devices') else None, 
            agent_two_name: agent_two.target_devices if hasattr(agent_two, 'target_devices') else None, 
        }
        ''' 
            Assumed order of transit_devices is agent_one -> agent_two (i.e. source -> target).
        '''
        self.transit_devices = {
            agent_one_name: transit_devices, 
            agent_two_name: transit_devices[::-1]
        }

        # add connection ingress and outgress qconnection to agent_one and agent_two
        agent_one.qconnections[agent_two_name] = self
        agent_two.qconnections[agent_one_name] = self
       
        self.agents = (agent_one, agent_two)
        '''
            Create queue to keep track of multiple requests. Name of queue is name of
            target agent.  
        '''
        self.queues = {
            agent_one_name: multiprocessing.Queue(),
            agent_two_name: multiprocessing.Queue()
        }

    def put(self, source, target, qubits):
        ''' 
        Constructs full list of devices that each qubit must travel through. 
        Places qubits, delay and the list of devices on a queue. Queue is keyed on target's name.
        
        :param String source: name of agent where the qubits being sent originated
        :param String target: name of agent receiving qubits
        :param Array qubits: array of numbers corresponding to qubits the source is sending 
        '''
        source_devices = self.source_devices[source]
        transit_devices = self.transit_devices[source]
        target_devices = self.target_devices[target]

        devices = source_devices + transit_devices + target_devices
        delay = 0
        self.queues[target].put((qubits, devices, delay))

    def get(self, agent): 
        '''
        Pops qubits off of the agent's queue. Sends each qubit through the devices in the qubits
        path through the network. Return an array of the qubits that have been altered as well as
        the time it took the qubit to travel through the network. 

        :param String agent: name of the agent receiving the qubits 
        '''
        qubits, devices, delay = self.queues[agent].get()
        program = self.agents[0].program
        for device in devices: 
            if device is not None: 
                delay += device.apply(program, qubits)
        
        return qubits, delay

class CConnect(): 
    def __init__(self, agent_one, agent_two):
        # add ingress and egress classical traffic between agent_one and agent_two
        agent_one_name = agent_one.name
        agent_two_name = agent_two.name
        agent_one.cconnections[agent_two_name] = self
        agent_two.cconnections[agent_one_name] = self
       
        '''
            Create queue to keep track of multiple requests. Name of queue is name of
            target agent.  
        '''
        self.queues = {
            agent_one_name: multiprocessing.Queue(),
            agent_two_name: multiprocessing.Queue()
        }

    def put(self, target, cbits):
        ''' 
        Places cbits and delay on the queue. 

        :param String target: name of recipient of program
        :param Array cbits: array of numbers corresponding to cbits agent is sending
        '''
        delay = 0
        self.queues[target].put((cbits, delay))

    def get(self, agent): 
        ''' 
        Pops cbits off of the agent's queue. 

        :param String agent: name of the agent receiving the cbits
        '''
        cbits, _ = self.queues[agent].get()
        return cbits