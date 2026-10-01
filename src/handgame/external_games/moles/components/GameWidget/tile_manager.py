from PySide6.QtCore import QTimer

from config import BASE_TILE_POSITIONS, MAX_OFFSET_Y
from ..tile import Tile


class TileManager:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.tiles = []
        self._init_tiles()

    def _init_tiles(self):
        for _ in BASE_TILE_POSITIONS:
            box = Tile(parent=self.parent)
            box.show()
            box.raise_()
            self.tiles.append(box)

    def update_positions(self, scaler, bg_y: float):
        remaining_offset_y = MAX_OFFSET_Y - bg_y

        for box, (bx, by, bw, bh) in zip(self.tiles, BASE_TILE_POSITIONS):
            current_by = by + remaining_offset_y

            nx = int(scaler.offset_x + (bx * scaler.scale))
            ny = int(scaler.offset_y + (current_by * scaler.scale))
            nw = int(bw * scaler.scale)
            nh = int(bh * scaler.scale)

            box.setGeometry(nx, ny, nw, nh)

    def reset_all(self):
        for box in self.tiles:
            if hasattr(box, "reset_tile"):
                box.reset_tile()
