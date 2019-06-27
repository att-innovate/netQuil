# Remove in future: currently allows us to import qnetdes
import sys
import threading 
import inspect
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')

from pyquil import Program
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator
from qnetdes import *

agents = ['alice', 'bob']
current_agent = None 

def tracefunc(frame, event, arg, indent=[0]):
      if event == "call":
        # if frame.f_code.co_name == 'run': 
        #     print(frame.f_code)
        #     print(frame.f_globals['alice'])

        #print(frame.f_globals)
        for agent in agents:
            print(frame.f_globals.values)
            if hasattr(frame.f_globals, 'alice'): 
                print('in')
                global current_agent
                current_agent = agent
                # print(current_agent)

        if frame.f_globals['__name__'] == 'pyquil.gates':
            # Check that current agent has correct qubits
            qubits = inspect.getargvalues(frame)
            # print(qubits, current_agent)
            # print(frame.f_globals)
      return tracefunc

sys.settrace(tracefunc)

class Alice():
    def run(self):
        p = Program(H(1)) 

alice = Alice()
alice.run()
