import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from snake_game import SnakeGame

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
        self.max_actions = len(self.game.coords_list) * 3
        # required for ppo
        self.action_space = spaces.Discrete(self.max_actions)


        self.observation_space = spaces.Dict({
            "board": spaces.Box(low=0, high=10, shape=(self.game.height, self.game.length), dtype=np.int8),
            # Inventory counts for special tools
            # "inventory": spaces.Box(low=0, high=99, shape=(2,), dtype=np.int8) # [bombs, rockets]
            "rockets": spaces.Box(low=0, high=10, shape=(1,), dtype=np.int8), 
            "bombs": spaces.Box(low=0, high=10, shape=(1,), dtype=np.int8)
        })

        # Initialize pygame if render mode is human
        if self.render_mode:
            pygame.init()

  

    def step(self, action_idx):
        if self.render_mode:
            self.render()
        # Optional: Guard check during training/debugging
        # mask = self.game._get_action_mask()
        # if mask[action_idx] == 0:
        #     print("hello")
        #     # The agent chose an illegal move! Punish it or handle gracefully
        #     return self.game._get_observation(), -10, False, False, {"error": "Illegal Move"}
        
        action = 1
        length = len(self.game.board)
        
        if action_idx >= length:
            mod = int(action_idx // length)
            action += mod
            action_idx -= length*mod        


        return  self.game.handleMove([self.game.action_keys[action_idx], action])
        

    def _get_action_mask(self):
        return self.game._get_action_mask()
        # Initialize a flat mask of all zeros (all moves illegal by default)
        mask = np.zeros(len(self.game.board)*2, dtype=np.int8)
        
        # Get your custom list of available moves, e.g., [["6,0", 1], ["8,4", 2]]
        available_moves = self.game.getAvailable()
        
        for coord_str, action_type in available_moves:

            # get index of coord
            idx = self.game.action_keys.index(coord_str)
            # if rocket, add len of game board
            if action_type == 3: 
                idx += len(self.game.board)
            
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