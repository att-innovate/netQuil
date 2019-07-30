import sys
sys.path.insert(0, '/Users/zacespinosa/Foundry/qnetdes')
sys.path.insert(1, '/Users/matthewradzihovsky/documents/qnetdes')

from pyquil import Program
from pyquil.api import WavefunctionSimulator, QVMConnection
from pyquil.gates import *
from qnetdes import *

__all__ = ["cat_entangler", "cat_disentangler"]

def distributed_gate(agent):
    agent.using_distributed_gate = not agent.using_distributed_gate

def notify_entangler_is_done(caller, target_agents): 
    ''' 
    Target agents should be expecting a cbit signaling the distributed gate is complete
    '''
    for agent in target_agents:
        cbit = [1] # cbit signaling done
        caller.csend(agent.name, cbit)

def cat_entangler(control, targets, entangled=False, notify=False):
    '''
    Performs the cat entangler, one of two primitive operations for 
    distributed quantum computing which can be used to implement non-local operations.
    Projects the state of Alice's local control bit (phi) on entangled qubits owned by other Agents, 
    allowing Agents to effectively use Alice's qubit as a control for their own operations. Measurements
    are stored in ro in the position corresponding to qubit's index (i.e. ith qubit measured into ro[i]). 
    Once the cat_entangler is started in the control agent, each target agent waits until they have received
    two classical bits from the control. The first is a placeholder for a measurement and the second indicates that
    the cat entangler is complete. e.g. non-local CNOTs, non-local controlled gates, and teleportation.

    Remember, the cat_disentangler sends classical bits between the control and targets, so be careful 
    when trying to perform similar operations in parallel!

    :param (agent, int, int, classical register): Agent owning phi and measure qubit (which should be the same agent calling cat_entangler), phi, measurement qubit, and register to store measurements
    :param List<(agent, qubit)> targets: agent and agent's qubit that will be altered
    :param Boolean entangled: true if qubits from other Agents are already maximally entangled
    :param Boolean notify: if true control agent will send cbit equaling 1 to all target agents, signaling completion 
    '''
    agent, phi, measure_qubit, ro = control
    p = agent.program

    # Collect all qubits except control bit
    qubits = [measure_qubit] + [q[1] for q in targets]

    # Tell Tracer to Ignore Operations
    distributed_gate(agent)

    # If qubits are not already entangled, and distribute all non-control qubits
    if not entangled:
        p += H(measure_qubit)
        for i in range(len(qubits) - 1):
            q1 = qubits[i] 
            q2 = qubits[i+1]
            p += CNOT(q1, q2)
    
    # Project control qubit onto qubit and measure
    p += CNOT(phi, measure_qubit)
    p += MEASURE(measure_qubit, ro[measure_qubit]) 

    # Send result of qubit that has been measured to all other agents
    cbit = [1] # Hard code a placeholder value until ro is calculated
    for a in [t[0] for t in targets]:
        agent.csend(a.name, cbit)

    # Conditionally Perform Measure Operations 
    for q in qubits:
        p.if_then(ro[measure_qubit], X(q))

    # Tell Tracer We're Done
    distributed_gate(agent)
    if notify: notify_entangler_is_done(caller=agent, target_agents=[t[0] for t in targets])

def cat_disentangler(control, targets, notify=False):
    '''
    Performs the cat disentangler, second of two primitive operations for 
    distributed quantum computing which can be used to implement non-local operations.
    Restores all qubits to state before cat_entangler was performed. Measurements
    are stored in ro in the position corresponding to qubit's index (i.e ith qubit measured into ro[i])

    Remember, the cat_disentangler sends classical bits between the control and targets, so be careful 
    when trying to perform similar operations in parallel!

    :param (agent, int, classical register): Agent owning phi qubit, phi, and register to store measurments
    :param List<(agent, qubit)> targets: agent and agent's qubit that will be altered
    :param Boolean notify: if true control agent will send cbit equaling 1 to all target agents, signaling completion 
    '''
    agent, phi, ro = control
    p = agent.program

    # Tell Tracer to Ignore Operations
    distributed_gate(agent)

    # Perform Hadamard of each qubit
    for _, q in targets: p += H(q)

    # Measure target bits and execute bit-flip to restore to 0
    for a, q in targets: 
        p += MEASURE(q, ro[q])
        p.if_then(ro[q], X(q))

        # Send qubit measurement to owner of phi in order to perform XOR
        cbit = [1] # Hard code a placeholder value until ro[q] is calculated
        a.csend(agent.name, cbit)
        agent.crecv(a.name)

    # Perform XOR between all measured bits and if true perform Z rotation on phi.
    # This will restore its original state
    for i in range(len(targets) - 1, 0, -1):
        p += XOR(ro[targets[i-1][1]], ro[targets[i][1]])

    p.if_then(ro[targets[0][1]], Z(phi))

    # Tell Tracer We're Done
    distributed_gate(agent)
    if notify: notify_entangler_is_done(caller=agent, target_agents=[t[0] for t in targets])

    