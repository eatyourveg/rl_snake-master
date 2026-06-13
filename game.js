import {nextMoves, hiddenTiles2025MAY, coords} from './const.js';

// https://www.dragoncompanion.com/simulation.html
// https://treasuredig3rdmap.luna-videogaming.workers.dev/
// https://www.youtube.com/watch?v=kH1oVioR4rM
// Q-Learning Agent with localStorage support
class QLearning {
    constructor(lr = 0.1, gamma = 0.9, epsilon = 0.1) {
      this.q = new Map();
      this.lr = lr;
      this.gamma = gamma;
      this.epsilon = epsilon;
      this.difficulty = 'intermediate';
    }
  
    getQ(state) {
      if (!this.q.has(state)) this.q.set(state, Array(100).fill(0));
      return this.q.get(state);
    }
  
    getAction(state, available) {
 
        // Use minimax for perfect play
      return this.getMinimaxAction(state, available);
      
  
      // Intermediate: epsilon-greedy
      if (Math.random() < this.epsilon) {
        return available[~~(Math.random() * available.length)];
      }
      const q = this.getQ(state);
      return available.reduce((best, a) => q[a] > q[best] ? a : best, available[0]);
    }
  
    getMinimaxAction(state, available) {
      let bestScore = -Infinity;
      let bestMove = available[0];
  
      for (const move of available) {
        const newState = state.substring(0, move) + 'O' + state.substring(move + 1);
        const score = this.minimax(newState, 0, false);
        if (score > bestScore) {
          bestScore = score;
          bestMove = move;
        }
      }
      return bestMove;
    }
  
    minimax(state, depth, isMaximizing) {
      const winner = this.checkWinnerStatic(state);
      if (winner === 'O') return 10 - depth;
      if (winner === 'X') return depth - 10;
      if (winner === 'draw') return 0;
  
      const available = [...state].map((c, i) => c === '-' ? i : null).filter(x => x !== null);
      
      if (isMaximizing) {
        let best = -Infinity;
        for (const move of available) {
          const newState = state.substring(0, move) + 'O' + state.substring(move + 1);
          best = Math.max(best, this.minimax(newState, depth + 1, false));
        }
        return best;
      } else {
        let best = Infinity;
        for (const move of available) {
          const newState = state.substring(0, move) + 'X' + state.substring(move + 1);
          best = Math.min(best, this.minimax(newState, depth + 1, true));
        }
        return best;
      }
    }
  
    checkWinnerStatic(state) {
      const patterns = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
      for (const p of patterns) {
        if (state[p[0]] !== '-' && state[p[0]] === state[p[1]] && state[p[1]] === state[p[2]]) {
          return state[p[0]];
        }
      }
      return state.includes('-') ? null : 'draw';
    }
  
    update(s, a, r, s2, available2) {
      const q = this.getQ(s);
      const maxQ2 = available2.length ? Math.max(...available2.map(a => this.getQ(s2)[a])) : 0;
      q[a] += this.lr * (r + this.gamma * maxQ2 - q[a]);
    }
  
    decay() {
      this.epsilon = Math.max(0.01, this.epsilon * 0.995);
    }
  
    reset() {
      this.q.clear();
      this.epsilon = 0.1;
    }
  
    // localStorage methods
    save() {
      const data = {
        q: Array.from(this.q.entries()),
        lr: this.lr,
        gamma: this.gamma,
        epsilon: this.epsilon,
        difficulty: this.difficulty
      };
      localStorage.setItem('tictactoe_ai', JSON.stringify(data));
    }
  
    load() {
      const saved = localStorage.getItem('tictactoe_ai');
      if (!saved) return false;
      
      try {
        const data = JSON.parse(saved);
        this.q = new Map(data.q);
        this.lr = data.lr;
        this.gamma = data.gamma;
        this.epsilon = data.epsilon;
        this.difficulty = data.difficulty || 'intermediate';
        return true;
      } catch (e) {
        console.error('Failed to load AI state:', e);
        return false;
      }
    }
  
    clearStorage() {
      localStorage.removeItem('tictactoe_ai');
    }
  }
  
  
