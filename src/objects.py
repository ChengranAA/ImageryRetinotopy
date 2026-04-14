from dataclasses import dataclass, field
from typing import ClassVar
from psychopy import visual, sound

@dataclass
class Object:
    window_size: tuple[int, int] = (1080, 720)
    window_fullscr: bool = True
    window_units: str = "pix"

    bullseye_inner_radius: float = 5
    bullseye_outer_radius: float = 8
    bullseye_inner_color: str = "green"
    bullseye_outer_color: str = "black"

    sector_image_dir: str = "../stimuli/sectors_a_pilot"
    sector_image_extension: str = ".png"
    sector_grid_path: str = "../stimuli/sector_grid_a_pilot.png"

    ring_image_dir: str = "../stimuli/sectors_d"
    ring_image_extension: str = ".png"
    ring_grid_path: str = "../stimuli/sector_grid_d.png"


    win: visual.Window = field(init=False)
    bullseye_inner: visual.Circle = field(init=False)
    bullseye_outer: visual.Circle = field(init=False)
    sector_stims: list[visual.ImageStim] = field(default_factory=list, init=False)

    SECTORS_COUNTERCLOCKWISE: ClassVar[list[str]] = [
        f"sector_a_{i:02d}" for i in range(12)
    ]
    SECTORS_CLOCKWISE: ClassVar[list[str]] = [
        SECTORS_COUNTERCLOCKWISE[0],
        *SECTORS_COUNTERCLOCKWISE[:0:-1],
    ]

    _RINGS: ClassVar[list[str]] = [
        f"sector_d_{i:02d}" for i in range(5)
    ]
    _REVERSE_RINGS: ClassVar[list[str]] = _RINGS.copy()
    _REVERSE_RINGS.pop()
    _REVERSE_RINGS.reverse()

    RINGS: ClassVar[list[str]] = _RINGS + _REVERSE_RINGS

    def __post_init__(self) -> None:
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

if __name__ == "__main__":
    from psychopy import core

    obj = Object()
    obj.bullseye_inner.draw()
    obj.bullseye_outer.draw()
    obj.win.flip()
    core.wait(2)
