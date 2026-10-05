from config import REF_HEIGHT, REF_WIDTH


class LayoutScaler:
    def __init__(self, ref_width: float = REF_WIDTH, ref_height: float = REF_HEIGHT):
        self.ref_width = ref_width
        self.ref_height = ref_height
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    def update(self, widget_width: float, widget_height: float):
        scale_x = widget_width / self.ref_width
        scale_y = widget_height / self.ref_height

        self.scale = min(scale_x, scale_y)
        self.offset_x = (widget_width - (self.ref_width * self.scale)) / 2.0
        self.offset_y = (widget_height - (self.ref_height * self.scale)) / 2.0

    @property
    def center_x(self) -> float:
        return self.offset_x + (self.ref_width * self.scale) / 2.0

    @property
    def center_y(self) -> float:
        return self.offset_y + (self.ref_height * self.scale) / 2.0
