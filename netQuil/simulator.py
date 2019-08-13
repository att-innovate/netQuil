import inspect
from .clock import *
import tqdm

from pyquil import Program

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
        self.pbars = {}

    def _create_agent_copies(self):
        '''
        Creates a dictionary of attributes for each agent. Stores list of dictionaries on self.agent_copies.
        Used to reset agents to their original state before each trial. Execute this function once at beginning of run
        if client requests multiple trials
        '''
        self.agent_copies = []
        program = self.agents[0].program.copy()
        for agent in self.agents:
            # Get attributes
            attributes = inspect.getmembers(agent, lambda a:not(inspect.isroutine(a)))
            # Remove private funcs and pythonic attrs 
            attrs_tuples = [a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
            attrs_dict = dict(attrs_tuples)
            attrs_clean = {k: v for k, v in attrs_dict.items() if k not in THREADING_ATTRS}
            attrs_clean["program"] = program
            self.agent_copies.append(attrs_clean)

    def _reset_agents(self, agent_classes):
        '''
        Creates exact duplicate of original agent given the class constructor and 
        a dictionary of agent attributes from _create_agent_copies

        :param List<Agent> agent_classes: list of agent classes 
        '''
        program_copy = None
        for indx, copy in enumerate(self.agent_copies): 
            # Create copy of agent
            new_agent = agent_classes[indx]()
            for k in copy:
                try: 
                    setattr(new_agent, k, copy[k])
                    if k == 'program' and program_copy == None:
                        program_copy = copy[k].copy()
                    if k == 'program': 
                        setattr(new_agent, k, program_copy)
                except: 
                    pass
            self.agents[indx] = new_agent

    def _reset_devices(self):
        '''
        Reset source devices for each agent after each trial. 
        '''
        for agent in self.agents: 
            for connection in agent.qconnections.values():
                connection.agents = {a.name: a for a in self.agents}
            for device in agent.source_devices:
                device.reset()

    def _add_program(self):
        '''
        Adds program to all agents if none set. If agents are not all sharing
        the same program, raise an exception.
        '''
        p = Program()
        set_program = self.agents[0].program

        for agent in self.agents: 
            if agent.program != set_program:
                raise Exception('All agents must share the same program')
            if agent.program == None: 
                agent.program = p

    def run(self, trials=1, agent_classes=[], network_monitor=False):
        '''
        Run the simulation

        :param Int trials: number of times to simulate program
        :param List<Agent> agent_classes: list of agent classes
        :param Boolean network_monitor: outputs each network transaction and device information
        :return: Returns list of programs. One for each trial
        '''
        self.using_notebook = check_notebook()

        # If program is not set, add default
        self._add_program()
        
        programs = []
        running_trials = trials > 1 

        # If trials is greater than 1, create copies of each agent
        if running_trials: self._create_agent_copies()

        for _ in range(trials): 

            # Start master clock and network monitor
            master_clock = MasterClock()
            for agent in self.agents:
                agent.master_clock = master_clock

            # Start agents, tracer, and network monitor
            for idx, agent in enumerate(self.agents):
                agent._start_tracer()
                agent.start()

            # Wait for agents to finish 
            for agent in self.agents: 
                agent.join()

            if network_monitor: 
                agent._get_device_results()
                master_clock.display_transactions()

            # Record program generated from trial
            programs.append(self.agents[0].program)

            # Reset agents if multiple trials
            if running_trials:
                self._reset_agents(agent_classes)
                self._reset_devices()

        return programs