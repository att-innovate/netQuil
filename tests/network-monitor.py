import sys
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *
    
class Alice(Agent):
    '''
    Alice sends Bob superdense-encoded classical bits
    '''
    def run(self):
        p = self.program
        for i in self.qubits:
            p += H(i) 
            self.qsend(bob.name, [i])

class Bob(Agent):
    '''
    Bob reconstructs Alice's classical bits
    '''
    def run(self):
        p = self.program
        ro = p.declare('ro', 'BIT', len(alice.qubits))
        for i in range(len(alice.qubits)):
            qbits = self.qrecv(alice.name)
            p += MEASURE(qbits[0], ro)

qvm = QVMConnection()
program = Program()
#define agents
alice = Alice(program, qubits=list(range(100)))
# for i in range(99):
#     alice.add_cmem([0])
# alice.add_source_devices([Laser(apply_error=True)])
bob = Bob(program)

#connect agents
QConnect(alice, bob)

#simulate agents
Simulation(alice, bob).run(verbose=False, network_monitor=False)
results = qvm.run(program)
print(results)
print(alice.master_clock.get_time())