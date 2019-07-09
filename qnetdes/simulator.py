__all__ = ["Simulation"]

def is_notebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False # Probably standard Python interpreter

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
        # Check is client is using jupyter notebooks
        n = is_notebook()
        
        for agent in self.agents:
            agent.start_network_monitor(n)
            agent.start()
        
        for agent in self.agents: 
            agent.join()
            agent.stop_network_monitor()