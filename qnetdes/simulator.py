import inspect
import sys
import threading

__all__ = ["Simulation"]

class Simulation:
    def __init__(self, *args):
        '''
        Initialize the simulation
        '''
        self.agents = args

    def tracefunc(self, frame, event, arg, indent=[0]):
        if event == "call":
            if frame.f_globals['__name__'] == 'pyquil.gates':
                inspect.getargvalues(frame)
                print(frame.f_locals)
        return self.tracefunc

    def run(self, network_monitor=False, verbose=False):
        '''
        Run the simulation

        :param Boolean network_monitor: whether to start a network monitor 
        :param Boolean verbose: whether the network monitor should create an error summary
            for each network transaction.
        '''
        sys.settrace(self.tracefunc)

        for agent in self.agents:
            agent.start()
        
        for agent in self.agents: 
            agent.join()