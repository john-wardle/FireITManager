"""Canvas configuration constants."""

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor

# ---------------------------------------------------------
# Scene
# ---------------------------------------------------------

SCENE_WIDTH = 20000
SCENE_HEIGHT = 20000

SCENE_RECT = QRectF(
    -SCENE_WIDTH / 2,
    -SCENE_HEIGHT / 2,
    SCENE_WIDTH,
    SCENE_HEIGHT,
)

# ---------------------------------------------------------
# Grid
# ---------------------------------------------------------

MINOR_GRID_SIZE = 20
MAJOR_GRID_SIZE = 100

GRID_MINOR_COLOR = QColor(55, 55, 55)
GRID_MAJOR_COLOR = QColor(80, 80, 80)

# ---------------------------------------------------------
# Zoom
# ---------------------------------------------------------

ZOOM_MIN = 0.10
ZOOM_MAX = 8.00
ZOOM_STEP = 1.15

# ---------------------------------------------------------
# Default Building Dimensions
# ---------------------------------------------------------

DEFAULT_BUILDING_WIDTH = 600
DEFAULT_BUILDING_HEIGHT = 400

# ---------------------------------------------------------
# Device Defaults
# ---------------------------------------------------------

DEFAULT_DEVICE_SIZE = 24

# ---------------------------------------------------------
# Z Order
# ---------------------------------------------------------

Z_BACKGROUND = -100
Z_GRID = -50
Z_BUILDING = 0
Z_DEVICE = 10
Z_TEXT = 20
Z_SELECTION = 100