import queue
import multiprocessing
import itertools
import sys

__all__ = ["QConnect", "CConnect"]

pulse_length_default = 10 * 10 ** -12 # 10 ps photon pulse length
signal_speed = 2.998 * 10 ** 5 #speed of light in km/s
fiber_length_default = 0.0

class QConnect(): 
    def __init__(self, agent_one, agent_two, transit_devices=[]):
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
            agent_one_name: agent_one.source_devices,
            agent_two_name: agent_two.source_devices,
        }

        self.target_devices = {
            agent_one_name: agent_one.target_devices,
            agent_two_name: agent_two.target_devices,
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
       
        self.agents = {
            agent_one_name: agent_one,
            agent_two_name: agent_two
        }

        '''
            Create queue to keep track of multiple requests. Name of queue is name of
            target agent.  
        '''
        self.queues = {
            agent_one_name: queue.Queue(),
            agent_two_name: queue.Queue()
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

        non_source_devices = {
            "transit": transit_devices,
            "target": target_devices,
        }

        program = self.agents[source].program
        qsource_delay = 0

        if not source_devices:
            qsource_delay += pulse_length_default
        else:
            for device in source_devices:
                qsource_delay += device.apply(program, qubits)

        self.queues[target].put((qubits, non_source_devices, qsource_delay))
        return qsource_delay

    def get(self, agent): 
        '''
        Pops qubits off of the agent's queue. Sends each qubit through the devices in the qubits
        path through the network. Return an array of the qubits that have been altered as well as
        the time it took the qubit to travel through the network. 

        :param Agent agent: agent receiving the qubits 
        '''
        qubits, devices, delay = self.queues[agent.name].get()
        agent.qubits = list(set(qubits + agent.qubits))

        program = self.agents[agent.name].program
       
        transit_devices = devices["transit"]
        target_devices = devices["target"]

        #default delays
        if not transit_devices:
            delay += fiber_length_default/signal_speed
        if not target_devices:
            delay += 0
          
        for device in list(itertools.chain(transit_devices, target_devices)):
            delay += device.apply(program, qubits)  

        return qubits, delay

class CConnect(): 
    def __init__(self, agent_one, agent_two, length=0.0):
        # add ingress and egress classical traffic between agent_one and agent_two
        agent_one_name = agent_one.name
        agent_two_name = agent_two.name
        agent_one.cconnections[agent_two_name] = self
        agent_two.cconnections[agent_one_name] = self
       
        self.agents = { 
            agent_one_name: agent_one, 
            agent_two_name: agent_two
        }

        self.length = length
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
        csource_delay = pulse_length_default * 8 * sys.getsizeof(cbits)
        self.queues[target].put((cbits, csource_delay))
        return csource_delay

    def get(self, agent): 
        ''' 
        Pops cbits off of the agent's queue. 

        :param String agent: name of the agent receiving the cbits
        '''
        cbits, delay = self.queues[agent].get()
        delay += self.length/signal_speed

        return cbits, delay