.. _getting-started: 

=========================================================
Getting Started
=========================================================

Requirements
============
NetQuil requires Pyquil 2.0, Python 3.6 or higher, and NumPy. NetQuil also uses version 4.32 of `tqdm <https://github.com/tqdm/tqdm>`_
as part of network monitor to provide real-time insights into quantum networking experiments. However, this feature is optional and can be
turned off accordig to the api-reference (TODO: insert link).

Installation
============

To install NetQuil using Anaconda (recommended): 

.. code:: python

    conda install netquil
    
To install using the Python package manager pip: 

.. code:: python

    pip install netquil
    
or without pip:

.. code:: python

    easy_install netquil

To instead install NetQuil from the source, clone this repository.
 
.. code:: python

    git clone https://github.com/att-innovate/netquil.git

Tutorial - Bell State Distribution
==================================
Lets start by building our first NetQuil program that creates and distributes a bell state pair 
between Alice and Bob. In this tutorial you will be introduced to ``Agents`` (the nodes in our network) and their operations, 
``QConnections`` and ``CConnections`` (the channels connecting nodes), and ``Devices`` (the customizable noise modules and error simulators).
Checkout our demos to see more advance examples NetQuil in action, and, for the more bold you, review our whitepaper and codebase on
implementing Distributed Shor's Algorithm using NetQuil.  

This tutorial assumes you have a basic understanding of quantum information theory
and the pyquil framework built on Quil. For a quick refresher, checkout `this <http://docs.rigetti.com/en/stable/intro.html>`_ resource.

Import Dependencies 
----------------------------------------
.. code:: python

    from pyquil import Program
    from pyquil.gates import *
    from netquil import *
    
Define Agents
-------------
Agents are nodes in our quantum network. Each Agent should extend the agent class and defined
a ``run`` function, allowing that Agent to run on its own thread. Agents are able to perform a variety
of operations. For example, they can send and receive quantum and classical information and define source and 
target devices that information too or from them must pass through. They also maintain local clocks that increment
based on traffic, a network monitor recording their traffic, and a list of qubits and classical bits that
they manage. 

All Agents should share the same PyQuil program that they will then modify to simulate network traffic.
The program can be explicitly attached to each Agent if presimulation computations must be done. 
Otherwise, all Agents by default are set to share a blank global quil program.

.. code:: python
    
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
-----------------------
``get_qubits`` returns the list of qubits that that Agent manages. Agents may not edits qubits that they do 
not own. ``get_program`` returns the global program shared between Agents. ``q_send(name, qubits)`` will send qubits
from one agent to another. 

.. code:: python
    
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
            self.log_results(r) 

Connect the Agents
------------------
.. code:: python
            
    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Create Quantum Channel between Alice and Bob
    QConnect(alice, bob)

Simulate the Network
--------------------
.. code:: python
            
    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Create Quantum Channel between Alice and Bob
    QConnect(alice, bob)

    Simulation(alice, bob).run()

Extend Simulation
----------------- 

introduce Noise, turn on network monitor, record time, multiple trials