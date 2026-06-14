import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from snake_game import SnakeGame

class SnakeEnv(gym.Env):
    """Gymnasium environment wrapper for Snake game"""

    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        # Initialize the game
        self.game = SnakeGame()
        
        # Define action and observation space
        # Actions: every tile is an action, multiply by 3 types of actions
        self.max_actions = len(self.game.board)
        # required for ppo
        self.action_space = spaces.Discrete(self.max_actions)

        self.observation_space = spaces.Dict({
            "board": spaces.Box(low=0, high=10, shape=(self.game.height, int(self.max_actions/self.game.height)), dtype=np.int8),
            # "action_mask": spaces.Box(low=0, high=1, shape=(self.max_actions,), dtype=np.int8),
            # Inventory counts for special tools
            "inventory": spaces.Box(low=0, high=99, shape=(2,), dtype=np.int8) # [bombs, rockets]
        })

        # Initialize pygame if render mode is human
        if self.render_mode == "human":
            pygame.init()

  

    def step(self, action_idx):
        if self.render_mode == "human":
            self.render()
        # Optional: Guard check during training/debugging
        mask = self.game._get_action_mask()
        if mask[action_idx] == 0:
            # The agent chose an illegal move! Punish it or handle gracefully
            return self.game._get_observation(), -10, False, False, {"error": "Illegal Move"}

        return  self.game.handleMove([self.game.action_keys[action_idx], 1])
        

    def _get_action_mask(self):
        # Initialize a flat mask of all zeros (all moves illegal by default)
        mask = np.zeros(len(self.game.board), dtype=np.int8)
        
        # Get your custom list of available moves, e.g., [["6,0", 1], ["8,4", 2]]
        available_moves = self.game.getAvailable()
        
        for coord_str, action_type in available_moves:
            # 1. Convert coordinate string "x,y" into grid integers
            # x, y = map(int, coord_str.split(','))
            # idx = self.game.board.index(coord_str)
            # y is 0-5, width is 8, x
            # x -= self.counter
            # 2. Map the 2D grid coordinates + action type into a single unique 1D flat index
            # action_type mapping: 1 -> index 0, 2 -> index 1, 3 -> index 2
            # action_idx = (y * self.width + x) * 3 + (action_type - 1)
            # action_idx = y * self.width + x
            # 3. Mark this specific action index as valid!
            # mask[idx] = 1
       
            idx = self.game.action_keys.index(coord_str)
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

        if self.render_mode == "human":
            self.render()

        return observation, info



    def render(self):
        """Render the environment"""
        if self.render_mode == "human":
            # Handle pygame events to prevent window from becoming unresponsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return

            self.game.render(mode="human")

    def close(self):
        """Close the environment"""
        self.game.close()