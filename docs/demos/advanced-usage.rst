
.. _advanced-usage:

=========================================================
Advanced Usage and Features
=========================================================

In this demo we will be reviewing netQuil's advanced features that make it a 
powerful and extensible platform for quantum networking simulation. Lets start with its built-in and
custom devices.

Built-in and Custom Devices
===========================
A device is a codified, single piece of hardware in your network. 
In classical networking this would include devices such as a router, modem, repeater, 
and network switch. In quantum networking think fiber optics, intensity modulators, lasers or 
photon sources, and `SNSPDs <https://en.wikipedia.org/wiki/Superconducting_nanowire_single-photon_detector>`_ or detectors. 
Associated with each device in a quantum network is its physical effect on qubits and the time it takes 
qubits to pass through the device.

There are three types of devices in netQuil: source, transit, and target devices. Source and target devices
are associated with an agent, while transit devices are associated with instances of ``QConnection``. When a qubit
leaves Alice and travels to Bob, the qubit originates from Alice's source devices, travels through the
transit devices attached to their ``QConnection`` and ends by arriving through Bob's target devices. The
order in which a qubit passes through each device corresponds to the order in which those devices
were added to either the agent or connection.  

NetQuil's devices module allows you to choose from a number of built-in source, transit, and target
devices. 

Built-in Devices
================
``Laser`` is a built-in noisy photon source that generates photons according to ``expected_photons`` and a poisson 
distribution. If ``network_monitor=True`` the laser will output its noise to signal ratio after each trial. 
You can create a custom ``get_results`` function that prints information about the device after each trial. 
The ``Laser`` will also return a delay equal to the photon pulse length. 

``Fiber`` is a built-in noisy fiber optical wire simulator and an example of a transit device. Fibers
have an associated length in kilometers and an attenuation coefficient. The attenuation coefficient is 
proportional to the probability that a photon is lost while traveling within the fiber (i.e. the photon is measured, 
and the measured value is inaccessible by any agent). In netQuil, if a qubit is lost due to attenuation, the 
target will receive the negative index of the qubit lost. For example, if Alice sends qubit 3 and it is
lost due to attenuation, Bob will receive -3, and neither Alice nor Bob will be able to operate with
qubit 3. If the qubit lost is 0 then the value will be set to -inf. Remember that when we send qubits between agents
we are sending the index of the qubit in the program and not the true qubit. 

Here is an example of a very simple program using the ``Laser`` and ``Fiber`` devices. 

.. code-block:: python
    :linenos:

    class Alice(Agent):
        def run(self):
            p = self.program
            for q in self.qubits:
                p += H(q)
                p += X(q)
                self.qsend('Bob', [q])

    class Bob(Agent):
        def run(self):
            p = self.program
            for i in range(3):
                q = self.qrecv(alice.name)[0]

                # Check if qubit is lost
                if q >= 0:
                    p += MEASURE(q, ro[q])

    p = Program()
    ro = p.declare('ro', 'BIT', 3)

    alice = Alice(p, qubits=[0,1,2])
    bob = Bob(p)

    # Define source device
    laser = Laser(rotation_prob_variance=.9)
    alice.add_source_devices([laser])

    # Define transit device and connection
    fiber = Fiber(length=5, attenuation_coefficient=-.90)
    QConnect(alice, bob, transit_devices=[fiber])

    # Run simulation
    Simulation(alice, bob).run()

    # Run program
    qvm = QVMConnection()
    results = qvm.run(p)
    print(results) 

Custom Devices
==============
Moreover, you can build your own custom devices by extending the ``Device`` class. All devices must have
an ``apply`` function that is responsible for the device's activity. The ``run`` function must return a 
dictionary that optionally contains the lost qubits and delay. The delay represents the time it took qubits to 
travel through the device. Remember, if qubits are lost while passing through the device, return an entry in the dictionary 
``lost_qubits: [lost qubits]``.

Most devices can be arbitrarily complex in their design and can depend on environmental factors such 
as temperature, humidity, or pressure. Custom devices allow us to simulate these arbitrarily complex devices.
As an example, we will create a simple custom fiber that changes the polarization of a photon by some random angle 
from a normal distribution.

