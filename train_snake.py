# train_snake.py
import json
import os

import numpy as np
from snake_env import SnakeEnv
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker # 👈 Import the wrapper
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv
import time
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback

import warnings

# # 1. Force Pygame/SDL to run in headless mode (No physical window needed)
# os.environ["SDL_VIDEODRIVER"] = "dummy"
# os.environ["TORCH_COMPILE_DISABLE"] = "1"
# # 2. Hide massive TensorFlow CPU optimization and warning logs
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

# # 3. Mute Python deprecation noise so you can read your SB3 training tables
# warnings.filterwarnings("ignore", category=DeprecationWarning)
# warnings.filterwarnings("ignore", category=UserWarning, module="gym")

from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor



from stable_baselines3.common.callbacks import BaseCallback

class CompactLoggerCallback(BaseCallback):
    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        for info in infos:
            if "episode" in info:
                ep = info["episode"]
                print(f"steps={self.num_timesteps} rew={ep['r']:.1f} len={ep['l']:.1f}")
        return True
    
    def _on_rollout_end(self) -> None:
        ev  = self.model.logger.name_to_value.get("train/explained_variance", 0)
        ent = self.model.logger.name_to_value.get("train/entropy_loss", 0)
        print(f"  ev={ev:.3f} ent={ent:.3f}")

def to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return obj

class BestEpisodeCallback(BaseCallback):
    def __init__(self, save_path, verbose=0):
        super().__init__(verbose)
        self.save_path = save_path
        self.best_reward = -np.inf

   

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        for info in infos:
            if "episode" in info:
                ep_reward = info["episode"]["r"]
                if info["eff"] > 2 and ep_reward > self.best_reward:
                    self.best_reward = ep_reward
                    self.model.save(self.save_path)
                    with open("logs/info.json", "a") as f:
                        clean = {k: to_serializable(v) for k, v in info.items() if k != "terminal_observation"}
                        f.write(json.dumps(clean) + "\n")
                        # f.write(json.dumps(info, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)) + "\n")
                    print(f"New best! rew={ep_reward:.1f} steps={self.num_timesteps}")
        return True

def mask_fn(environment):
    return environment._get_action_mask()
    
fn = "snake_model.zip"

def train_snake(timesteps=300000, render=False):
    print(f"Total timesteps: {timesteps}")

    # render = True
    # Create environment
    render_mode = True if render else False
    # Define a helper function that handles creating AND wrapping a single environment instance
    # def make_wrapped_env():
        # 1. Create the base environment instance
    env = SnakeEnv(render_mode=render_mode)
        
        # 2. Wrap it so SB3 can officially read the masks
    env = ActionMasker(env, mask_fn)
    env = Monitor(env)
        # return env

    # 3. Pass this helper function to make_vec_env to    spin up 4 properly wrapped copies
    # 4 envs dropped to 400 fps
    # 1 env maxed out at 300 fps
    if __name__ == '__main__': # Required for Windows/Mac multiprocessing
        # train_env = make_vec_env(make_wrapped_env, n_envs=4, vec_env_cls=SubprocVecEnv)
        # evaluation_env = env()
        best_ep_callback = BestEpisodeCallback(save_path="./logs/best")
        # eval_callback = MaskableEvalCallback(
        #     eval_env=env,
        #     best_model_save_path="./logs/best_model",
        #     log_path="./logs/results",
        #     eval_freq=25000,         # How often to check performance (in steps)
        #     n_eval_episodes=1,      # Run 40 episodes to get a solid average score
        #     deterministic=True,      # Turn off random exploration during testing
        #     verbose=1
        # )
    
    if os.path.exists(fn):
        print(" Found existing model!")
        # Load the model and connect it to your current environment
        model = MaskablePPO.load(fn, 
                                 env=env,
                                 custom_objects={"ent_coef": 0.15,
                                                 "learning_rate": 3e-5},
                                 )
    else:
        model = MaskablePPO(
            "MlpPolicy",
            env,
            verbose=1,
            learning_rate=3e-4,       # Standard starting rate, can lower to 1e-4 if updates jump too violently
            n_steps=512,             # How many steps to collect per environment before updating
            batch_size=256,           # Minibatch size for optimization (128 or 256 is good for grid boards)
            gamma=0.995,               # Discount factor (0.99 means it cares about long-term rewards)
            
            # --- CRITICAL FIXES FOR YOUR LOGS ---
            ent_coef=0.01,            # Forces exploration! Higher values stop entropy from collapsing to -0.164
            clip_range=0.2,           # Standard PPO safety clipping bounds
            gae_lambda=0.95,          # Bias vs variance trade-off for generalized advantage estimation
            n_epochs=10,              # Number of times to optimize using the collected rollout data
        )
    try:

        
        # Train the model
        print("Starting training...")
        model.learn(total_timesteps=timesteps, 
            callback=[
                best_ep_callback,
                # CompactLoggerCallback()
            ])
     
        # Save the model
        model.save(fn)
        print("Model saved as 'snake_model'")

    except KeyboardInterrupt:
        # This block triggers the moment you hit Ctrl+C
        print("\nTraining interrupted by user! Saving current progress safely...")
        model.save(fn)
        print(f"Model successfully saved to {fn}")

    env.close()
    return model

def play_trained_model(model_path="snake_model", episodes=1, render_mode=False):
    
    # Create environment with rendering
    env = SnakeEnv(render_mode)
    env = ActionMasker(env, mask_fn)
    # Load model
    # model_path = "./logs/best_model/best_model"
    model = MaskablePPO.load(model_path, env=env)


    for episode in range(episodes):
        result = env.reset()
        if isinstance(result, tuple):
            obs, info = result
        else:
            obs = result
            info = {}
        done = False

        # print(f"Episode {episode + 1}:")

        while not done:
            # Get action from model
            current_mask = env.action_masks()
            action, _ = model.predict(obs, 
                                      action_masks=current_mask,
                                      deterministic=True)

            # Take step
            
            # print(action)
            obs, reward, terminated, truncated, info = env.step(action)
            print(info)
            # print(obs, reward, terminated, truncated, info)
            done = terminated or truncated
            # print(terminated, truncated, obs  )
            if render_mode:
                time.sleep(1)




    env.close()



def main():
    """Main function with simple command line interface"""
    import sys

    if len(sys.argv) == 1:
        # Default training
        train_snake()
    elif sys.argv[1] == "train":
        # Custom training
        timesteps = int(sys.argv[2]) if len(sys.argv) > 2 else 300000
        render = "--render" in sys.argv
        if "--new" in sys.argv: 
            try:
                os.remove(fn)
                print("File deleted successfully.")
            except FileNotFoundError:
                print("The file does not exist.")
            except PermissionError:
                print("Permission denied (the file might be open in another program).")
        train_snake(timesteps, render)
    elif sys.argv[1] == "play":
        render = "--render" in sys.argv

        # Play trained model
        model_path = "snake_model"
        # model_path = sys.argv[2] if len(sys.argv) > 2 else "snake_model"
        # episodes = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        play_trained_model(model_path, render_mode=render)
    else:
        print("Usage:")
        print("  python train_snake.py                    # Train with defaults")
        print("  python train_snake.py train 200000       # Train for 200k steps")
        print("  python train_snake.py train 50000 --render # Train with rendering")
        print("  python train_snake.py play               # Watch trained model")
        print("  python train_snake.py play snake_model 3 # Watch model play 3 games")

if __name__ == "__main__":
    main()