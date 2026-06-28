import re
import json
from bs4 import BeautifulSoup

# Load your HTML file
with open("_1.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# Char mapping configuration
char_to_tile = {
    'A': 'TileType.SPACE', 'H': 'TileType.HIDDEN', 'G': 'TileType.GRASS',
    'B': 'TileType.STARB', 'Y': 'TileType.STARY',  'S': 'TileType.STONE',
    'R': 'TileType.ROCKET', 'O': 'TileType.BOMB',  'Z': 'TileType.CHESTR',
    'X': 'TileType.CHESTB', 'C': 'TileType.CHESTOPEN'
}

# Grouping dictionary: { col_idx: { row_idx: tile_type } }
grid_data = {}

# Find all grid cell elements with an id matching "cell-row-col"
cells = soup.find_all(id=re.compile(r"^cell-\d+-\d+"))

for cell in cells:
    cell_id = cell.get("id")  # e.g., "cell-0-696"
    char = cell.get("data-orig-char", "A") # Default to SPACE if empty
    
    # Extract row and column numbers
    _, row, col = cell_id.split("-")
    
    # Resolve the TileType string representation
    tile_enum_str = char_to_tile.get(char, "TileType.SPACE")
    
    # Initialize column dictionary if not exists
    if col not in grid_data:
        grid_data[col] = {}
        
    grid_data[col][row] = tile_enum_str

# Print out a snippet or save the raw formatted string to a Python source file
output_lines = ["grid = {"]
for col in sorted(grid_data.keys(), key=int):
    output_lines.append(f'    "{col}": {{')
    for row in sorted(grid_data[col].keys(), key=int):
        output_lines.append(f'        "{row}": {grid_data[col][row]},')
    output_lines.append('    },')
output_lines.append("}")

# Write code output to a file
with open("parsed_grid.py", "w") as out_f:
    out_f.write("\n".join(output_lines))

print("Grid successfully parsed and written to parsed_grid.py!")