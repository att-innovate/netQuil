import inspect
from .clock import *

__all__ = ["Simulation"]

def check_notebook():
    '''
    Check is client is using jupyter notebook
    '''
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

# Attributes to keep on newly instantiated agent when resetting agents
THREADING_ATTRS = ['_started', '_stderr', '_tstate_lock', '_initialized', '_indent', '_is_stopped', '_target']

class Simulation:
    def __init__(self, *args):
        '''
        Initialize the simulation
        '''
        self.agents = list(args)

    def _create_agent_copies(self):
        '''
        Creates a dictionary of attributes for each agent. Stores list of dictionaries on self.agent_copies.
        Used to reset agents to their original state before each trial. Execute this function once at beginning of run
        if client requests multiple trials
        '''
        self.agent_copies = []
        for agent in self.agents:
            # Get attributes
            attributes = inspect.getmembers(agent, lambda a:not(inspect.isroutine(a)))
            # Remove private funcs and pythonic attrs 
            attrs_tuples = [a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
            attrs_dict = dict(attrs_tuples)
            attrs_clean = {k: v for k, v in attrs_dict.items() if k not in THREADING_ATTRS}
            self.agent_copies.append(attrs_clean)

    def _reset_agents(self, agent_classes):
        '''
        Creates exact duplicate of original agent given the class constructor and 
        a dictionary of agent attributes

        :param List<Agent> agent_classes: list of agent classes 
        '''
        for indx, copy in enumerate(self.agent_copies): 
            # Create copy of agent
            new_agent = agent_classes[indx]()
            for k in copy:
                try: 
                    setattr(new_agent, k, copy[k])
                except: 
                    pass
            self.agents[indx] = new_agent

    def _reset_devices(self):
        '''
        Reset source devices for each agent after each trial. 
        '''
        for agent in self.agents: 
            for device in agent.source_devices:
                device.reset()

    def run(self, trials=1, agent_classes=[], network_monitor=False, verbose=False):
        '''
        Run the simulation

        :param Int trials: number of times to simulate program
        :param List<Agent> agent_classes: list of agent classes
        :param Boolean network_monitor: whether to start a network monitor 
        :param Boolean verbose: whether the network monitor should create an error summary
            for each network transaction.
        '''
        # Check is client is using jupyter notebooks
        using_notebook = check_notebook()
        running_trials = trials > 1 
        # If trials is greater than 1, create copies of each agent
        if running_trials: self._create_agent_copies()

        for _ in range(trials): 
            master_clock = MasterClock()
            for agent in self.agents:
                agent.master_clock = master_clock
                agent._start_network_monitor(using_notebook, network_monitor)
                agent.start()
            
            for agent in self.agents: 
                agent.join()
                agent._stop_network_monitor()

            if verbose: 
                master_clock.display_transactions()

            if running_trials:
                self._reset_devices()
                self._reset_agents(agent_classes)


