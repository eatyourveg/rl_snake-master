import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from snake_game import SnakeGame, qprint


class SnakeEnv(gym.Env):
    """Gymnasium environment wrapper for Snake game"""

    metadata = {"render_modes": True, "render_fps": 30}

    def __init__(self, render_mode=False):
        super().__init__()
        self.render_mode = render_mode
        # Initialize the game
        self.game = SnakeGame()
        
        # Define action and observation space
        # Actions: every tile is an action, multiply by 3 types of actions
        self.max_actions = self.game.tileLength * 3
        # required for ppo
        self.action_space = spaces.Discrete(self.max_actions)


        self.observation_space = spaces.Dict({
            # shape does not include the 3 moves
            "board": spaces.Box(low=0, high=10, shape=(self.game.height, self.game.length), dtype=np.int8),
            "rockets": spaces.Box(low=0, high=10, shape=(1,), dtype=np.int8), 
            "bombs": spaces.Box(low=0, high=10, shape=(1,), dtype=np.int8)
        })

        # Initialize pygame if render mode is human
        if self.render_mode:
            pygame.init()

  
    # sb3 interface
    def step(self, mask_idx):
        if self.render_mode:
            self.render()

        # mask is flat 1d array 3k length. action_keys doesnt 
        # action is 1-indexed
        action = mask_idx // self.game.tileLength + 1
        # position within action_keys block
        action_idx = mask_idx % self.game.tileLength
      
        
        # qprint("hello",action_idx)   

        # qprint([self.game.action_keys[action_idx], action])
        stats = self.game.handleMove([self.game.action_keys[action_idx], action])
        # if self.render_mode: qprint(stats[4])
        return stats
        
    # sb3 interface
    def _get_action_mask(self):
        # Initialize a flat mask of all zeros (all moves illegal by default)
        mask = np.zeros(self.max_actions, dtype=np.int8)
        
        # Get your custom list of available moves, e.g., [["6,0", 1], ["8,4", 2]]
        for coord_str, action_type in self.game.getAvailable():
            # ["6,0", 1], get maskindex of this command, if action, add length
            idx = self.game.action_keys.index(coord_str) + self.game.tileLength * (action_type - 1)
            mask[idx] = 1
        
        return mask

    def reset(self, seed=None, options=None):
        """Reset the environment"""
        super().reset(seed=seed)

        if seed is not None:
            np.random.seed(seed)

        observation = self.game._get_observation()

        # observation = self.game.reset()
        info = {"score": self.game.score}

        if self.render_mode:
            self.render()

        return observation, info



    def render(self):
        """Render the environment"""
        if self.render_mode:
            # Handle pygame events to prevent window from becoming unresponsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return

            self.game.render(mode=True)

    def close(self):
        """Close the environment"""
        self.game.close()