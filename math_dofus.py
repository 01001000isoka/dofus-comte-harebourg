import math

MAP_WIDTH = 14  

def build_dofus_grid():
    id_to_coord = {}
    coord_to_id = {}
    for cell_id in range(560):
        x = (cell_id % 14) + (cell_id // 28)
        y = (cell_id // 28) - (cell_id % 14)
        if cell_id % 28 >= 14:
            x += 1
        id_to_coord[cell_id] = (x, y)
        coord_to_id[(x, y)] = cell_id
    return id_to_coord, coord_to_id