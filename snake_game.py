
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
map_idx = 1
start_idx = 0

class Action(Enum):
    DIG = (1,)
    BOMB = (2,)
    ROCKET = (3,)
    @property
    def key(self):
        # Returns the raw button number assigned to this action
        return self.value[0]

    @classmethod
    def from_button(cls, button_num):
        # Loop through all actions to find the one matching the button index
        for action in cls:
            if action.key == button_num:
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

        
        # convert coord json to flat map
        
        coordsList = coords[map_idx].items()
        boardList = [None] * len(coordsList) * self.height
        for col, rows in coordsList:
            for row, value in rows.items():
                # boardList.append(value)
                boardList[int(col)*self.height+int(row)] = value
        # print(self.coords_list)
        self.coords_list = np.array(boardList)
        
    

        # Keeps only the first 6,000 
        # beginning col
        self.beg = start[start_idx]["beg"]
        # column length, not tiles
        self.length = start[start_idx]["end"] - self.beg
        self.tileBeg = self.beg*self.height
        self.tileEnd = start[start_idx]["end"] * self.height
        self.tileLength = self.length*self.height
        self.counter = 0
        

        for key in start[start_idx]["tiles"]:
            self.coords_list[self.keyToIndex(key)] = TileType.SPACE
        self.board = self.coords_list.copy()
        self._visible_tiles = set()

        # make only the adjacent space tiles visible to trigger the jumps
        # for idx,tile in enumerate(self.coords_list):
        #     if tile == TileType.SPACE:
            
        #         if idx>10000: break
        #         self.counter = idx // self.height
        #         self.isTileVisible(idx)
     
        # print(self._visible_tiles)
        self._visible_tiles_init = self._visible_tiles.copy()
        
        self.cache = {}
        self.reset()

    def keyToIndex(self,tile):
        x,y = tile.split(",")
        return int(x)*self.height+int(y)
    
    def indexToKey(self,index):
        return [index // self.height, index % self.height]

 

    def reset(self):
        """Reset the game to initial state"""
        
   
        # self.board = {k: self.coords_list[k] for k in list(self.coords_list.keys())[self.beg*self.height:(self.length+self.beg)*self.height]}
        self.board = self.coords_list.copy()
       

        self._visible_tiles = self._visible_tiles_init.copy()
        self.next = 0
        if "next" in start[start_idx]:
            self.next = nextMoves[map_idx].index(start[start_idx]["next"]) 
        self.counter = start[start_idx]["beg"]
        self.score = 0
        self.rockets = start[start_idx]["rockets"]
        self.bombs = start[start_idx]["bombs"]
        self.totalReward = 0
        # self.reward = 0
        self.moves = []
        self.checkHidden()

        return self._get_observation()
    
    

       
    
    def getCurrentBoard(self):
        """slice the board dict to only include the current visible area based on counter"""
        start = self.counter * self.height 
        end = start + self.width * self.height
   
        return self.board[start:end]



    def _get_observation(self):
        
        # get entire board
        def get_numeric_board_array(self):
            # 1. Initialize a blank 2D grid matching your board dimensions
            # Shape is (rows, columns) -> (height, width)
            grid = np.zeros((self.height, self.length), dtype=np.int8)
    
            # 3. Loop through and map string symbols to numeric values for the AI
            # for key, val in self.board.items():
            for idx, val in enumerate(self.board[self.tileBeg:self.tileEnd]):
                
                # adjust to 0
                idx -= self.beg
                x, y = self.indexToKey(idx)

                # Map your custom Enum symbols or values to clean integers/floats
                grid[y, x] = TILE_TYPE_MEMBERS.index(val)
    
          
            return grid
        
        return np.concatenate([
            get_numeric_board_array(self).flatten(),
            [self.rockets],
            [self.bombs]
        ])

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
                # 
                # must be called after self.screen(), load images
                for tile in TileType:
                    # load image and scale to cell size, store in cache
                    if tile.image: self.cache[tile] = pygame.transform.scale(pygame.image.load(tile.image).convert_alpha(),(self.cell_size, self.cell_size))

            # draw tiles
            self.screen.fill(self.BLACK)
            for i,value in enumerate(self.getCurrentBoard()):
                
                y = i % self.height
                x = i // self.height
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                self.screen.blit(self.cache[value], rect)
                if not i+self.counter*self.height in (self._visible_tiles): 
                    self.screen.blit(self.dark_overlay, rect)

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
        # index 0
        col = min(int((pixel_x - left) / self.cell_size), self.width - 1)
        row = min(int((pixel_y - top) /  self.cell_size), self.height - 1)
        # cell index of current board
        # cell_index = row * self.width + col
        # tile = {column: col+self.counter, row: row}
        coord = (col+self.counter)*self.height+row

        move_result = self.handleMove([coord,e.button])
        if move_result is None:
            # Use current values so the step function returns valid elements

            info = {"invalid_move": True}
        else:
            # Unpack safely since we confirmed it's not None
            obs, reward, terminated, truncated, info = move_result

        if info: 
            print(info)
        

      
    
    # get all current legal moves and return list [["123,1",1]]
    def getAvailable(self): 
        moves = []
        for i in range(self.height*self.width):
            idx = i+self.counter*self.height
            val = self.board[idx]
            # get all dig moves, no space, no open chests, and only visible 
            # if key == "14,0": print(key,val)
            if val not in (TileType.SPACE,TileType.CHESTOPEN) and self.isTileVisible(idx):
                moves.append([idx,Action.DIG.key])
                # if key == "14,0": print(key,val)
            # rocket and bomb moves are just any space
            elif val == TileType.SPACE and self.isTileVisible(idx):
                if self.rockets > 0 : moves.append([idx, Action.ROCKET.key])
                if self.bombs > 0 :moves.append([idx, Action.BOMB.key])
        # return flat array
        return moves
    
    def onTileDug(self, tile):
        self.board[tile] = TileType.SPACE
        # when a tile becomes space, re-check all its neighbors for visibility
        for neighbor in self.getAdjacentTiles(tile):
            self.isTileVisible(neighbor)  # will add to set if now visible
        # also check the tile itself
        self.isTileVisible(tile)

    # go through entire board at init, get all visible
    # afterwards only trigger ittilevisiible on change
    # Then getAvailable becomes a pure set lookup with no function calls:
    # if connected to 2 adjacent space tiles, the tile is visible
    def isTileVisible(self, tile):
        # if already in set
    
        if tile in self._visible_tiles:
            return True
        # if the tile is space, thats already 1
        visible = False
        if self.board[tile] == TileType.SPACE:
            for tile2 in self.getAdjacentTiles(tile):
                if TileType.SPACE == self.board[tile2]: 
                    self._visible_tiles.add(tile2)
                    visible = True
                    break
            
        else:
            # if tile is not space, check if any connected tile is space then check if that tile has a space connected
         
            for tile2 in self.getAdjacentTiles(tile):
                
                if TileType.SPACE == self.board[tile2] and self.isTileVisible(tile2): 
                    visible = True
                    
                    break
                
        if visible:
            self._visible_tiles.add(tile)
        return visible
    
    # returns list of indexes
    def getAdjacentTiles(self, tile):
        adjacentIndexes = []
        column, row = self.indexToKey(tile)
        # Directions: right, left, down, up
        directions = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        
        for dc, dr in directions:
            # column, row = self.splitCoord(tile)
            

            dc += column
            dr += row
            
            # Skip if out of bounds
            # Visible columns range from counter to counter+width-1
            # Rows range from 0 to height-1
            if dc < self.counter or dc >= self.counter + self.width or dr < 0 or dr >= self.height:
                continue

            # key = self.getCoord(column, row)
            idx = dc * self.height + dr
            # Only add tile if it exists in the map
            # if key in self.board:
            adjacentIndexes.append(idx)
        return adjacentIndexes
    
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
        self._visible_tiles.add(coord)
        # for tile in self.getAdjacentTiles(coord):
        #     self.isTileVisible(tile)

    def checkHidden(self):
        for i in range(self.height*self.width):
            self.isTileVisible(i+self.counter*self.height)
        
        # self.render()

    def handleMove(self, move):
        
        terminated = False
        
        tile, button = move
        tileValue = self.board[tile]
        action = Action.from_button(button)
    
        # cant click opened chests or  tiles
        if tileValue ==TileType.CHESTOPEN or not self.isTileVisible(tile): raise Exception("firstcheck")
            # return self._get_observation(), self.reward, True, False, {"first_check": move}
        self.reward = -1
        if action == Action.ROCKET:
            #  can only rocket on space tile
            if tileValue != TileType.SPACE or self.rockets <= 0: return
            # self.reward += 0.5
            self.rockets -= 1
            column, row = self.indexToKey(tile)
            # set row to spaces
            for addColumn in range(self.width):
                # ignore actiontile
                if self.counter + addColumn == column:
                    continue
                self.setTile((self.counter+addColumn) * self.height + row)
            if self.reward <2: self.reward -=2
            elif self.reward >=5: self.reward +=2
            elif self.reward >=2: self.reward +=1
        elif action == Action.DIG:
            # invalid move
            if tileValue == TileType.SPACE: 
                
                # return 
                raise Exception(f"{move} digspace")
                # return self._get_observation(), self.reward, True, False, {"dug_space": move}
            
            
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

            if self.reward <2: self.reward -=2
            elif self.reward >=5: self.reward +=2
            elif self.reward >=2: self.reward +=1
            
        self.checkHidden()
        self.checkAdvance()
        self.moves.append([self.indexToKey(tile),button])
        

        # if (action == Action.BOMB or action == Action.ROCKET) and self.reward <= 3: self.reward -= 5
        # finalScore = self.score
        # win condition
        
        if self.counter>=self.beg+self.length-self.width:
            eff = self.length/self.score
            self.reward += eff*self.length + self.rockets * 6 + self.bombs * 6
            self.totalReward += self.reward
            info = {"score": self.score,"reward":round(self.reward,2), "move":[self.indexToKey(tile),button],"totalReward":round(self.totalReward,1), "bombs":self.bombs,"rockets":self.rockets, "eff":round(eff,2), "moves":self.moves}
            # if self.screen : print(info)
            self.reset()
            
            terminated = True
            
            return self._get_observation(), self.reward, terminated, False, info
        self.totalReward += self.reward
        info = {"score": self.score,"reward":round(self.reward,2), "move":[self.indexToKey(tile),button], "totalReward":round(self.totalReward,1) , "bombs":self.bombs,"rockets":self.rockets}
        # if self.screen : print(info)
        return self._get_observation(), self.reward, False, False, info
    
    def getInfo():
        return
    
    
    def  getColumn(self,colIndex):
        start = colIndex * self.height
        return self.board[start:start+self.height]
    

    def checkAdvance(self):
        colIndex = self.counter + self.width - 1
        lastColArr = self.getColumn(colIndex)
        
        def advance():
            # print(f'advance:{self.counter}')
            self.counter += 1
            self.reward += 1
            self.checkHidden()
            self.checkAdvance()
            # self.render()
        
        # what if chest at last but has space behind it (not visible)
        if any(
            # if last column has chest, and spaces on the sides of it (only covers visible cells on board)
            self.isChestVisibleForAdvance(colIndex * self.height + row) or
            # if last column has visible space or chest
            ((TileType.SPACE == value or TileType.isChest(value)) and self.isTileVisible(colIndex * self.height + row)) or
            # if last column has space and has chest in front of it, advance
            (TileType.SPACE == value and TileType.isChest(self.board[(colIndex-1)*self.height + row]))
            #
            for row, value in enumerate(lastColArr)
        ):
            advance()

    def isChestVisibleForAdvance(self,tile):
        
        # chest only
        if TileType.isChest(self.board[tile]) :
            # must be adjtiles because it has to be visible
            adjIndexes = self.getAdjacentTiles(tile)
            # col, row = self.splitCoord(tile)
            
            # remove front tile
            frontTile = tile - self.height

            if frontTile in adjIndexes:
                adjIndexes.remove(frontTile)

            for idx in adjIndexes:
                # print(adjIndexes, self.board[idx])
                if self.board[idx]==TileType.SPACE: return True
        return False
      
                
    def nextMove(self): 
        # ["6,0", 1], curr format
        move = nextMoves[map_idx][self.next]
        move[0] = move[0][0]*self.height + move[0][1]
        move_result  = self.handleMove(move)

        if move_result is None:
            info = {"move": nextMoves[map_idx][self.next],"invalid_move": True}
        else:
            # Unpack safely since we confirmed it's not None
            obs, reward, terminated, truncated, info = move_result

        if info: 
            print(info)
    
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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        
                        self.nextMove()



            # Render
            self.render()
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