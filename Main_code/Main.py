import gym
import numpy as np

from PER_DQN_Agent import Agent
# from PER_DDQN_Agent import Agent
from device import device
from Atari.ATARI.Pong.pong import Pong
from image_process import preprocess_state
from tensorflow.keras.callbacks import TensorBoard
import datetime
import tensorflow as tf

# Create TensorBoard callback
log_dir = "logs/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
# alada logs/dqn or Log/ddqn
tensorboard_callback = TensorBoard(log_dir=log_dir, histogram_freq=1)

# env = gym.make('CartPole-v1', render_mode='human')
env = Pong(render_mode='human', device=device)

# seed
# state_size = env.observation_space.shape[0]
state_size = env.observation_space.shape
action_size = env.action_space.n

agent = Agent(state_size, action_size)


num_episodes = 10000
max_t = 1000
batch_size = 32
eval_interval = 50

max_possible_reward = 490
# Lists to store metrics for each episode
episode_rewards = []
episode_epsilons = []

# to write the tensorboard logs
writer = tf.summary.create_file_writer(log_dir)

for e in range(num_episodes):
    state = env.reset(seed=42)
    print(f'state for atari: {state}')
    print(f'state shape: {state.shape}')  # Print the shape of the initial state

    # if isinstance(state, tuple):
    #     state = state[0]

    # state = state.flatten()
    state, state_size = preprocess_state(state)
    print(f'state for atari: {state}')
    print(f'flattened state shape: {state.shape}')  # Print the shape after flattening
    print(f'state size: {tf.size(state)}')
    state = np.reshape(state, [84, 84])
    print(f'state after reshape: {state}')
    state = np.reshape(state, [1, state_size])
    print(f'state after final reshape: {state}')

    total_reward = 0
    for t in range(max_t):
        action = agent.act(state)

        next_state, reward, done, truncated, info = env.step(action)
        next_state, state_size = preprocess_state(next_state)
        # next_state = next_state.flatten()
        next_state = np.reshape(next_state, [1, state_size])

        # agent.step(state, action, reward, next_state, done or truncated)
        agent.remember(state, action, reward, next_state, done or truncated)

        state = next_state
        total_reward += reward

        if done or truncated:
            loss = agent.replay(batch_size)
            # print(f"Episode: {e}/{num_episodes}, Score: {total_reward}, Epsilon: {agent.epsilon:.2f}")
            print(f"Episode: {e}/{num_episodes}, Score: {total_reward}, Epsilon: {agent.epsilon:.2f}, Loss: {loss}")

            episode_rewards.append(total_reward)
            episode_epsilons.append(agent.epsilon)

            break
    # agent.replay(batch_size)
    agent.update_target_model()

    if agent.epsilon > agent.epsilon_min:
        agent.epsilon *= agent.epsilon_decay

    with writer.as_default():
        tf.summary.scalar('Total Reward', total_reward, step=e)
        tf.summary.scalar('Epsilon', agent.epsilon, step=e)

    if e % eval_interval == 0:
        eval_mean_reward, eval_std_reward = agent.evaluate(env)
        print(f"Evaluation at episode {e}: mean reward = {eval_mean_reward}, std reward = {eval_std_reward}")
        with writer.as_default():
            tf.summary.scalar('Eval Mean Reward', eval_mean_reward, step=e)
            tf.summary.scalar('Eval Std Reward', eval_std_reward, step=e)
            # Check if the mean reward exceeds the maximum possible reward threshold
            if eval_mean_reward >= max_possible_reward:
                print(f"\nMaximum possible reward reached! Stopping training......")
                break


# Save model weights
agent.save("dqn_model.keras")
