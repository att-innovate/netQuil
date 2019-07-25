.. _getting-started: 

=========================================================
Getting Started
=========================================================

Requirements
============
Pyquil 2.0, Python 3.6 or higher, and NumPy are requirements for NetQuil. NetQuil also uses version 4.32 of `tqdm <https://github.com/tqdm/tqdm>`_
as part of its network monitor to provide real-time insights into all of your quantum networking experiments. This feature, however, is optional and can be
disabled.

Installation
============

To install NetQuil using Anaconda (recommended): 

.. code:: python

    conda install netquil
    
To install using the Python package manager, pip:

.. code:: python

    pip install netquil
    
To install without pip:

.. code:: python

    easy_install netquil

To instead install NetQuil from the source, clone the repository.
 
.. code:: python

    git clone https://github.com/att-innovate/netquil.git

Tutorial - Bell State Distribution
==================================
Lets start by building our first NetQuil program that creates and distributes a bell state pair 
between Alice and Bob. In this tutorial you will be introduced to ``Agents`` (the nodes in your network), 
``QConnections`` and ``CConnections`` (the channels connecting nodes), and ``Devices`` (the customizable noise modules and error simulators).
Checkout our other demos to see more advanced examples of NetQuil in action, and, for the more bold of you, review our whitepaper and codebase on Distributed Shor's Algorithm using NetQuil.  

This tutorial assumes you have a basic understanding of quantum information theory
and the pyquil framework built on Quil. For a quick refresher, review this `resource <http://docs.rigetti.com/en/stable/intro.html>`_.

Import Dependencies
===================
Let's start by importing all of our dependencies. 

.. code-block:: python
    :linenos:

    from pyquil import Program
    from pyquil.gates import *
    from netquil import *
    
Define Agents
=============
Agents are nodes in our quantum network. Each Agent should extend the agent class and define
a ``run`` function, allowing that Agent to run on its own thread. Agents can send and receive quantum and classical information, 
as well as define source and target devices that ingress and egress information must pass through. They also maintain local clocks 
that increment based on traffic, a network monitor recording their traffic, and a list of qubits and classical bits that
they manage.

All Agents should share the same PyQuil program that they can modify to simulate network traffic.
The program can be explicitly attached to each Agent if presimulation computations must be done, or 
be omitted as set default.

.. code-block:: python
    :linenos: 
    
    from pyquil import Program
    from pyquil.gates import *
    from netquil import *

    class Alice(Agent):
        def run(self):
           a, b = self.get_qubits() 
           p = self.get_program()

    class Bob(Agent):
        def run(self):
            pass
    
    alice = Alice(qubits=[0,1])
    bob = Bob()

Create the Run Function
=======================
An Agent's run function should encapsulate all of the work that Agent is responsible for. ``get_qubits`` returns the list of qubits that
an Agent owns and may modify. ``get_program`` returns the global program shared between Agents, and ``qsend(name, qubits)`` and ``qrecv(name)`` 
will send and receive qubits from one agent to another, respectively. 

.. code-block:: python
    :linenos:
    :lineno-start: 5
    
    class Alice(Agent):
        def run(self):
           a, b = self.get_qubits() 
           p = self.get_program()

           # Create Bell State
           p += H(a)
           p += CNOT(a,b)

           # Send half of bell state to Bob
           qsend('bob', b)

    class Bob(Agent):
        def run(self):
            p = self.get_program()

            # Receive half of bell state from Alice 
            b = qrecv('alice')

            # Measure qubits and run program
            p += Measure(b)
            r = qvm.run(p)
            print(r) 

Connect the Agents
==================
``QConnect(agent)`` will create both an ingress and egress quantum channel between the given agents. 
Without establishing this connection, agents have no way of communicating between each other. 
Similarly ``CConnect(agent)`` will create both an ingress and egress classical channel between the given agents. 

.. code:: python
            
    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Connect alice and bob to quantum network
    QConnect(alice, bob)

Simulate the Network
====================
``Simulation(agents...)`` will start each agent on its own thread and call Agents' ```run``` function. 

.. code:: python
            
    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Create Quantum Channel between Alice and Bob
    QConnect(alice, bob)

    Simulation(alice, bob).run()

Next Steps
========== 
All together, your program should look something like this! 

.. code-block:: python
    :linenos:

    from pyquil import Program
    from pyquil.gates import *
    from netquil import *

    class Alice(Agent):
        def run(self):
           a, b = self.get_qubits() 
           p = self.get_program()

           # Create Bell State
           p += H(a)
           p += CNOT(a,b)

           # Send half of bell state to Bob
           qsend('bob', b)

    class Bob(Agent):
        def run(self):
            p = self.get_program()

            # Receive half of bell state from Alice 
            b = qrecv('alice')

            # Measure qubits and run program
            p += Measure(b)
            r = qvm.run(p)
            print(r)

    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Connect alice and bob to quantum network
    QConnect(alice, bob)

    Simulation(alice, bob).run()

Congratulations! You now have your first working NetQuil program that creates and distributes a Bell State pair between Alice 
and Bob. Explore our advanced demos to learn to use NetQuil's error module for quantum noise. 
Checkout our API reference to see how our network monitor for real time traffic managing, master clock
for syncronizing agents, and multi-trial experiments works. Or dive into our whitepaper on Distributed
Shor's Algorithm with NetQuil to see NetQuil's distributed gates module in action.