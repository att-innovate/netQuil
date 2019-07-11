import sys
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *

class Bob(Agent):
   
    def run(self):
        p = self.program
        #test bit flip
        noise.bit_flip(p,0,0)
        print("0 bit flip")
        printWF(p)
        noise.bit_flip(p,0,1)
        print("1 bit flip")
        printWF(p)

        p += H(0)
        print("H gate")
        printWF(p)

        #test phase flip
        noise.phase_flip(p,0,0)
        print("0 phase flip")
        printWF(p)
        noise.phase_flip(p,0,1)
        print("1 phase flip")
        printWF(p)

        #test depolarizing noise
        noise.depolarizing_noise(p,0,0)
        print("0 dp noise")
        printWF(p)
        noise.depolarizing_noise(p,0,1)
        print("1 dp flip")
        printWF(p)
    
def printWF(program):
        wf_sim = WavefunctionSimulator()
        waveFunction = wf_sim.wavefunction(program)
        print(waveFunction)
    

qvm = QVMConnection()
program = Program()

#define agents
bob = Bob(program, qubits=[0,2])

#connect agents

#simulate agents
Simulation(bob).run()
results = qvm.run(program, trials=1)

#print initial states

print('Bob\'s results:', results)
print('Bob\'s time:', bob.time)

'''
# check instructions:
for inst in program.instructions:
    print(program.defined_gates)
    ry:
        print(inst.name)
    except:
        pass

'''
    


