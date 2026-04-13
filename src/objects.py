from dataclasses import dataclass, field
from typing import ClassVar

from matplotlib import image
from psychopy import visual


@dataclass
class Object:
    window_size: tuple[int, int] = (500, 500)
    window_fullscr: bool = False
    window_units: str = "pix"

    bullseye_inner_radius: float = 5
    bullseye_outer_radius: float = 8
    bullseye_inner_color: str = "green"
    bullseye_outer_color: str = "black"

    sector_image_dir: str = "../stimuli/sectors_a_pilot"
    sector_image_extension: str = ".png"
    sector_grid_path: str = "../stimuli/sector_grid_a_pilot.png"

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

    def __post_init__(self) -> None:
        self.win = visual.Window(
            size=self.window_size,
            fullscr=self.window_fullscr,
            units=self.window_units,
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

        self.sector_stims = [
            visual.ImageStim(
                self.win,
                image=f"{self.sector_image_dir}/{sector_name}{self.sector_image_extension}",
            )
            for sector_name in self.SECTORS_CLOCKWISE
        ]

        self.sector_grid = visual.ImageStim(
            self.win,
            image=self.sector_grid_path
        )

if __name__ == "__main__":
    from psychopy import core

    obj = Object()
    obj.bullseye_inner.draw()
    obj.bullseye_outer.draw()
    obj.win.flip()
    core.wait(2)
