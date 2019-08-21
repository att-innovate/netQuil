# Quantum Networking Devices and Errors Simulator

NetQuil is an open-source Python framework designed specifically for simulating quantum networks and distributed quantum protocol. Built on the already extensive quantum computing framework [pyQuil](https://github.com/rigetti/pyquil), by [Rigetti Computing](https://www.rigetti.com/), netQuil is perfect for extending your current quantum computing experiments and testing ideas in quantum network topology and distributed quantum protocol. NetQuil offers an extensible device simulator, quantum and classical noise modules, and a performant multi-threaded simulation manager. It also allows you to run multiple trials across your network, syncronize agents based on local and master clocks, and review traffic in real time with a network monitor. NetQuil is also optimized for distributed quantum protocol with its implementation of the primitive cat-entangler and cat-disentangler introduced by [Yimsiriwattana Lomonaco](https://arxiv.org/abs/quant-ph/0402148). This primitive protocols can be used to implement non-local CNOTs, non-local controlled gates, and teleportation, and should be the backbone of any distributed quantum protocol you create.

NetQuil is a project by AT&T Foundry. NetQuil is a work in progress and contributions are encouraged.

## Documentation
Explore netQuil's [documentation center](https://att-innovate.github.io/netQuil/index.html) learn more about the framework and its use cases. If you are interested in learning about the state of distributed quantum computing (DQC) and netQuil's role as a framework in the field read the [whitepaper](https://github.com/att-innovate/netQuil), "netQuil: A quantum playground for distributed quantum computing simulations". 

## Installation
You can install netQuil directly using `pip`: 

```
pip install netquil
```

## netQuil Design
![Overview of netQuil framework structure](https://github.com/att-innovate/netQuil/blob/gh-pages/_images/layout.png)

## Demos
Checkout netQuil in action in the [demos](https://github.com/att-innovate/netQuil/tree/master/demos) folder and at the [documentation center](https://att-innovate.github.io/netQuil/index.html): 

### Quantum Teleportation

As a simple demonstration of netQuil, let's imagine a scenario where Alice wants to send Bob the quantum state of an arbitrary qubit she possesses. 
Since Alice does not know the state of the qubit, and she cannot measure it, because measuring it would cause the state to collapse, Alice decides to use [quantum 
teleportation](https://en.wikipedia.org/wiki/Quantum_teleportation).

![Quantum Teleportation Circuit](https://raw.githubusercontent.com/att-innovate/netQuil/blob/gh-pages/_images/teleportation.png)

- Charlie creates a bell state pair and sends one qubit to Alice and the other to Bob.
- Alice receives Charlie's qubit. Alice projects her arbitrary quantum state onto qubit A using a CNOT and Hadamard gate. 
- Alice measures her qubits and classically sends the results to Bob. As a result of the measurements Bob's state collapses to one of the four Bell States. 
- Bob recreate's Alice's arbitrary state based on Alice's measurements, namely applying a Pauli-X (X) gate if Alice's bell state pair is 1 and applying a Pauli-Z (Z) gate if the arbitrary state is measured to be 1. 

We can implement quantum teleportation using netQuil in the following manner: 
```
from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *

def printWF(p):
    '''
    Prints the wavefunction from simulating a program p
    '''
    wf_sim = WavefunctionSimulator()
    waveFunction = wf_sim.wavefunction(p)
    print(waveFunction)
    

class Charlie(Agent):
    '''
    Charlie sends Bell pairs to Alice and Bob
    '''
    def run(self):

        # Create Bell State Pair
        p = self.program
        p += H(0)
        p += CNOT(0,1)

        self.qsend(alice.name, [0])
        self.qsend(bob.name, [1])

class Alice(Agent): 
    '''
    Alice projects her state on her Bell State Pair from Charlie
    '''
    def run(self): 
        p = self.program

        # Define Alice's Qubits
        phi = self.qubits[0]
        qubitsCharlie = self.qrecv(charlie.name)
        a = qubitsCharlie[0]

        # Entangle Ancilla and Phi
        p += CNOT(phi, a)
        p += H(phi)

        # Measure Ancilla and Phi
        p += MEASURE(a, ro[0])
        p += MEASURE(phi, ro[1])
    

class Bob(Agent): 
    '''
    Bob recreates Alice's state based on her measurements
    '''
    def run(self):
        p = self.program

        # Define Bob's qubits
        qubitsCharlie = self.qrecv(charlie.name)
        b = qubitsCharlie[0]

        # Prepare State Based on Measurements
        p.if_then(ro[0], X(b))
        p.if_then(ro[1], Z(b))


p = Program()

# Prepare psi
p += H(2)
p += Z(2)
p += RZ(1.2, 2)
print("Initial Alice State: ")
printWF(p)

# Create Classical Memory
ro = p.declare('ro', 'BIT', 3)

# Create Alice, Bob, and Charlie. Give Alice qubit 2 (phi). Give Charlie qubits [0,1] (Bell State Pairs). 
alice = Alice(p, qubits=[2], name='alice')
bob = Bob(p, name='bob')
charlie = Charlie(p, qubits=[0,1], name='charlie')

# Connect agents to distribute qubits and report results
QConnect(alice, charlie, bob)
CConnect(alice, bob)

# Run simulation
Simulation(alice, bob, charlie).run(trials=1, agent_classes=[Alice, Bob, Charlie])
qvm = QVMConnection()
qvm.run(p)
print("Final Bob's State: ")
printWF(p)
```