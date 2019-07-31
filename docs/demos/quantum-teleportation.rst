.. _quantum-teleportation: 

=========================================================
Quantum Teleportation
=========================================================

Quantum teleportation, or "spooky action at a distance" as denoted by Einstein,
is a method to deliver any arbitrary quantum state, :math:`|\psi\rangle`,
between agents only using classical communication channels. This protocol allows Alice to deliver
an unknown qubit state, :math:`|\psi\rangle`, to Bob using a shared bell state pair. 

This protocol enables quantum computers to interact as a network in sharing arbitrary quantum states. 
Note that due to the requirement of classical communication, this protocol does not validate faster-than-light
communication. Quantum teleporatation transports a quantum state by sending two classical bits, and thus is the inverse
of :ref:`superdense coding <superdense-coding>`.

Protocol
=========================================================
Quantum teleportation involves 3 agents, Alice, Bob, and Charlie. Charlie prepares the bell state pair and distributes
the entangled qubits to Alice and Bob. Alice entangles her qubit :math:`|\psi\rangle` with her bell state pair from Charlie, 
and then measures her qubits. Finally, based on these measurements, Bob can recreate Alice's qubit
:math:`|\psi\rangle` by operating using :math:`\textbf{X}` and :math:`\textbf{Z}` gates. 

Steps 
----------------------------------------
1. Charlie creates Bell State Pair using a Hadamard (:math:`\textbf{H}`) and Controlled-Not (:math:`\textbf{CNOT}`) gate,
:math:`|AB\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle) `, sending qubit :math:`A` to Alice and qubit :math:`B` to Bob. 

2. Alice projects her arbitrary quantum state :math:`|\psi\rangle = \alpha |0\rangle + \beta |1\rangle` onto qubit :math:`A` using a Controlled-Not (:math:`\textbf{CNOT}`) and 
a Hadamard (:math:`\textbf{H}`) gate. 
The 3-qubit quantum system, :math:`|\psi A B\rangle`, is in state: 
:math:`\frac{1}{2}[|00\rangle (\alpha |0\rangle + \beta |1\rangle) + |01\rangle (\alpha |1\rangle + \beta |0\rangle)`
:math:`+ |10\rangle (\alpha |0\rangle - \beta |1\rangle) + |11\rangle (\alpha |1\rangle - \beta |0\rangle)]`

3. Alice measures :math:`|\psi\rangle` and :math:`A` and classically sends the results to Bob. Bob's state collapses to 
one of the four Bell States.

4. Bob recreate's :math:`|\psi\rangle` based on Alice's measurements, namely applying a Pauli-X (:math:`\textbf{X}`) gate if 
:math:`A` is measured to be :math:`|1\rangle` and applying a Pauli-Z (:math:`\textbf{Z}`) gate if :math:`\psi` is measured to
be :math:`|1\rangle`. Bob's qubit :math:`B` is now in state :math:`|\psi\rangle = \alpha |0\rangle + \beta |1\rangle`.

Tutorial
=========================================================
We will now implement quantum teleportation using NetQuil's framework of ref:`Agent <agent>` and ref:`Connections <connections>`
to simulate teleportation of a quantum state using a quantum network. The ref:`Devices <devices>` module 
and ref'Noise <noise>' allows you to include realistic devices with noise in your quantum network.

Import Dependencies 
----------------------------------------
.. code:: python

    from pyquil import Program
    from pyquil.api import QVMConnection
    from pyquil.gates import *
    from netQuil import *

Setup Agents 
----------------------------------------
Let us first define Agent Charlie who creates and distributes the Bell State Pair to Alice and Bob. We can extend the Agent
classes and redefine our :math:`\textit{run()}` methods. To create our Bell State Pair, he can use a
Hadamard (:math:`\textbf{H}`) and Controlled-Not (:math:`\textbf{CNOT}`) gate from pyquil. Then,
using NetQuil, we want to send each qubit to Alice and Bob.

.. code:: python

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

Now, we will create Agent Alice and Agent Bob. Alice will project her state :math:`|\psi\rangle = \alpha |0\rangle + \beta |1\rangle` onto her 
Bell State Pair. Then, she will measure her two qubits, and send the results to Bob, which Bob will use to recreate Alice's original state
:math:`|\psi\rangle = \alpha |0\rangle + \beta |1\rangle` with his Bell State Pair.

.. code:: python

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

Create Program
----------------------------------------
We can now define our pyquil program to pass into each agent. For this demo, we will let qubit 2 be our state :math:`|\psi\rangle`, 
prepared using a Hadamard. Therefore, Alice has state :math:`|\psi\rangle = |2\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)`. 


.. code:: python

    p = Program()
    p += H(2)

    # Create Classical Memory
    ro = p.declare('ro', 'BIT', 3)


Simulate Network
----------------------------------------
Finally, we can define our agents, connect them, and simulate our program. Notice, that initially Charlie has qubits 0 and 1, 
in order to make the Bell State Pair, while Alice has qubit 2, representing state :math:`|\psi\rangle`. 

.. code:: python

    # Create Alice, Bob, and Charlie. Give Alice qubit 2 (phi). Give Charlie qubits [0,1] (Bell State Pairs). 
    alice = Alice(p, qubits=[2], name='alice')
    bob = Bob(p, name='bob')
    charlie = Charlie(p, qubits=[0,1], name='charlie')

    # Connect agents to distribute qubits and report results
    QConnect(alice, charlie)
    QConnect(bob, charlie)
    QConnect(alice, bob)
    CConnect(alice, bob)

    # Run simulation
    Simulation(alice, bob, charlie).run(trials=1, agent_classes=[Alice, Bob, Charlie])
    qvm = QVMConnection()
    qvm.run(p)


Check Results
----------------------------------------
We can check if our state was teleported without a quantum channel by using pyquil's WaveFunctionSimulator as follows.

.. code:: python

    from pyquil.api import WavefunctionSimulator

    def printWF(p):
        '''
        Prints the wavefunction from simulating a program p
        '''
        wf_sim = WavefunctionSimulator()
        waveFunction = wf_sim.wavefunction(p)
        print(waveFunction)

    printWF(p) 


Extend Simulation
----------------------------------------
You have now created a program to simulate quantum teleportation! You can now teleport a quantum state only using
a classical channel quantum bit. It is now time to get creative. Add noise, add extra agents, or add a complicated initial state.

Source Code
=========================================================
The source code for this demo is included in the demos directory of the NetQuil repository.

