from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    # Keep these imports available to type checkers, but do not load PsychoPy's
    # OpenGL visual stack while the experiment modules are merely importing.
    from psychopy import visual

@dataclass
class Object:
    window_size: tuple[int, int] = (1080, 720)
    window_fullscr: bool = False
    window_units: str = "pix"

    bullseye_inner_radius: float = 5
    bullseye_outer_radius: float = 8
    bullseye_inner_color: str = "green"
    bullseye_outer_color: str = "black"

    sector_image_dir: str = "../stimuli/sectors_a_pilot"
    sector_image_extension: str = ".png"
    sector_grid_path: str = "../stimuli/sector_grid_a_pilot.png"

    ring_image_dir: str = "../stimuli/rings_d"
    ring_image_extension: str = ".png"
    ring_grid_path: str = "../stimuli/ring_grid_d.png"


    win: visual.Window = field(init=False)
    bullseye_inner: visual.Circle = field(init=False)
    bullseye_outer: visual.Circle = field(init=False)
    sector_stims: list[visual.ImageStim] = field(default_factory=list, init=False)

    SECTORS_COUNTERCLOCKWISE: ClassVar[list[str]] = [
        f"sector_a_{i:02d}" for i in range(12)
    ]
    # Each image starts at ``index * 30°`` and spans 60°, so its centre is
    # ``index * 30° + 30°``.  Start at index 2: sector_a_02 is centred at 90°.
    # Decrementing the index gives a clockwise sweep in the stimulus coordinate
    # system (0° = right, 90° = up).
    SECTOR_START_INDEX: ClassVar[int] = 2
    SECTOR_STEP_DEGREES: ClassVar[float] = 30.0
    SECTOR_WIDTH_DEGREES: ClassVar[float] = 60.0
    SECTORS_CLOCKWISE: ClassVar[list[str]] = [
        # Class-body comprehensions have their own scope, hence the literals
        # here rather than references to the constants immediately above.
        f"sector_a_{(2 - offset) % 12:02d}"
        for offset in range(12)
    ]
    SECTOR_CENTER_DEGREES: ClassVar[list[float]] = [
        ((2 - offset) * 30.0 + 60.0 / 2) % 360
        for offset in range(12)
    ]

    RINGS: ClassVar[list[str]] = ['ring_d_00', 'ring_d_01', 'ring_d_02', 'ring_d_03', 'ring_d_04', 'ring_d_05', 'ring_d_04', 'ring_d_03', 'ring_d_02', 'ring_d_01', 'ring_d_00']

    def __post_init__(self) -> None:
        # Creating an Object is the point at which a display and audio device are
        # actually needed. Deferring this import noticeably shortens startup to
        # the participant dialog and avoids opening the visual stack prematurely.
        from psychopy import sound, visual

        self.win = visual.Window(
            size=self.window_size,
            fullscr=self.window_fullscr,
            units=self.window_units,
            backgroundImage="../stimuli/noise_gaussian_1920x1080.png"
        )

        # Create drawables using the instance window
        self.bullseye_inner = visual.Circle(
            self.win,
            radius=self.bullseye_inner_radius,
            fillColor=self.bullseye_inner_color,
            lineColor=None,
        )
        self.bullseye_outer = visual.Circle(
            self.win,
            radius=self.bullseye_outer_radius,
            fillColor=self.bullseye_outer_color,
            lineColor=None,
        )

        self.sound1 = sound.Sound(value = 440, secs = 0.250, stereo=True)
        self.sound2 = sound.Sound(value = 880, secs = 0.250, stereo=True)

        self.sector_stims = [
            visual.ImageStim(
                self.win,
                image=f"{self.sector_image_dir}/{sector_name}{self.sector_image_extension}",
                opacity = 1.0
            )
            for sector_name in self.SECTORS_CLOCKWISE
        ]
        # Kept alongside ``sector_stims`` so trial code can log and cue the
        # exact polar-angle position without relying on list indices.
        self.sector_center_degrees = self.SECTOR_CENTER_DEGREES.copy()

        self.sector_grid = visual.ImageStim(
            self.win,
            image=self.sector_grid_path
        )


        self.ring_stims = [
            visual.ImageStim(
                self.win,
                image=f"{self.ring_image_dir}/{ring_name}{self.ring_image_extension}",
                opacity = 1.0
            )
            for ring_name in self.RINGS
        ]


        self.ring_grid = visual.ImageStim(
            self.win,
            image=self.ring_grid_path
        )
