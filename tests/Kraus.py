
import matplotlib.pyplot as plt
from pyquil import get_qc, Program
from pyquil.gates import MEASURE
import numpy as np
from pyquil.api import QVMConnection


def kraus_ops_bit_flip(prob):
    # define flip (X) and not flip (I) Kraus operators
    I_ = np.sqrt(1 - prob) * np.array([[1, 0], [0, 1]])
    X_ = np.sqrt(prob) * np.array([[0, 1], [1, 0]])
    return [I_, X_]

def random_unitary(n):
    # draw complex matrix from Ginibre ensemble
    z = np.random.randn(n, n) + 1j * np.random.randn(n, n)
    # QR decompose this complex matrix
    q, r = np.linalg.qr(z)
    # make this decomposition unique
    d = np.diagonal(r)
    l = np.diag(d) / np.abs(d)
    return np.array([[1, 0], [0, 1]])

# pick probability
prob = 0.2
# noisy program
p = Program()
p.defgate("DummyGate", random_unitary(2))
p += ("DummyGate", 0)
p.define_noisy_gate("DummyGate", [0], kraus_ops_bit_flip(prob))
ro = p.declare('ro')
p += MEASURE(0, ro)

#qc = get_qc('1q-qvm')
qvm = QVMConnection()

num_expts = 1000
num_shots = 1000

p.wrap_in_numshots_loop(num_shots)


results = qvm.run(p, trials = 1000)

    
plt.figure(figsize=(10, 8))
plt.hist(results, bins=50)
plt.show()