// legend
// A : Space ??
// H : Hidden Space
// G : Grass
// B : Blue Star
// Y : Yellow Star
// S : Space
// R : Rocket
// O : Bomb
// Z : Chest...2nd value has rocket/bomb, CB, CR
// X : also chest, source had Z as closed chests and X as open chests, but we can just use Z for all chests and differentiate with hidden/visible



const gridColumns = 8;
const gridRows = 6;
const cellCount = gridColumns*gridRows
const debug = false

function jsonToMapDeep(obj) {
  
  const map = new Map()
  for (const [key, value] of Object.entries(obj)) {
    for(const [k, v] of Object.entries(value)){
      map.set(`${key},${k}`, v);
    }
    
  }
  return map;
}



const TILES = {
  SPACE: { symbol: 'A', image: 'assets/dirt_dt.png' },
  HIDDEN: { symbol: 'H', image: 'assets/hidden_dt.png' },
  GRASS: { symbol: 'G', image: 'assets/grass_dt.png' },
  STARB: { symbol: 'B', image: 'assets/blue_dt.png' , action: () => game.stats.StarBlue++},
  STARY: { symbol: 'Y', image: 'assets/yellow_dt.png', action  : () => game.stats.StarYellow++},
  STONE: { symbol: 'S', image: 'assets/stone_dt.png' },
  ROCKET: { symbol: 'R', image: 'assets/rocket_dt.png', action: () => game.stats.Rockets++},
  BOMB: { symbol: 'O', image: 'assets/bomb_dt.png' , action: () => game.stats.Bombs++},
  CHESTR: { symbol: 'Z', image: 'assets/chest_dt.png' },
  CHESTB: { symbol: 'X', image: 'assets/chest_dt.png' }
  
};


