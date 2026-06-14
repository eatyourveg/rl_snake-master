import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from snake_game import SnakeGame

class SnakeEnv(gym.Env):
    """Gymnasium environment wrapper for Snake game"""

    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, render_mode=None, width=8, height=6):
        super().__init__()

        self.width = width
        self.height = height
        self.render_mode = render_mode

        # Initialize the game
        self.game = SnakeGame(width=width, height=height)

        # Define action and observation space
        # Actions: 4 directions (up, right, down, left)
        # self.action_space = spaces.Discrete(4)
        self.max_actions = len(self.game.board)
        self.action_space = spaces.Discrete(self.max_actions)

        self.observation_space = spaces.Dict({
            "board": spaces.Box(low=0, high=10, shape=(self.height, int(self.max_actions/self.height)), dtype=np.int8),
            # "action_mask": spaces.Box(low=0, high=1, shape=(self.max_actions,), dtype=np.int8),
            # Inventory counts for special tools
            "inventory": spaces.Box(low=0, high=99, shape=(2,), dtype=np.int8) # [bombs, rockets]
        })

        # # Observation space: 11 boolean/binary features
        # self.observation_space = spaces.Box(
        #     low=0, high=1, shape=(11,), dtype=np.float32
        # )

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
        # idx = -1
        # for i in range(action_idx+1):
        #     if mask[i] == 1: idx +=1
      
        # print(self.game.action_keys[action_idx])
        # available_moves = self.game.getAvailable()
        # print(mask, available_moves, action_idx, idx)
        observation, reward, terminated, truncated, info = self.game.handleMove([self.game.action_keys[action_idx], 1])
        # ... Decode action_idx back to your grid coordinates and execute move ...
        # print(available_moves[idx], reward)
        # Get new state observation
        # new_mask = self._get_action_mask()
        # obs = self._get_obs(new_mask)
        # reward = self._calculate_reward()
        # terminated = self._check_game_over()
        
        
        return observation, reward, terminated, truncated, info
    
    # def step(self, action):
    # """Execute one step in the environment"""
    # observation, reward, terminated, truncated, info = self.game.take_action(action)

    # if self.render_mode == "human":
    #     self.render()

    # return observation, reward, terminated, truncated, info


    # def _get_obs(self, mask):
    #     return {
    #         "board": self.game.get_numeric_board_array(),
    #         "inventory": np.array([self.game.bombs, self.game.rockets], dtype=np.int8),
    #         "action_mask": mask
    #     }

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
            if coord_str in self.game.coords_list:
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