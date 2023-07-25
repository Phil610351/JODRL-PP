from __future__ import division
from re import A
import numpy as np
import torch
from torch.autograd import Variable
import gc
from MEC_env import mec_env
import train
import buffer
from SAC import SAC

import os


# 使用GPU卡
os.environ["CUDA_VISIBLE_DEVICES"] = "6"
# env = gym.make('Pendulum-v0')
reward_record = []
delay_record = []
energy_record = []
privacy_record = []
punish_record = []
MAX_EPISODES = 1000
MAX_STEPS = 300
MAX_BUFFER = 1000000

n_agents = 5
n_actions = 10
n_states = 3
S_DIM = n_agents * n_states
A_DIM = n_agents * n_actions
A_MAX = 1


env = mec_env(n_agents, n_states , n_actions, task_rate = 2)
ram = buffer.MemoryBuffer(MAX_BUFFER)
trainer = train.Trainer(S_DIM, A_DIM, A_MAX, ram)
# agent = SAC(S_DIM,A_DIM)

for _ep in range(MAX_EPISODES):
	observation = env.reset().reshape(n_agents*n_states)
	total_reward = 0.0
	total_privacy = 0.0
	total_energy = 0.0
	total_delay = 0.0
	total_punish = 0.0
	for r in range(MAX_STEPS):
		state = np.float32(observation)
		action = trainer.get_exploration_action(state)
		# action = agent.predict(state)
		# if _ep%5 == 0:
		# 	# validate every 5th episode
		# 	action = trainer.get_exploitation_action(state)
		# else:
		# 	# get action based on observation, use exploration policy here
		# 	action = trainer.get_exploration_action(state)
		# n X action
		action = action.reshape(n_agents, n_actions)
		
		new_observation, reward, done, _info, action = env.step(action)

		# # dont update if this is validation
		# if _ep%50 == 0 or _ep>450:
		# 	continue
		total_reward += sum(reward)
		total_privacy += sum(_info[0])
		total_energy += sum(_info[1])
		total_delay += sum(_info[2])
		total_punish += sum(_info[3])

		new_observation = new_observation.reshape(n_agents * n_states)
		action = action.reshape(n_agents*n_actions)
		new_state = np.float32(new_observation)
			# push this exp in ram
		ram.add(state, action, total_reward, new_state)
		# agent.buffer.push([state, action, total_reward, new_state, 0])
		observation = new_observation
		# if agent.buffer.buffer_len()>100:
		# 	agent.learn()
		# perform optimization
		if _ep >= 1 :
			trainer.optimize()
	temp = n_agents * MAX_STEPS
	print('Episode: %d, reward = %f' % (_ep, total_reward/temp))
	reward_record.append(total_reward/temp)
	privacy_record.append(total_privacy/temp)
	energy_record.append(total_energy/temp)
	delay_record.append(total_delay/temp)
	punish_record.append(total_punish/temp)
	# check memory consumption and clear memory
	gc.collect()
	# process = psutil.Process(os.getpid())
	# print(process.memory_info().rss)

	# if _ep%100 == 0:
	# 	trainer.save_models(_ep)


print('Completed episodes')
np.save('central_reward', reward_record)
np.save('central_privacy', privacy_record)
np.save('central_energy', energy_record)
np.save('central_delay', delay_record)
np.save('central_punish', punish_record)
