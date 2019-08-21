.. _getting-started: 

=========================================================
Getting Started
=========================================================

Requirements
============
Pyquil 2.0, Python 3.6 or higher, and NumPy are requirements for netQuil. You will also need to download the Rigetti's QVM and Compiler as described on their
`Getting Started <http://docs.rigetti.com/en/stable/start.html>`_ page. 

Installation
============

To install using the Python package manager, pip:

.. code:: python

    pip install netquil
    
To install without pip:

.. code:: python

    easy_install netquil

To instead install netQuil from the source, clone the repository.
 
.. code:: python

    git clone https://github.com/att-innovate/netquil.git

Tutorial - Bell State Distribution
==================================
Lets start by building our first netQuil program that creates and distributes a bell state pair 
between Alice and Bob. In this tutorial you will be introduced to ``Agents`` (the nodes in your network), 
``QConnections`` and ``CConnections`` (the channels connecting nodes), and ``Devices`` (the customizable noise modules and error simulators).
Checkout our other demos to see more advanced examples of netQuil in action, and, for bold of you, review our whitepaper to learn about the state of 
distributed quantum protocols and netQuil. 

This tutorial assumes you have a basic understanding of quantum information theory
and the pyquil framework built on Quil. For a quick refresher, review this `resource <http://docs.rigetti.com/en/stable/intro.html>`_.

Import Dependencies
===================
Let's start by importing all of our dependencies. 

.. code-block:: python
    :linenos:

    from netquil import *
    from pyquil import Program
    from pyquil.gates import *
    
Define Agents
=============
Agents are nodes in our quantum network. Each Agent should extend the agent class and define
a ``run`` function, allowing that agent to run on its own thread. Agents can send and receive quantum and classical information, 
as well as define source and target devices that ingress and egress information must pass through, respectively. They also maintain local clocks 
that increment based on traffic and the delay that devices return, a network monitor recording their traffic, and a list of qubits and classical bits that
they manage.

All agents should share the same PyQuil program that they can modify to simulate network traffic.
The program can be explicitly attached to each agent if presimulation computations must be done, or 
be omitted to default to a blank program. 

.. code-block:: python
    :linenos: 
    
    from netquil import *
    from pyquil import Program
    from pyquil.gates import *

    class Alice(Agent):
        def run(self):
           a, b = self.qubits
           p = self.program

    class Bob(Agent):
        def run(self):
            pass
    
    alice = Alice(qubits=[0,1])
    bob = Bob()

Create the Run Function
=======================
An agent's run function should encapsulate all of the work that agent is responsible for. ``self.qubits`` returns the list of qubits that
an agent owns and may modify. ``self.program`` returns the global program shared between agents, and ``qsend(name, qubits)`` and ``qrecv(name)`` 
will send and receive qubits from one agent to another, respectively. 

.. code-block:: python
    :linenos:
    :lineno-start: 5
    
    class Alice(Agent):
        def run(self):
           a, b = self.qubits
           p = self.program

           # Create Bell State
           p += H(a)
           p += CNOT(a,b)

           # Send half of bell state to Bob
           self.qsend('bob', b)

    class Bob(Agent):
        def run(self):
            p = self.program

            # Receive half of bell state from Alice 
            b = self.qrecv('alice')

            # Measure qubits and run program
            p += Measure(b)

Connect the Agents
==================
``QConnect()`` will create a quantum channel between the given agents.
Without establishing this connection, agents have no way of communicating between each other. 
Similarly ``CConnect()`` will create a classical channel between the given agents. Both 
``QConnect()`` and ``CConnect()`` will create channels between all agents passed to them. On 
``QConnect()`` you may also specify ``transit_devices`` which all qubits will travel through when passed
between agents. 

.. code:: python
            
    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Connect alice and bob to quantum network
    QConnect(alice, bob)

Simulate the Network
====================
``Simulation(agents...)`` will start each agent on its own thread and call agents' ``run`` function. 
``Simulation().run`` will return a list of Quil programs, one for each trial (defaults to one trial), 
that can be executed on a qvm. 

.. code:: python
            
    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Create Quantum Channel between Alice and Bob
    QConnect(alice, bob)

    programs = Simulation(alice, bob).run()
    results = qvm.run(programs[0])
    print(results)

Next Steps
========== 
All together, your program should look something like this! 

.. code-block:: python
    :linenos:

    from netquil import *
    from pyquil import Program
    from pyquil.gates import *

    class Alice(Agent):
        def run(self):
           a, b = self.qubits
           p = self.program

           # Create Bell State
           p += H(a)
           p += CNOT(a,b)

           # Send half of bell state to Bob
           self.qsend('bob', b)

    class Bob(Agent):
        def run(self):
            p = self.program

            # Receive half of bell state from Alice 
            b = self.qrecv('alice')

            # Measure qubits and run program
            p += Measure(b)

    alice = Alice(qubits=[0,1])
    bob = Bob()

    # Connect alice and bob to quantum network
    QConnect(alice, bob)

    programs = Simulation(alice, bob).run()
    results = qvm.run(programs[0])
    print(results)

Congratulations! You now have a working netQuil program that creates and distributes a bell state pair between Alice and Bob. 

Explore our :ref:`advanced usage <advanced-usage>` demo to learn about netQuil's error module for quantum noise and transit, source and target devices, 
as well as how to run multiple trials and syncronize agents. 

Read the :ref:`distributed protocol <distributed-protocol>` demo to see how the cat-entangler and cat-disentangler can be used to implement non-local CNOTs, 
non-local controlled gates, and teleportation. 

Or, just for fun, checkout the :ref:`middle-man attack <middle-man>`, :ref:`teleportation <quantum-teleportation>`, 
or :ref:`superdense coding <superdense-coding>` demos to learn about common quantum networking protocols.