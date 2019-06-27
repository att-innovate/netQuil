__all__ = ["Simulation"]

class Simulation:
    def __init__(self, *args):
        '''
        Initialize the simulation
        '''
        self.agents = args

    def run(self, network_monitor=False, verbose=False):
        '''
        Run the simulation

        :param Boolean network_monitor: whether to start a network monitor 
        :param Boolean verbose: whether the network monitor should create an error summary
            for each network transaction.
        '''

        for agent in self.agents:
            agent._manageAgentQubits()
            agent.start()
        
        for agent in self.agents: 
            agent.join()