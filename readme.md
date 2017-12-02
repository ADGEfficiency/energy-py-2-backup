## energy_py v2.0

**energy_py is reinforcement learning for energy systems.**

Using reinforcement learning agents to control virtual energy environments is the first step towards using reinforcement learning to optimize real world energy systems.

energy_py supports this goal by providing a **collection of reinforcement learning agents, energy environments and tools to run experiments.**

energy_py is built and maintained by Adam Green - [adam.green@adgefficiency.com](adam.green@adgefficiency.com).  

This project is in rapid development - if you would like to get involved send
me an email.

I write about energy & machine learning at [adgefficiency.com](http://adgefficiency.com/).  

I teach a one day [introduction to reinforcement learning learning](https://github.com/ADGEfficiency/DSR_RL) class at [Data Science Retreat](https://www.datascienceretreat.com/).

### Basic usage
Below I run experiments using two different agents and the battery
environment.

```
from energy_py.experiments import random_experiment, reinforce_experiment
from energy_py.envs import BatteryEnv

#  select the location of your raw_state.csv
data_path = os.getcwd()

env = BatteryEnv

random_outputs = random_experiment(env, 
                                   data_path=data_path,
                                   base_path='random/expt_1')

dqn_outputs = dqn_experiment(env,
                             data_path=data_path,
                             base_path='dqn/expt_2')
```

### Installation
Below I use Anaconda to create a Python 3.5 virtual environment.  You can of course use your own environment manager.

If you just want to install to your system Python you can skip to cloning the repo.  
```
conda create --name energy_py python=3.5.2
```
Activate the virtual environment
```
activate energy_py (windows)

source activate energy_py (unix)
```
Clone the repo somewhere
```
git clone https://github.com/ADGEfficiency/energy_py.git
```
Move into the energy_py folder and install using setup.py.  This will install energy_py into your activated Python environment
```
cd energy_py
python setup.py install
```
Finally install the required packages
```
pip install requirements.txt
```
The main dependencies of energy_py are numpy, pandas, Keras & TensorFlow (GPU).  

energy_py was built using Keras 2.0.8 & TensorFlow 1.3.0.  

### Project structure

Many classes inherit from the [Utils](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/scripts/utils.py) class, which contains useful generic functionality.  many methods are static - which makes me think that perhaps just importing functions may
be better than inheriting from the Utils class.  

Environments are created by inheriting from the [BaseEnv](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/envs/env_core.py) class.  All of the environments implemented so far are children of the [TimeSeriesEnv](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/envs/env_ts.py) class.  Likely in the future that I will merge BaseEnv and TimeSeriesEnv into one class.  

Agents are created by inheriting from the [BaseAgent](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/agents/agent_core.py) class.  Another key object is the [AgentMemory](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/agents/memory.py) which holds and processes agent experience.  

**Environments**

Agent and environment interaction is shown below - it follows the standard
Open AI gym API for environments i.e. .reset, .step(action).

```
from energy_py.agents import DQN, KerasQ
from energy_py.envs import BatteryEnv

env = BatteryEnv()

agent = DQN(env,
            discount=0.9,
            Q=KerasQ,          
            batch_size=64,
            brain_path='/brain',
            total_steps=1000)

obs = env.reset()
action = agent.act(observation=obs)
next_obs, reward, done, info = env.step(action)
agent.memory.add_experience(obs, action, reward, next_obs, step, episode)

```
The following environments are implemented:

- [Electricity storage in a battery](https://github.com/ADGEfficiency/energy_py/tree/master/energy_py/envs/battery)

- [Generic flexibility action environment](https://github.com/ADGEfficiency/energy_py/tree/master/energy_py/envs/flex)

- [Cooling flexibility action - in development](https://github.com/ADGEfficiency/energy_py/tree/master/energy_py/envs/precool) 

In energy_py v1.0 I implemented a combined heat and power plant - not planning
on introducing this into energy_py v2.0.

**Agents**

The following agents are currently implemented:

- [Random agent](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/agents/random_agent.py)

- [Naive battery agent](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/agents/naive/naive_battery.py)

- [REINFORCE aka Monte Carlo policy gradient - based on TensorFlow function approximators](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/agents/policy_based/reinforce.py)

- [DQN aka Q-Learning with experience replay and target network - Keras function approximators](https://github.com/ADGEfficiency/energy_py/blob/master/energy_py/agents/Q_learning/DQN.py)

I plan to make energy_py environments fully agent agnostic - so that agents built using other libraries can be used.  

**Function approximators**

energy_py is deep learning library agnostic - any framework can be used to [parameterize either policies or value functions](https://github.com/ADGEfficiency/energy_py/tree/master/energy_py/agents/function_approximators).  Classes are used to allow flexibility in combining different function approximator with different agents.


