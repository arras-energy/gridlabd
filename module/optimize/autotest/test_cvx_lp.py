from cvxpy import Parameter,Variable,Minimize,Problem
from numpy import array,random,maximum

A=array([[-1.63889162,  0.67050154],
       [ 0.95878413, -0.77257773],
       [-0.34031999,  0.14162186]])
A = Parameter(shape=A.shape,value=A,name='A')
x = Variable(2,name='x')
s0 = random.randn(A.shape[0]) # make the problem non-trival
lamb0 = maximum(-s0,0)
s0 = maximum(s0,0)
x0 = random.randn(A.shape[1])
b = A @ x0 + s0
c = -A.T @ lamb0

A.value=array([[-1.63889162,  0.67050154],
       [ 0.95878413, -0.77257773],
       [-0.34031999,  0.14162186]])

objective = Minimize(c.T@x)
constraints = [A@x<=b]
problem = Problem(objective,constraints)
result = problem.solve()
assert abs(result-(c.T@x).value) < 1e-6, "incorrect result"

A.value=array([[ 0.96762019,  1.79056869],
       [ 0.37556373, -0.06711015],
       [-1.23913575,  0.72500816]])
s0 = random.randn(A.shape[0]) # make the problem non-trival
lamb0 = maximum(-s0,0)
s0 = maximum(s0,0)
x0 = random.randn(A.shape[1])
b = A @ x0 + s0
c = -A.T @ lamb0

result = problem.solve()
assert abs(result-(c.T@x).value) < 1e-6, "incorrect result"
