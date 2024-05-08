[[/Module/Behavior/Learning]] -- Reinforcement learning behavior model

# Synopsis

GLM:

~~~
class learning 
{
	method target; // (REQUIRED) Target CLASS:PROPERTY or OBJECT.PROPERTY
	method policy; // (REQUIRED) Learning policy
	double exploration; // (REQUIRED) Exploration factor (1-exploitation factor)
	double interval[s]; // (REQUIRED) Interval of decision-making
	double discount; // Discount rate of future rewards (per interval)
	method reward; // (OUTPUT) Observed rewards for each state
}
~~~

# Description

The reinforcement `learning` model implements a learning mechanisms that is effective at modeling behavior where trade-offs between short-term and long-term rewards and regrets are important.

The agent's action selection is modeling as a map specified by the `policy`, e.g.,

$\pi : A \times S \to [0,1]$

$\pi(a,s) = \Pr(A_t=a|S_t=s)$

which gives the probability of taking the action $a$ when in the state $s$. The value of a state is defined as the expected discounted return when starting with the state $s$ and following the policy $\pi$.  This is roughly given by

$V_\pi(s) = \E[G|S_0=s] = \E\left[ \sum_{t=0}^\infty \gamma^t R_{t+1} | S_0=s \right]$

where the random variable $G$ is the discounted return of the rewards, and $R_{t+1}$ is the reward for transitioning from the state $S_t$ to $S_{t+1}$, and $0 \le \gamma \le 1$ is the discount rate for future rewards. Based on the theory of Markoc decision processes, the search is restricted to stationary deterministic policies, which selects actions based only on the current state.

The approach uses brute force, i.e., when exploration is selected each possible policy is sampled to determine the returns while following it, and when exploitation is selected the policy with the largest returns is chosen.

# Example

TODO

# See also

* [[/Module/Behavior]]
