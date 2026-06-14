import json
import pygame
import numpy as np
import random
import itertools
from enum import Enum
from consts import *




class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
class Action(Enum):
    DIG = (1,)
    BOMB = (2,)
    ROCKET = (3,)
    @property
    def mouse_button(self):
        # Returns the raw button number assigned to this action
        return self.value[0]

    @classmethod
    def from_button(cls, button_num):
        # Loop through all actions to find the one matching the button index
        for action in cls:
            if action.mouse_button == button_num:
                return action
        return None




class SnakeGame:
    def __init__(self, width=8, height=6, cell_size=80):
        self.width = 8
        self.height = 6
        self.cell_size = cell_size

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.DARK_GREEN = (0, 128, 0)
        
        # Pygame setup (only initialized when needed)
        self.screen = None
        self.clock = None
        self.font = None

        self.dark_overlay = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        self.dark_overlay.fill((0, 0, 0, 160)) # Adjust 160 up or down for darkness preference

        self.coords_list = self.jsonToMapDeep()
        
        for values in hiddenTiles2025MAY:
            self.coords_list[values] = TileType.HIDDEN

        # Keeps only the first 6,000 
        self.ceiling = 600
        self.finalScore = 0
        self.coords_list = {k: self.coords_list[k] for k in list(self.coords_list.keys())[:self.ceiling]}
        self.action_keys = list(self.coords_list.keys())
        self.cache = {}
        self.reset()


    def reset(self):
        """Reset the game to initial state"""
        self.snake = [(self.width // 2, self.height // 2)]
        self.food = [0,0]
        self.board = self.coords_list.copy()
        self.next = 0
        
        
        
    #           this.counter = 0
    #   this.moves = 0
    #   this.next = 0
    #   this.stats = { Bombs: 0, Rockets: 0, StarBlue: 0, StarYellow: 0 }

    #   this.map = jsonToMapDeep(coords);

        self.direction = Direction.RIGHT
        self.counter = 0
        self.score = 0
        self.rockets = 0
        self.bombs = 0
        self.game_over = False

        return self._get_observation()
    
    def loadImages(self):
        for tile in TileType:
            # load image and scale to cell size, store in cache
            if tile.image: self.cache[tile] = pygame.transform.scale(pygame.image.load(tile.image).convert_alpha(),(self.cell_size, self.cell_size))

    def jsonToMapDeep(self):
        flatMap = {}
        for col, rows in coords.items():
            for row, value in rows.items():
                flatMap[self.getCoord(col,row)] = value
        return flatMap         
    
    def getCurrentBoard(self):
        """slice the board dict to only include the current visible area based on counter"""
        start = self.counter * self.height 
        end = start + self.width * self.height
        return dict(itertools.islice(self.board.items(), start,end))



    def _get_observation(self):
        
        return {
            "board": self.get_numeric_board_array(),
            # "action_mask": mask or self._get_action_mask(),
            "inventory": np.array([self.bombs, self.rockets], dtype=np.int8)
        }
    

    def get_numeric_board_array(self):
        # 1. Initialize a blank 2D grid matching your board dimensions
        # Shape is (rows, columns) -> (height, width)
        grid = np.zeros((self.height, int(len(self.board)/self.height)), dtype=np.int8)
        
        # 2. Grab your raw board state dictionary
        # current_board = self.getCurrentBoard() # Returns {"0,0": "H", "1,0": "A", ...}
        
        # 3. Loop through and map string symbols to numeric values for the AI
        for key, val in self.board.items():
            # 5,3 -> (15, 3)
            x, y = map(int, key.split(','))
            # subtract x to get relative coord to currentboard
            # x -= self.counter
            # Map your custom Enum symbols or values to clean integers/floats

            grid[y, x] = TILE_TYPE_MEMBERS.index(val)
 
                
        return grid

    

    def render(self, mode='human'):
        """Render the game"""
        if mode == 'human':
            if self.screen is None:
                pygame.init()
                window_width = self.width * self.cell_size
                window_height = self.height * self.cell_size + 50  # Extra space for UI
                self.screen = pygame.display.set_mode((window_width, window_height))
                pygame.display.set_caption("Snake Game")
                self.clock = pygame.time.Clock()
                self.font = pygame.font.Font(None, 32)
                # must be called after self.screen()
                self.loadImages()

            # draw tiles
            self.screen.fill(self.BLACK)
            for i, (coord_str,value) in enumerate(self.getCurrentBoard().items()):
                y = int(i % self.height)
                x = int(i / self.height)
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                self.screen.blit(self.cache[value], rect)
                if not self.isTileVisible(coord_str): self.screen.blit(self.dark_overlay, rect)

            for i in range(self.width):
                x = i * self.cell_size + (self.cell_size/2)
                y = 5
                score_text = self.font.render(str(self.counter+i), True, self.WHITE)
                self.screen.blit(score_text, (x, y))

            # Draw UI
            ui_y = self.height * self.cell_size + 10
            score_text = self.font.render(f"Score: {self.score}, Rockets:{self.rockets}, Bombs:{self.bombs}", True, self.WHITE)
            self.screen.blit(score_text, (10, ui_y))

            # Game over overlay
            if self.game_over:
                overlay = pygame.Surface(self.screen.get_size())
                overlay.set_alpha(128)
                overlay.fill(self.BLACK)
                self.screen.blit(overlay, (0, 0))

                game_over_text = self.font.render("GAME OVER", True, self.WHITE)
                score_text = self.font.render(f"Final Score: {self.score}", True, self.WHITE)
                restart_text = self.font.render("Press SPACE to restart or ESC to quit", True, self.WHITE)

                window_width = self.width * self.cell_size
                window_height = self.height * self.cell_size + 50

                game_over_rect = game_over_text.get_rect(center=(window_width // 2, window_height // 2 - 40))
                score_rect = score_text.get_rect(center=(window_width // 2, window_height // 2))
                restart_rect = restart_text.get_rect(center=(window_width // 2, window_height // 2 + 40))

                self.screen.blit(game_over_text, game_over_rect)
                self.screen.blit(score_text, score_rect)
                self.screen.blit(restart_text, restart_rect)

            pygame.display.flip()
            if self.clock:
                self.clock.tick(30)

    def close(self):
        """Close the rendering window"""
        if self.screen is not None:
            pygame.quit()
            self.screen = None

    def getCoord(self, col, row):
        return f"{col},{row}"

    def handle_click(self, e): 
      # if (this.gameOver || this.training) return;

        # if need bounds
        left = 0
        top = 0
        pixel_x, pixel_y = e.pos
        """cell click relative to canvas"""
        col = min(int((pixel_x - left) / self.cell_size), self.width - 1)
        row = min(int((pixel_y - top) /  self.cell_size), self.height - 1)
        # cell index of current board
        # cell_index = row * self.width + col
        # tile = {column: col+self.counter, row: row}
        coord = self.getCoord(col+self.counter, row)
        currVal = self.board[coord]
        # Object.entries(MOUSE_BUTTONS).find(([key,value]) => value==e.button)[0]
        # print(f"cell: ({coord}) {currVal}")
        
        
        self.handleMove([coord,e.button])
        
        # this.draw()
    def checkHidden(self):
      # get all hidden tiles in the current board, and if any are adjacent to a revealed tile, reveal them
      for tile , value in self.getCurrentBoard().items():
        if value == TileType.HIDDEN and self.isTileVisible(tile):
          self.setTile(tile)
        #   print(f'Revealed "H" at ${tile}')
        
      
    

    def getAvailable(self): 
        current = self.getCurrentBoard().items()
        tilesVisibleNonspace = [[key, 1] for key, val in current
            if val != TileType.SPACE and val != TileType.CHESTOPEN and self.isTileVisible(key)]
        tilesRocket = []
        tilesBomb = []
 
        # for key, val in current:
        #     if val == TileType.SPACE:
        #         if self.rockets > 0 : tilesRocket.append([key, 2])
        #         if self.bombs > 0 :tilesBomb.append([key, 3])
        # return flat array
        return tilesVisibleNonspace +tilesRocket + tilesBomb
    
    def isTileVisible(self, tile):
        return TileType.SPACE == self.board[tile] or any(TileType.SPACE == self.board[tile2] for tile2 in self.getAdjacentTiles(tile))
    
    def isMoveVisible(self,tile):
      # if the tile is already revealed, it's visible
      if TileType.SPACE == self.board[tile]: return True

      # if adjacent to a revealed tile, it's visible
      return self.isTileVisible(tile)
    

    def getAdjacentTiles(self, tile):
        adjacent = []
        # Directions: right, left, down, up
        directions = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        
        for dc, dr in directions:
            column, row = self.splitCoord(tile)
            column += dc
            row += dr

            # Skip if out of bounds
            # Visible columns range from counter to counter+width-1
            # Rows range from 0 to height-1
            if column < self.counter or column >= self.counter + self.width or row < 0 or row >= self.height:
                continue

            key = self.getCoord(column, row)
            # Only add tile if it exists in the map
            if key in self.board:
                adjacent.append(key)
        
        return adjacent
    
    def splitCoord(self, coord): 
      return [int(x) for x in coord.split(',')]
    


    def setTile(self, coord, targetSymbol=TileType.SPACE):
    
        
        currTile = self.board[coord]
        # If the tile is already the desired symbol, do nothing
        # Prevent overwriting chest tiles (they are permanent)
        # if debug:
        #     print(f"Setting tile {coord} from {currTile} to {targetSymbol}")
        if currTile == targetSymbol or TileType.isChest(currTile):
            return
        
        TileType.claimTile(self,currTile)
        # Update the tile in the board
        self.board[coord] = targetSymbol


    def handleMove(self, move):
        
        terminated = False
        self.reward = -10
        tile = move[0]
        val = self.board[tile]
        action = Action.from_button(move[1])
        # val = TileType.from_symbol(self.board[tile])
        if val in ( TileType.CHESTOPEN, TileType.HIDDEN )or not self.isMoveVisible(tile): return
        if action == Action.ROCKET:
            #  can only rocket on space tile
            if val != TileType.SPACE or self.rockets <= 0: return
            self.rockets -= 1
            column, row = self.splitCoord(tile)
            # set row to spaces
            for i in range(self.width):
                if self.counter + i == column:
                    continue
                self.setTile(self.getCoord(self.counter + i, row))
        elif action == Action.DIG:
        # // do nothing if tile is revealed
            if val == TileType.SPACE: return
            elif val == TileType.STONE: 
                self.score += 1
                self.reward -= 10
                self.setTile(tile)
            # note clicking this chest doesnt add shovel
            # returning avoids score add
            elif val == TileType.CHESTB:
                self.bombs+=1
                self.board[tile] = TileType.CHESTOPEN
                self.score -= 1
                self.reward +=20
            elif val == TileType.CHESTR:
                self.rockets+=1
                self.board[tile] = TileType.CHESTOPEN
                self.score -= 1
                self.reward += 20
            else:
                self.setTile(tile)
                
            
            
        
        
        elif action == Action.BOMB:
            #  can only bomb on space tile
            if val != TileType.SPACE or self.bombs <=0: return
            self.bombs -= 1
            arr = set()
            # get adjacent tiles, then get their adjacent tiles
            
        
            for adj in self.getAdjacentTiles(tile):
                arr.update([adj])         
                for adj2 in self.getAdjacentTiles(adj):
                    arr.update([adj2])
            
            for coord in arr:
                self.setTile(coord)

          
        self.lastMove = tile
        self.score += 1
        self.checkHidden()
        self.checkAdvance()

        if self.counter>=90:
            self.finalScore = self.score
            self.reset()
            
            terminated = True
           
        return self._get_observation(), self.reward, terminated, False, {"score": self.finalScore}
    
    
    def  getColumn(self,colIndex=None):
      if not colIndex:
        colIndex = self.counter + self.width - 1
      start = colIndex * self.height
      end = start + self.height
      return list(itertools.islice(self.board.items(), start, end))
    

    def checkAdvance(self):
        lastColArr = self.getColumn()
        
        def advance():
            # print(f'advance:{self.counter}')
            self.counter += 1
            # reveal any hidden tiles in the new column
            self.reward += 100
            self.checkHidden()
            self.checkAdvance()
            # self.render()
        
      # if any tile is A or (chest and visible), advance the board. otherwise
    #   any(self.board.get(tile2) == TileType.SPACE.symbol for tile2 in self.getAdjacentTiles(tile))
        if any(TileType.SPACE == value or (TileType.isChest(value) and self.isTileVisible(key)) for key, value in lastColArr):
           
            advance()        
        elif any(value == TileType.HIDDEN for key, value in lastColArr):
            hidden = [key for key, val in lastColArr if val == TileType.HIDDEN]
            for val in hidden:
                chest = next((adj for adj in self.getAdjacentTiles(val) if TileType.isChest(self.board[adj])), None)
                if not chest: continue

                hiddenCoords = self.splitCoord(val)
                chestCoords = self.splitCoord(chest)
                if abs(hiddenCoords[1]-chestCoords[1])<=1:
                    # print(f'Advanced at {val} due to top/bottom chest at {chest}')
                    advance()
                    return
                elif hiddenCoords[0]-chestCoords[0]==1: 
                    # print(f'Advanced at hidden {val} due to behind chest at ${chest}')
                    advance()
                    return
                
    def nextMove(self): 
      
      self.handleMove(nextMoves[self.next])
      
      self.render()
    #   print(f'Next: {nextMoves[self.next]}. Next move: {nextMoves[self.next+1]}')
      self.next += 1
      
    #   pos = self.getCoordinatesFromIndex(self.getCurrentBoard().findIndex(([key]) => key === nextMoves[this.next+1][0]))
    #    this.ctx.fillStyle = "green";
    #    this.ctx.fillRect(pos.x, pos.y, 30, 30);
    #    this.ctx.drawImage(, pos.x + this.cellSize/2, pos.y + this.cellSize/2)
    #   let img = null
    #   switch(nextMoves[this.next+1][1]){
    #     case MOUSE_BUTTONS.LEFT: img = this.cache['H']; break;
    #     case MOUSE_BUTTONS.RIGHT: img = this.cache['R']; break;
    #     case MOUSE_BUTTONS.MIDDLE: img = this.cache['O']; break;
    #   }
      
    #   this.ctx.drawImage(img, pos.x, pos.y, 30, 30);
    #   this.next++

    
    def _get_action_mask(self):
        # Initialize a flat mask of all zeros (all moves illegal by default)
        mask = np.zeros(len(self.board), dtype=np.int8)
        
        
        # Get your custom list of available moves, e.g., [["6,0", 1], ["8,4", 2]]
        available_moves = self.getAvailable()
        
        for coord_str, action_type in available_moves:
            # 1. Convert coordinate string "x,y" into grid integers
            # x, y = map(int, coord_str.split(','))
            # idx = self.board.index(coord_str)
            # y is 0-5, width is 8, x
            # x -= self.counter
            # 2. Map the 2D grid coordinates + action type into a single unique 1D flat index
            # action_type mapping: 1 -> index 0, 2 -> index 1, 3 -> index 2
            # action_idx = (y * self.width + x) * 3 + (action_type - 1)
            # action_idx = y * self.width + x
            # 3. Mark this specific action index as valid!
            # mask[idx] = 1


            if coord_str in self.coords_list:
                idx = self.action_keys.index(coord_str)
                mask[idx] = 1
        
        return mask

    def play_manual(self, fps=8):
        """Play the game with manual controls"""

        if self.screen is None:
            self.render()  # Initialize display

  
        running = True

        while running:
            # Handle events
            for event in pygame.event.get():
                # print(event)
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event)
                    self.render()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        
                        self.nextMove()



            # Render
            # self.render()
            pygame.display.flip()
            self.clock.tick(fps)
            # Show pause indicator


        self.close()
        print(f"Game ended. Final score: {self.score}")
        



def main():
    game = SnakeGame()

    try:
        game.play_manual()
    except KeyboardInterrupt:
        game.close()
        print("\nGame interrupted")

if __name__ == "__main__":
    main()