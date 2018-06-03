"""
checks
- that the online and double q vars are always the same
    check using both copy ops type comparisons and sess.runs

todo
- processors
- logging
- tensorboard
- copy ops as an option
- prioritized experience replay support

"""
import numpy as np
import tensorflow as tf

import energy_py
from energy_py.agents import BaseAgent

from networks import feed_forward
from policies import e_greedy
from utils import find_sub_array_in_2D_array as find_action
from utils import make_copy_ops, get_tf_params
from expt_utils import EpisodeStats


class DQN(BaseAgent):
    """
    The new energy_py implementation of Deep Q-Network

    BaseAgent args (passed as **kwargs)

    DQN args

    """

    def __init__(
            self,
            discount=0.9,
            total_steps=10000,
            num_discrete_actions=20,
            nodes=(5, 5, 5),
            initial_epsilon=1.0,
            final_epsilon=0.05,
            epsilon_decay_fraction=0.3,
            double_q=False,
            batch_size=64,
            **kwargs):

        super().__init__(**kwargs)

        self.total_steps = total_steps
        self.nodes = nodes

        self.epsilon_decay_fraction = epsilon_decay_fraction
        self.initial_epsilon = initial_epsilon
        self.final_epsilon = final_epsilon

        self.double_q = double_q
        self.batch_size = batch_size

        self.discrete_actions = self.env.discretize_action_space(
            num_discrete_actions)

        self.num_actions = self.discrete_actions.shape[0]

        with tf.variable_scope('discrete_actions_tensor'):
            self.discrete_actions_tensor = tf.Variable(
                initial_value=self.discrete_actions,
                trainable=False,
                name='discrete_actions',
            )

        with tf.variable_scope('placeholders'):
            self.discount = tf.Variable(
                initial_value=discount,
                trainable=False,
                name='gamma')

            self.observation = tf.placeholder(
                shape=(None, *self.env.obs_space_shape),
                dtype=tf.float32
            )

            self.selected_action_indicies = tf.placeholder(
                shape=(None), dtype=tf.int64)

            self.reward = tf.placeholder(shape=(None), dtype=tf.float32)

            self.next_observation = tf.placeholder(
                shape=(None, *self.env.obs_space_shape),
                dtype=tf.float32)

            self.terminal = tf.placeholder(shape=(None), dtype=tf.bool)

            self.learn_step_tensor = tf.placeholder(
                shape=(),
                dtype=tf.int64,
                name='learn_step_tensor'
            )

        self.build_acting_graph()

        self.build_learning_graph()

    def build_acting_graph(self):

        with tf.variable_scope('online') as scope:

            self.online_q_values = feed_forward(
                'online_obs',
                self.observation,
                self.env.obs_space_shape,
                self.nodes,
                self.num_actions,
            )

            if self.double_q:
                scope.reuse_variables()

                self.online_next_obs_q = feed_forward(
                    'online_next_obs',
                    self.next_observation,
                    self.env.obs_space_shape,
                    self.nodes,
                    self.num_actions,
                )

        with tf.variable_scope('e_greedy_policy'):
            self.epsilon, self.policy = e_greedy(
                self.online_q_values,
                self.discrete_actions_tensor,
                self.learn_step_tensor,
                self.total_steps * self.epsilon_decay_fraction,
                self.initial_epsilon,
                self.final_epsilon
            )

    def build_copy_ops(self):
        self.online_params = get_tf_params('online')
        self.target_params = get_tf_params('target')

        return make_copy_ops(
            self.online_params,
            self.target_params,
        )

    def build_learning_graph(self):

        """ Learning """
        with tf.variable_scope('target', reuse=False):
            self.target_q_values = feed_forward(
                'target',
                self.next_observation,
                self.env.obs_space_shape,
                self.nodes,
                self.num_actions,
            )

        self.copy_ops, self.tau = self.build_copy_ops()

        with tf.variable_scope('bellman_target'):
            self.q_selected_actions = tf.reduce_sum(
                self.online_q_values * tf.one_hot(self.selected_action_indicies,
                                                  self.num_actions),
                1
            )


            if self.double_q:
                online_actions = tf.argmax(self.online_next_obs_q, axis=1)

                next_state_max_q = tf.reduce_sum(
                    self.target_q_values * tf.one_hot(online_actions,
                                                     self.num_actions),
                    axis=1,
		    keepdims=True
                )

            else:
                next_state_max_q = tf.reduce_max(
                    self.target_q_values,
                    reduction_indices=1,
                    keepdims=True
                )

            self.next_state_max_q = tf.where(
                self.terminal,
                next_state_max_q,
                tf.zeros_like(next_state_max_q),
		name='terminal_mask'
            )

            self.bellman = self.reward + self.discount * self.next_state_max_q

        with tf.variable_scope('optimization'):
            error = tf.losses.huber_loss(
                self.bellman,
                self.q_selected_actions,
                weights=1.0,
                scope='huber_loss'
            )

            loss = tf.reduce_mean(error)

            learning_rate = 0.001
            decay_learning_rate = True
            gradient_norm_clip = 10

            if decay_learning_rate:
                learning_rate = tf.train.exponential_decay(
                    0.01,
                    global_step=self.learn_step_tensor,
                    decay_steps=self.total_steps,
                    decay_rate=0.96,
                    staircase=False,
                    name='learning_rate'
                )

            optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)

            if gradient_norm_clip:
                with tf.variable_scope('gradient_clipping'):

                    grads_and_vars = optimizer.compute_gradients(
                        loss, 
                        var_list=self.online_params
                    )

                    for idx, (grad, var) in enumerate(grads_and_vars):
                        if grad is not None:
                            grads_and_vars[idx] = (tf.clip_by_norm(grad, gradient_norm_clip), var)
                    self.train_op = optimizer.apply_gradients(grads_and_vars)

            else:
                self.train_op = optimizer.minimize(loss, var_list=self.online_params)

        #  initialize the tensorflow variables
        self.sess.run(
            tf.global_variables_initializer()
        )

        #  copy the target net weights
        self.sess.run(
            self.copy_ops,
            {self.tau: 1.0}
        )


    def __repr__(self):
        return '<energy_py DQN agent>'

    def _act(self, observation):
        """

        Use the learn_step to decay epsilon, as we want to stop exploring
        only after we start learning
        """

        action = self.sess.run(
            self.policy,
            {self.learn_step_tensor: self.learn_step,
             self.observation: observation}
        )

        self.act_step += 1

        return action.reshape(1, *self.env.action_space_shape)

    def _learn(self):
        """
        Our agent attempts to make sense of the world
        """
        if self.memory_type == 'priority':
            raise NotImplementedError()

        batch = self.memory.get_batch(self.batch_size)

        #  awkward bit - finding the indicies using np :(
        #  working on a tensorflow solution
        indicies = []
        for action in batch['action']:
            indicies.append(
                find_action(np.array(action).reshape(-1), self.discrete_actions)
            )

        _ = self.sess.run(
            self.train_op,
            {self.learn_step_tensor: self.learn_step,
             self.observation: batch['observation'],
             self.selected_action_indicies: indicies,
             self.reward: batch['reward'],
             self.next_observation: batch['next_observation'],
             self.terminal: batch['done']  #  should be ether done or terminal TODO
             }
        )

        #  hardcoded for now
        _ = self.sess.run(
            self.copy_ops,
            {self.tau: 0.001}
        )


if __name__ == '__main__':
    env = energy_py.make_env('CartPole')
    obs = env.observation_space.sample()
    discount = 0.95

    with tf.Session() as sess:
        agent = DQN(
            sess=sess,
            env=env,
            total_steps=10,
            discount=discount,
            memory_type='deque',
            learning_rate=1.0
        )

        ep_stats = EpisodeStats(sess, './ep_stats') 

        obs = env.reset()

        for step in range(20):
            act = agent.act(obs)
            next_obs, reward, done, info = env.step(act)
            agent.remember(obs, act, reward, next_obs, done)
            obs = next_obs
            ep_stats.record_step(reward)

        agent.learn()

        ep_stats.record_episode()