const MOUSE_BUTTONS = {
  LEFT: 0,
  MIDDLE: 1,
  RIGHT: 2
};




  // Tic-Tac-Toe Game with difficulty levels and persistence
  
  class TicTacToe {
    constructor() {
      
      // this.board = '---------';
      this.ai = new QLearning();
      this.stats = { played: 0, aiWins: 0, playerWins: 0, draws: 0 };
      this.training = false;
      this.gameOver = false;
      this.cache = {}
      this.canvas = document.getElementById('gameCanvas');
      this.ctx = this.canvas.getContext('2d');
      this.cellSize = 80
          
      this.canvas.addEventListener('mousedown', (event) => {
        event.preventDefault(); 
        this.handleClick(event)
      });
      this.canvas.addEventListener('contextmenu', (event) => {
        event.preventDefault(); 
      });
      this.initControls();
      this.loadState();
      
      this.init();

      
      // console.log(this.map)
    }

    async init() {
      this.counter = 0
      this.moves = 0
      this.next = 0
      this.stats = { Bombs: 0, Rockets: 0, StarBlue: 0, StarYellow: 0 }

      this.map = jsonToMapDeep(coords);
      
      // convert all tiles in hiddenTiles2025MAY to H in the map, only up to 999
      for (const val of hiddenTiles2025MAY) {
        // this.setTile(val,TILES.HIDDEN)
        this.map.set(val, TILES.HIDDEN.symbol)
      }
      

      
      // col 1 = col 1000
      // because only up to 999. copy the first 1000 tiles to columns 1000-1999 to create a
      const origKeys = [...this.map.keys()]
      for(let i = 1; i <= 1000; i++){
        const key = origKeys[i]
        const value = this.map.get(key)
        const [column, row] = this.splitCoord(key)
        const newKey = this.getCoord(column+999, row)
        this.map.set(newKey, value)
      }

      // this.map = new Map([...this.map].slice(0, 120))
      await this.loadImages();
      this.draw()
    }
    
    /**
     * Sets a tile to a specified type, preventing overwrite of chest tiles.
     * @param {string} coord - The tile key in format "column,row"
     * @param {string} [type='A'] - The tile type to set (defaults to empty space 'A')
     */

    getTileType = (type) => Object.values(TILES).find(tile => tile.symbol === type);
    setTile(coord, targetSymbol = TILES.SPACE) {
      
      const currTile = this.getTileType(this.map.get(coord));
      // If the tile is already the desired symbol, do nothing
      // Prevent overwriting chest tiles (they are permanent)
      if (currTile === targetSymbol || currTile === TILES.CHESTB || currTile === TILES.CHESTR) return;

      currTile.action?.();
        
      // Update the tile in the map
      this.map.set(coord, targetSymbol.symbol);
    }

     /**
     * Creates a coord by combining column and row coordinates.
     * @param {number} column - The column coordinate
     * @param {number} row - The row coordinate
     * @returns {string} A key in format "column,row" used to identify tiles in the map
     */
     getCoord(column, row) {
      return `${column},${row}`;
    }

    /**
     * Splits a tile coordinate string into column and row components.
     * @param {string} coord - The tile key in format "column,row"
     * @returns {Array<string>} An array where [0] is the column and [1] is the row as strings
     */
    splitCoord(coord) {
      // console.log(coord)
      return coord.split(',').map(Number);
    }

  


    
   

    


    loadImages() {
      const {cache} = this
      const promises = []
      Object.values(TILES).forEach (tile  =>{ 

        const src = tile.image;
      
        if (src) {
          const img = Object.assign(new Image(), { src });
          cache[tile.symbol] = img;
          const p = new Promise(resolve => {
            img.onload = resolve;
          });
          promises.push(p)
        }
      })
      return Promise.all(promises)
    }
    initControls() {
      ['learningRate', 'discountFactor', 'explorationRate'].forEach(id => {
        const el = document.getElementById(id);
        el.oninput = e => {
          const val = parseFloat(e.target.value);
          document.getElementById(id + 'Value').textContent = val.toFixed(2);
          if (id === 'learningRate') this.ai.lr = val;
          if (id === 'discountFactor') this.ai.gamma = val;
          if (id === 'explorationRate') this.ai.epsilon = val;
          this.saveState();
        };
      });
    }
  
    setDifficulty(level) {
      this.ai.difficulty = level;
      
      // Update button styles
      ['beginner', 'intermediate', 'expert'].forEach(diff => {
        const btn = document.getElementById(`diff${diff.charAt(0).toUpperCase() + diff.slice(1)}`);
        if (diff === level) {
          btn.className = 'py-2 px-4 rounded-lg font-semibold text-sm transition-all bg-purple-600 text-white border-2 border-purple-600';
        } else {
          btn.className = 'py-2 px-4 rounded-lg font-semibold text-sm transition-all bg-white text-gray-700 hover:bg-gray-100';
        }
      });
  
      // Adjust AI parameters based on difficulty
      if (level === 'beginner') {
        this.setStatus('🌱 Beginner mode: AI makes more mistakes');
      } else if (level === 'intermediate') {
        this.setStatus('🎯 Medium mode: Balanced AI using Q-learning');
      } else {
        this.setStatus('🔥 Expert mode: Perfect AI using minimax algorithm');
      }
  
      this.saveState();
    }

    // draw image from cache based on symbol
    drawImage(symbol, x, y) {
      const {cellSize,ctx,cache} = this
      
      const img = cache[symbol]
      console.log(cache,symbol)
      if (img && img.complete && !debug) {
        ctx.drawImage(img, x - cellSize/2, y - cellSize/2, cellSize, cellSize);
      } else {
        ctx.font = '30px Arial';
        ctx.fillStyle = 'black';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(symbol, x, y);
      }
    }

    /**
     * Retrieves the current board state as an array.
     * @returns {Array} [coords,value] for the current visible board based on the counter position, sliced from the map entries.
     */
    getCurrentBoard(){
      return [...this.map.entries()].slice(this.counter*gridRows, this.counter*gridRows + cellCount)
    }


   
    /**
     * Returns an array of adjacent tile keys (up, down, left, right) for a given tile.
     * Only includes tiles that are within the current visible board bounds and exist in the map.
     * @param {string} tile - The tile key in format "column,row"
     * @returns {Array<string>} Array of adjacent tile keys that are in bounds and exist
     */
    getAdjacentTiles(tile){
      const adjacent = [];
      // Directions: right, left, down, up
      const directions = [[1,0],[-1,0],[0,1],[0,-1]];
      
      for(const [dc, dr] of directions){
        let [column, row] = this.splitCoord(tile);
        column += dc;
        row += dr;

        // Skip if out of bounds
        // Visible columns range from counter to counter+gridColumns-1
        // Rows range from 0 to gridRows-1
        if(column < this.counter || column >= this.counter + gridColumns || row < 0 || row >= gridRows) {
          continue;
        }

        const key = this.getCoord(column, row);
        // Only add tile if it exists in the map
        if(this.map.get(key)) {
          adjacent.push(key);
        }
      }
      
      return adjacent;
    }

    getElementsStartingWith(prefix) {
      const matches = [];
      
      for (const [key, value] of this.map.entries()) {
        if (key.startsWith(prefix)) {
          matches.push({ key, value });
        }
      }
      
      return matches;
    }

    checkHidden(){
      // get all hidden tiles in the current board, and if any are adjacent to a revealed tile, reveal them
      this.getCurrentBoard().forEach(([tile,value]) => {
        if(value === TILES.HIDDEN.symbol && this.isTileVisible(tile)){
          this.setTile(tile)
          console.log(`Revealed "H" at ${tile}`);
        }
      })
    }

    /**
     * Retrieves a column from the board map by index.
     * @param {number} [colIndex] - The column index to retrieve. Defaults to the last visible column (counter + gridColumns - 1).
     * @returns {Array<[string, string]>} An array of [key, value] entries representing the tiles in the specified column.
     */
    getColumn(colIndex) {
      colIndex = colIndex || this.counter + gridColumns - 1
      return   [...this.map.entries()].slice(colIndex*gridRows, colIndex*gridRows + gridRows)
    }

    // getCurrentBoard(){
    //   return [...this.map.entries()].slice(this.counter*gridRows, this.counter*gridRows + cellCount)
    // }
    
    
    // checks if last row has a visible tile. If so, advance the board by one column and redraw.
    checkAdvance(){
      const lastColArr = this.getColumn()

      const advance = () => {
        console.log("advance: ", this.counter)
        this.counter++
         // reveal any hidden tiles in the new column
         this.checkHidden()
         this.draw()
      }
      // if any tile is A or (chest and visible), advance the board. otherwise
      if(lastColArr.some(([key,value]) => value === TILES.SPACE.symbol || (value === TILES.CHESTB.symbol || value === TILES.CHESTR.symbol) && this.isTileVisible(key))){
        advance()        
      } else if (lastColArr.some(([key,value]) => value === 'H')) {

        // console.log(lastColArr.find(([key,value]) => value=== TILES.HIDDEN.symbol))
        const hiddenTiles = lastColArr.filter(([key,value]) => value=== TILES.HIDDEN.symbol)
        for (const [hidden] of hiddenTiles) {
          const chest = this.getAdjacentTiles(hidden).find(value => this.map.get(value) === TILES.CHESTB.symbol || this.map.get(value) === TILES.CHESTR.symbol)
          // console.log(hidden,chest)
          // console.log(this.getAdjacentTiles(hidden))
          if(!chest) continue

          const hiddenCoords = this.splitCoord(hidden)
          const chestCoords = this.splitCoord(chest)
          
          if(Math.abs(hiddenCoords[1]-chestCoords[1])<=1) {
            console.log(`Advanced at ${hidden} due to top/bottom chest at ${chest}`);
            advance()
            return
          } else if (hiddenCoords[0]-chestCoords[0]===1) {
            console.log(`Advanced at hidden ${hidden} due to behind chest at ${chest}`);
            advance()
            return
          }
        
        }
        // console.log(this.getAdjacentTiles(hidden).find(([key,value]) => value === TILES.CHESTB.symbol || value === TILES.CHESTR.symbol))
        
        
    

      }
    }

    

    /**
     * Converts a grid index to x and y coordinates
     * @param {number} index - The index position in the grid
     * @returns {{x: number, y: number}} An object containing x and y pixel coordinates
     */
    getCoordinatesFromIndex(index){
      const y = ~~(index % gridRows) * this.cellSize;
      const x = ~~(index / gridRows) * this.cellSize;
      return {x:x, y:y}
    }

    draw() {
      const { ctx, canvas, cellSize ,cache} = this;
      this.checkHidden()
      this.checkAdvance()
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
   

      this.getCurrentBoard().forEach((tile,i) => {
        // const { ctx, cellSize ,cache} = this;
        const symbol = tile[1];
        // 0/00,1/01,2/02,3/03
        // 3. Draw image at the canvas center (width/2, height/2)
        const pos = this.getCoordinatesFromIndex(i)

        const img = cache[symbol]
        if (img && img.complete && !debug) {
          
          ctx.drawImage(img, pos.x, pos.y, cellSize, cellSize);
          // draw semi-transparent black overlay if tile is hidden and not space
          if(symbol!==TILES.SPACE.symbol && !this.isTileVisible(tile[0])){
            ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
            ctx.fillRect(pos.x, pos.y, cellSize, cellSize);
          }
        }
      })

      // number header
      for (let i = 0; i < gridColumns; i++) {
        ctx.font = '20px Arial';
        ctx.fillStyle = "white";
        ctx.fillText(this.counter + i, i * cellSize + cellSize / 2, 15);
      }
      
      // draw last move. needs to happen after drawing board
      const i = this.getCurrentBoard().findIndex(([key]) => key === this.lastMove)
      const pos = this.getCoordinatesFromIndex(i)
      ctx.fillStyle = "red";
      ctx.fillRect(pos.x, pos.y, 30, 30);

      
      // console.log(this.getCurrentBoard())
   
      this.updateStats();
      // const winner = this.checkWinner();
      // if (winner?.line) this.drawWinLine(winner.line);
    }

  

    isTileVisible(tile){
      // console.log(`Tile ${tile} is "${this.map.get(tile)}" and adjacent tiles are:`, this.getAdjacentTiles(tile).map(t => `${t}:"${this.map.get(t)}"`))
      return this.getAdjacentTiles(tile).some(tile2 => 
        this.map.get(tile2) === TILES.SPACE.symbol 
        // this.map.get(tile2) === 'A' || this.map.get(tile2) === 'Z' || this.map.get(tile2) === 'X' 
      )
    }
    isMoveVisible(tile){
      // if the tile is already revealed, it's visible
      if(this.map.get(tile) === TILES.SPACE.symbol) return true

      // if adjacent to a revealed tile, it's visible
      return this.isTileVisible(tile)
    }

    handleMove(tile,e){

      if (e.button === MOUSE_BUTTONS.RIGHT) {
        // can only rocket on revealed tile
        if(this.map.get(tile) !== TILES.SPACE.symbol) return
        
        const [column, row] = this.splitCoord(tile)
        // set row to spaces
        for(let i = 0; i<gridColumns;i++){
          if(this.counter+i == column) continue
          this.setTile(this.getCoord(this.counter+i, row))
        }
        console.log(`Rocket used at ${[tile]}`);
      } else if (e.button === MOUSE_BUTTONS.LEFT){ 
        // do nothing if tile is revealed
        this.getAvailable()
        if(this.map.get(tile) === TILES.SPACE.symbol) return
        if(this.map.get(tile) === TILES.STONE.symbol) this.moves++
        this.setTile(tile)
        
        
      } else if (e.button === MOUSE_BUTTONS.MIDDLE){
        if(this.map.get(tile) !== TILES.SPACE.symbol) return
        let arr = []
        // get adjacent tiles, then get their adjacent tiles
        this.getAdjacentTiles(tile).forEach(adj => {
          arr.push(adj)
          this.getAdjacentTiles(adj).forEach(adj2 => {
            arr.push(adj2)
            
          })
        })
        arr.forEach(tile => {
          this.setTile(tile)
          // console.log(tile)
        })
        console.log(`Bomb used at ${[tile]}`);
      }
      this.lastMove = tile
      this.moves++
    
      
    }
  
    handleClick(e) {
      // if (this.gameOver || this.training) return;
      
      const rect = this.canvas.getBoundingClientRect();
      const col = ~~((e.clientX - rect.left) / rect.width * gridColumns);
      const row = ~~((e.clientY - rect.top) / rect.height * gridRows);
      // const idx = row * gridColumns + col;
      // const tile = {column: col+this.counter, row: row}
      const coord = this.getCoord(col+this.counter, row)
      const currVal = this.map.get(coord)
      console.log(`${Object.entries(MOUSE_BUTTONS).find(([key,value]) => value==e.button)[0]} cell: (${coord}) "${currVal}"`);
      if(currVal === TILES.CHESTB.symbol || currVal === TILES.CHESTR.symbol || currVal === TILES.HIDDEN.symbol || !this.isMoveVisible(coord)) return
      
      this.handleMove(coord,e)
      this.draw()
    }
  
    move(idx, player) {
      if (this.board[idx] !== '-' || this.gameOver) return false;
      this.board = this.board.substring(0, idx) + player + this.board.substring(idx + 1);
      this.draw();
      this.checkGameOver();
      return true;
    }

    sim() {
      const level = Number(prompt("how many levels"))
      for(let i = 0; i<level; i++){
        this.nextMove();
      }
      
    }
    nextMove() {
      
      this.handleMove(nextMoves[this.next][0], {button: nextMoves[this.next][1]})
      this.draw()
      console.log(`Next: ${nextMoves[this.next][0]} ${Object.entries(MOUSE_BUTTONS).find(([key,value]) => value==nextMoves[this.next][1])[0]}. Next move: ${nextMoves[this.next+1]}`)
      
      const pos = this.getCoordinatesFromIndex(this.getCurrentBoard().findIndex(([key]) => key === nextMoves[this.next+1][0]))
      // this.ctx.fillStyle = "green";
      // this.ctx.fillRect(pos.x, pos.y, 30, 30);
      // this.ctx.drawImage(, pos.x + this.cellSize/2, pos.y + this.cellSize/2)
      let img = null
      switch(nextMoves[this.next+1][1]){
        case MOUSE_BUTTONS.LEFT: img = this.cache['H']; break;
        case MOUSE_BUTTONS.RIGHT: img = this.cache['R']; break;
        case MOUSE_BUTTONS.MIDDLE: img = this.cache['O']; break;
      }
      
      this.ctx.drawImage(img, pos.x, pos.y, 30, 30);
      this.next++

    }
  
    aiMove() {
      if (this.counter===10) return;
      
      const state = this.map;
      const available = this.getAvailable();
      const action = this.ai.getAction(state, available);
      
      // this.move(action, 'O');
      this.setTile(action)
      
      // const winner = this.checkWinner();
      // const reward = winner?.winner === 'O' ? 1 : winner?.winner === 'X' ? -1 : 0;
      const reward = this.counter
      this.ai.update(state, action, reward, this.board, this.getAvailable());
      console.log(this.ai.getQ())
      
    }
  
    getAvailable() {
      return this.getCurrentBoard().filter(([key,val]) => val !== TILES.SPACE.symbol && this.isTileVisible(key))
      // console.log(this.getCurrentBoard().filter(([key,val]) => val !== TILES.SPACE.symbol && this.isTileVisible(key)))
      // return [...this.board].map((c, i) => c === '-' ? i : null).filter(x => x !== null);
    }
  
    checkWinner() {
      const patterns = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
      for (const p of patterns) {
        if (this.board[p[0]] !== '-' && 
            this.board[p[0]] === this.board[p[1]] && 
            this.board[p[1]] === this.board[p[2]]) {
          return { winner: this.board[p[0]], line: p };
        }
      }
      return this.board.includes('-') ? null : { winner: 'draw', line: null };
    }
  
    checkGameOver() {
      const result = this.checkWinner();
      if (!result) return;
  
      this.gameOver = true;
      this.stats.played++;
  
      if (result.winner === 'X') {
        this.stats.playerWins++;
        if (!this.training) this.setStatus('🎉 You win!');
      } else if (result.winner === 'O') {
        this.stats.aiWins++;
        if (!this.training) this.setStatus('🤖 AI wins!');
      } else {
        this.stats.draws++;
        if (!this.training) this.setStatus('🤝 Draw!');
      }
  
      if (!this.training) {
        this.updateStats();
        this.saveState();
      }
    }
  
    setStatus(msg) {
      document.getElementById('gameStatus').textContent = msg;
    }
  
    updateStats() {
      document.getElementById('counter').textContent = this.counter;
      document.getElementById('moves').textContent = this.moves;
      document.getElementById('simMoves').textContent = this.next;
      document.getElementById('stats').innerHTML = Object.entries(this.stats).map(([key,value]) => `${key}: ${value}`).join('<br>')
      // document.getElementById('aiWins').textContent = this.stats.aiWins;
      // document.getElementById('playerWins').textContent = this.stats.playerWins;
      // document.getElementById('draws').textContent = this.stats.draws;
      // document.getElementById('statesLearned').textContent = this.ai.q.size;
      
      // const winRate = this.stats.played ? (this.stats.aiWins / this.stats.played * 100).toFixed(1) : 0;
      // document.getElementById('winRate').textContent = `${winRate}%`;
    }
  
    reset() {
      // this.board = '---------';
      // this.gameOver = false;
      // this.draw();
      // this.setStatus('Your turn! (X)');

      this.init()
      
    }
  
    resetAI() {
      if (confirm('Reset AI memory? All progress will be lost.')) {
        this.ai.reset();
        this.ai.clearStorage();
        this.stats = { played: 0, aiWins: 0, playerWins: 0, draws: 0 };
        this.updateStats();
        this.reset();
        this.setStatus('AI memory reset!');
        localStorage.removeItem('tictactoe_stats');
      }
    }
  
    async startTraining() {
      this.training = true;
      document.getElementById('trainingIndicator').classList.remove('hidden');
      
      const originalEpsilon = this.ai.epsilon;
      this.ai.epsilon = 0.3;
  
      for (let i = 0; i < 1000; i++) {
        await this.trainGame();
        this.ai.decay();
        if (i % 50 === 0) {
          document.getElementById('trainingProgress').textContent = `${i + 1}/1000`;
          await new Promise(r => setTimeout(r, 0));
        }
      }
  
      this.ai.epsilon = originalEpsilon;
      this.training = false;
      document.getElementById('trainingIndicator').classList.add('hidden');
      this.updateStats();
      this.reset();
      this.setStatus('Training complete!');
      this.saveState();
    }
  
    async trainGame() {
      this.board = '---------';
      this.gameOver = false;
      const moves = [];
  
      while (!this.gameOver && moves.length < 9) {
        const state = this.board;
        const available = this.getAvailable();
        const action = this.ai.getAction(state, available);
        const player = moves.length % 2 === 0 ? 'X' : 'O';
        
        moves.push({ state, action, player });
        this.move(action, player);
      }
  
      const winner = this.checkWinner();
      moves.forEach(m => {
        const reward = winner?.winner === m.player ? 1 : winner?.winner && winner.winner !== m.player ? -1 : 0;
        this.ai.update(m.state, m.action, reward, this.board, []);
      });
    }
  
    // Save state to localStorage
    saveState() {
      this.ai.save();
      localStorage.setItem('tictactoe_stats', JSON.stringify(this.stats));
    }
  
    // Load state from localStorage
    loadState() {
      const loaded = this.ai.load();
      if (loaded) {
        const savedStats = localStorage.getItem('tictactoe_stats');
        if (savedStats) {
          this.stats = JSON.parse(savedStats);
        }
        this.updateStats();
        this.setDifficulty(this.ai.difficulty);
        
        // Update sliders
        document.getElementById('learningRate').value = this.ai.lr;
        document.getElementById('learningRateValue').textContent = this.ai.lr.toFixed(2);
        document.getElementById('discountFactor').value = this.ai.gamma;
        document.getElementById('discountFactorValue').textContent = this.ai.gamma.toFixed(2);
        document.getElementById('explorationRate').value = this.ai.epsilon;
        document.getElementById('explorationRateValue').textContent = this.ai.epsilon.toFixed(2);
        
        console.log('✓ Loaded AI state from localStorage');
      }
    }
  }
  // Initialize game
  let game;
  window.addEventListener('DOMContentLoaded', async () => {
    game = new TicTacToe();
  });
  document.getElementById('reset-btn').addEventListener('click', () => {
    game.reset();
  });
  document.getElementById('next-btn').addEventListener('click', () => {
    game.nextMove();
  });
  document.getElementById('sim-btn').addEventListener('click', () => {
    game.sim();
  });
  document.getElementById('aiMove-btn').addEventListener('click', () => {
    game.aiMove();
  });
