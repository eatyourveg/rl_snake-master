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
        self.game = SnakeGame()
        
        # Actions: every tile is an action, multiply by 3 types of actions
        self.max_actions = self.game.tileLength * 3
        # required for ppo
        self.action_space = spaces.Discrete(self.max_actions)
        # self.action_key_index = {k: i for i, k in enumerate(self.game.action_keys)}

        self.observation_space = spaces.Box(
            low=0, high=10, 
            shape=(self.game.height * self.game.length + 2,), 
            dtype=np.int8
        )

        # Initialize pygame if render mode is human
        if self.render_mode:
            pygame.init()

  
    # sb3 interface
    def step(self, mask_idx):
        if self.render_mode:
            self.render()

        # mask is flat 1d array 3k length. action_keys doesnt 
        # action is 1-indexed
        action = int(mask_idx // self.game.tileLength + 1)
        # position within action_keys block
        action_idx = int(mask_idx % self.game.tileLength)
      
        
        # qprint("hello",action_idx)   

        # qprint([action_idx, action])
        stats = self.game.handleMove([action_idx, action])
        # if self.render_mode: qprint(stats[4])
        return stats
        
    # sb3 interface
    def _get_action_mask(self):
        # Initialize a flat mask of all zeros (all moves illegal by default)
        mask = np.zeros(self.max_actions, dtype=np.int8)
        # qprint("avail",self.game.counter,self.game.getAvailable())
        # Get your custom list of available moves, e.g., [["6,0", 1], ["8,4", 2]]
        # dbg = []
        for coord_str, action_type in self.game.getAvailable():
            # dbg.append([coord_str, coord_str in self.game._visible_tiles])
            # ["6,0", 1], get maskindex of this command, if action, add length
            idx = coord_str + self.game.tileLength * (action_type - 1)
            # print(coord_str,idx)
            mask[idx] = 1

        # print(dbg)
        return mask

    def reset(self, seed=None, options=None):
        """Reset the environment"""
        super().reset(seed=seed)

        # observation = self.game._get_observation()

        observation = self.game.reset()
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