.. code-block:: python
    :linenos:

    class Simple_Fiber(Device):
        def __init__(self, length, fiber_quality, rotation_std):
            self.fiber_quality = fiber_quality
            self.length = length
            self.rotation_std = rotation_std
            self.signal_speed = 2.998 * 10 ** 5 #speed of light in km/s

        def apply(self, program, qubits):
            for qubit in qubits:
                if np.random.rand() > self.fiber_quality:
                    rotation_angle = np.random.normal(0, self.rotation_std)
                    program += RX(rotation_angle, qubit)

            delay = self.length/self.signal_speed

            return {
                'delay': delay,
            }

    class Alice(Agent):
        def run(self):
            p = self.program
            for q in self.qubits:
                p += H(q)
                p += X(q)
                self.qsend('Bob', [q])

    class Bob(Agent):
        def run(self):
            p = self.program
            for _ in range(3):
                q = self.qrecv(alice.name)[0]
                p += MEASURE(q, ro[q])

    p = Program()
    ro = p.declare('ro', 'BIT', 3)

    alice = Alice(p, qubits=[0,1,2])
    bob = Bob(p)

    # Define source device
    laser = Laser(rotation_prob_variance=.9)
    alice.add_source_devices([laser])

    fiber = Simple_Fiber(length=10, fiber_quality=.6, rotation_std=5)
    QConnect(alice, bob, transit_devices=[fiber])

    Simulation(alice, bob).run(network_monitor=True)

    qvm = QVMConnection()
    results = qvm.run(p)
    print(results)

NetQuil also has a built-in noise module for performing common qubit operations such as normal 
unitary rotations, depolarization, and bit and phase flips.

Trials and Time
===============
In some situations, pyQuil programs generated between trials will be different depending 
on noise or the dynamic nature of your network. In order to accomodate this, ``Simulation().run()`` will always return a list of 
programs (i.e. one program per trial) that can be run on your qvm or qpu. Pass the number of trials you would like to run
into ``Simulation().run(trials=5)``, as well as a list containing the class of each agent being run. Do `NOT` forget to 
pass ``agent_classes`` (``Simulation(alice, bob).run(trials=5, agent_classes=[Alice, Bob]``), since this
is required in order to reset the agents between trials. 

You can also pass ``network_monitor=True`` to ``run`` in order to see a list of transactions on the network, the time of each transaction, 
and information about your devices. In addition to individual agent clocks, a master clock is running throughout the network
simulation that can be accessed through ``agent.get_master_time()`` on any agent. If you are implementing 
`time-bin encoding <https://en.wikipedia.org/wiki/Time-bin_encoding>`_ or one of its variation, we encourage you to 
experiment with the master and agent clocks. 

.. code-block:: python
    :linenos:

    class Simple_Fiber(Device): 
        def __init__(self, length, fiber_quality, rotation_std):
        self.fiber_quality = fiber_quality
        self.length = length
        self.rotation_std = rotation_std
        self.signal_speed = 2.998 * 10 ** 5 #speed of light in km/s

        def apply(self, program, qubits):
            for qubit in qubits: 
                # Apply noise
                if np.random.rand() > self.fiber_quality:
                    rotation_angle = np.random.normal(0, self.rotation_std)
                    program += RX(rotation_angle, qubit)

            delay = self.length/self.signal_speed

            return {
                'delay': delay,
            }

    class Alice(Agent):
        def run(self):
            p = self.program
            for q in self.qubits:
                p += H(q)
                p += X(q)
                self.qsend('Bob', [q])

    class Bob(Agent):
        def run(self):
            p = self.program
            for _ in range(3): 
                q = self.qrecv(alice.name)[0]

                # Check if qubit is lost
                if q >= 0: 
                    p += MEASURE(q, ro[q])

    p = Program()
    ro = p.declare('ro', 'BIT', 3)

    alice = Alice(p, qubits=[0,1,2])
    bob = Bob(p)

    # Define source device
    laser = Laser(rotation_prob_variance=.9) 
    alice.add_source_devices([laser])

    # Define transit devices and connection
    custom_fiber = Simple_Fiber(length=5, fiber_quality=.6, rotation_std=5)
    fiber = Fiber(length=5, attenuation_coefficient=-.20) 
    QConnect(alice, bob, transit_devices=[fiber, custom_fiber])

    # Run simulation
    programs = Simulation(alice, bob).run(trials=5, agent_classes=[Alice, Bob]) 

    # Run programs
    qvm = QVMConnection()
    for idx, program in enumerate(programs): 
        results = qvm.run(program)
        print('Program {}: '.format(idx), results)

Looking Forward
===============
In this demo we introduced netQuil's built-in and custom devices, noise module, multiple trials, and network monitor.
As you can see, netQuil is a powerful quantum networking simulator due to its extensibility, but it is also an active project.
If you find a bug open an issue or, better yet, a PR! 