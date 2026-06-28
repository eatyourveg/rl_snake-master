
import pygame
import numpy as np

import itertools
from enum import Enum
from consts import *

import inspect

def qprint(*args, **kwargs):
    # Get the frame of the code that called this function
    frame = inspect.currentframe().f_back
    line_number = frame.f_lineno
    file_name = frame.f_code.co_filename
    
    # Extract just the base filename (e.g., 'snake_game.py' instead of the full path)
    short_file = file_name.split('\\')[-1].split('/')[-1]
    
    # Print the line details before your actual message
    print(f"[{short_file}:{line_number}]", *args, **kwargs)




# 125 good spot
start = {
    0:{
        "bombs": 0,
        "rockets":0,
        "beg":0,
        # "end":69,
        "end":97,
        "tiles":[]
        
    },
    1:{
        "bombs": 0,
        "rockets":1,
        "beg":97,
        
        # "end":198,
        "end":206,
        "tiles":["97,5"],
        "next":["102,0",1],
        
    }

}
start_idx = 1

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
    def __init__(self):
        self.width = 8
        self.height = 6
        self.cell_size = 80
        
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

        self.coords_list = {}
        # convert coord json to flat map
        for col, rows in coords1.items():
            for row, value in rows.items():
                self.coords_list[self.getCoord(col,row)] = value
        # print(self.coords_list)
        
        # for values in hiddenTiles2025MAY:
        #     self.coords_list[values] = TileType.HIDDEN

        # Keeps only the first 6,000 
        self.beg = start[start_idx]["beg"]
        self.length = start[start_idx]["end"] - self.beg
        self.tileBeg = self.beg*self.height
        self.tileEnd = start[start_idx]["end"] * self.height

        

        for values in start[start_idx]["tiles"]:
            self.coords_list[values] = TileType.SPACE

        self.action_keys = list(self.coords_list.keys())[self.tileBeg:self.tileEnd]
    
        # to get indexed version of dict
        
        self.cache = {}
        self.reset()


    def reset(self):
        """Reset the game to initial state"""
        
   
        # self.board = {k: self.coords_list[k] for k in list(self.coords_list.keys())[self.beg*self.height:(self.length+self.beg)*self.height]}
        self.board = self.coords_list.copy()
       

        
        self.next = 0
        if start[start_idx]["next"]: 
            self.next = nextMoves.index(start[start_idx]["next"])
        self.counter = start[start_idx]["beg"]
        self.score = 0
        self.rockets = start[start_idx]["rockets"]
        self.bombs = start[start_idx]["bombs"]
        self.totalReward = 0
        self.checkHidden()
   

        return self._get_observation()
    
    def loadImages(self):
        for tile in TileType:
            # load image and scale to cell size, store in cache
            if tile.image: self.cache[tile] = pygame.transform.scale(pygame.image.load(tile.image).convert_alpha(),(self.cell_size, self.cell_size))

       
    
    def getCurrentBoard(self):
        """slice the board dict to only include the current visible area based on counter"""
        start = self.counter * self.height 
        end = start + self.width * self.height
   
        return dict(itertools.islice(self.board.items(), start,end))



    def _get_observation(self):
        
        def get_numeric_board_array(self):
            # 1. Initialize a blank 2D grid matching your board dimensions
            # Shape is (rows, columns) -> (height, width)
            grid = np.zeros((self.height, self.length), dtype=np.int8)
    
            # 3. Loop through and map string symbols to numeric values for the AI
            # for key, val in self.board.items():
            for key, val in list(self.board.items())[self.tileBeg:self.tileEnd]:
                # list(self.coords_list.keys())
                # 5,3 -> (15, 3)

                x, y = map(int, key.split(','))
                x -= self.beg

                # Map your custom Enum symbols or values to clean integers/floats
                grid[y, x] = TILE_TYPE_MEMBERS.index(val)
    
          
            return grid

        return {
            "board": get_numeric_board_array(self),
            "rockets": np.array([self.rockets], dtype=np.int8),
            "bombs": np.array([self.bombs], dtype=np.int8)
        }
    
    def render(self, mode=True):
        """Render the game"""
        if mode:
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
        
        move_result = self.handleMove([coord,e.button])
        if move_result is None:
            # Use current values so the step function returns valid elements

            info = {"invalid_move": True}
        else:
            # Unpack safely since we confirmed it's not None
            obs, reward, terminated, truncated, info = move_result

        if info: 
            print(info)
        
        # this.draw()
    def checkHidden(self):
      # get all hidden tiles in the current board, and if any are adjacent to a revealed tile, reveal them
      for tile , value in self.getCurrentBoard().items():
        if value == TileType.HIDDEN and self.isTileVisible(tile):
          self.setTile(tile)
        
      
    

    def getAvailable(self): 
        current = self.getCurrentBoard().items()
        tilesVisibleNonspace = [[key, 1] for key, val in current
            if val != TileType.SPACE and val != TileType.CHESTOPEN and self.isTileVisible(key)]
        tilesRocket = []
        tilesBomb = []
 
        for key, val in current:
            if val == TileType.SPACE:
                if self.rockets > 0 : tilesRocket.append([key, 3])
                if self.bombs > 0 :tilesBomb.append([key, 2])
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
        
        tile, button = move
        tileValue = self.board[tile]
        action = Action.from_button(button)

        # cant click opened chests or hidden tiles
        if tileValue in ( TileType.CHESTOPEN, TileType.HIDDEN ) or not self.isMoveVisible(tile): return
        self.reward = -1
        if action == Action.ROCKET:
            #  can only rocket on space tile
            if tileValue != TileType.SPACE or self.rockets <= 0: return
            # self.reward += 0.5
            self.rockets -= 1
            column, row = self.splitCoord(tile)
            # set row to spaces
            for i in range(self.width):
                # ignore actiontile
                if self.counter + i == column:
                    continue
                self.setTile(self.getCoord(self.counter + i, row))
        elif action == Action.DIG:
            # invalid move
            if tileValue == TileType.SPACE: return
            
            
            if tileValue == TileType.STONE: 
                self.score += 2
                self.reward -= 3
                self.setTile(tile)
            # note clicking this chest doesnt add shovel
            # returning avoids score add
            elif tileValue == TileType.CHESTB:
                self.bombs+=1
                self.board[tile] = TileType.CHESTOPEN
                self.reward += 5
            elif tileValue == TileType.CHESTR:
                self.rockets+=1
                self.board[tile] = TileType.CHESTOPEN
                self.reward += 5
            else:
                # score only increases when dig and not chest
                self.score += 1
                self.setTile(tile)
                
            
            
        
        
        elif action == Action.BOMB:
            #  can only bomb on space tile
            if tileValue != TileType.SPACE or self.bombs <=0: return self._get_observation(), self.reward, False, False, info
            # self.reward += 0.5
            self.bombs -= 1
            arr = set()
            # get adjacent tiles, then get their adjacent tiles
            
        
            for adj in self.getAdjacentTiles(tile):
                arr.update([adj])         
                for adj2 in self.getAdjacentTiles(adj):
                    arr.update([adj2])
            
            for coord in arr:
                self.setTile(coord)
            
        
        self.checkHidden()
        self.checkAdvance()

        if (action == Action.BOMB or action == Action.ROCKET) and self.reward <= 3: self.reward -= 5
        # finalScore = self.score
        # win condition
        if self.counter>=self.beg+self.length-self.width:

            self.reward += self.length*2 - self.score*2  + self.rockets * 6 + self.bombs * 6
            self.totalReward += self.reward
            info = {"score": self.score,"reward":self.reward, "move":move,"totalReward":self.totalReward, "bombs":self.bombs,"rockets":self.rockets, "eff":self.length/self.score}
            # if self.screen : print(info)
            self.reset()
            
            terminated = True
            
            return self._get_observation(), self.reward, terminated, False, info
        self.totalReward += self.reward
        info = {"score": self.score,"reward":self.reward, "move":move, "totalReward":self.totalReward , "bombs":self.bombs,"rockets":self.rockets}
        # if self.screen : print(info)
        return self._get_observation(), self.reward, False, False, info
    
    
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
            self.reward += 1
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
      
        move_result  = self.handleMove(nextMoves[self.next])

        if move_result is None:
            info = {"invalid_move": True}
        else:
            # Unpack safely since we confirmed it's not None
            obs, reward, terminated, truncated, info = move_result

        if info: 
            print(info)
    
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
        mask = np.zeros(self.length*self.height*3, dtype=np.int8)
        
        
        # Get your custom list of available moves, e.g., [["6,0", 1], ["8,4", 2]]
        available_moves = self.getAvailable()
        # qprint("avail", available_moves)
        for coord_str, action_type in available_moves:
        
            # ["6,0", 1]
            # get index of key
            # if action, add length
            idx = self.action_keys.index(coord_str)
            if action_type == 3: 
                idx += self.length*self.height*2
            elif action_type == 2:
                idx += self.length*self.height
        
            # print(coord_str, action_type, idx)
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