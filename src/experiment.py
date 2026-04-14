from psychopy import core
from condition import Condition
from objects import Object

class Experiment:
    def __init__(self):
        self.obj = Object()

    def draw_bullseye(self):
        self.obj.bullseye_outer.draw()
        self.obj.bullseye_inner.draw()

    def _trial(self, grid, stim_list):
        # reference phase
        opacity_step = ((100 - 10) / len(stim_list)) / 100
        current_opacity = 1.0
        for idx, s in enumerate(stim_list):
            grid.draw()
            current_opacity = current_opacity - opacity_step
            s.opacity = current_opacity
            s.draw()
            self.draw_bullseye()
            if idx == 0:
                self.obj.sound2.play()
            else:
                self.obj.sound1.play()
            self.obj.win.flip()
            core.wait(2)

        # Imagery Phase
        grid.draw()
        self.draw_bullseye()
        self.obj.win.flip()

        # first loop
        for idx, _ in enumerate(stim_list):
            if idx == 0:
                self.obj.sound2.play()
            else:
                self.obj.sound1.play()
            core.wait(2)

        # second loop
        for idx, _ in enumerate(stim_list):
            if idx == 0:
                self.obj.sound2.play()
            else:
                self.obj.sound1.play()
            core.wait(2)

    def run_trial(self, condition: Condition):
        # clear the variable (just in case)
        grid = None
        stim_list = None
        match condition:
            case Condition.SECTOR:
                grid = self.obj.sector_grid
                stim_list = self.obj.sector_stims.copy()

            case Condition.RING:
                grid = self.obj.ring_grid
                stim_list = self.obj.ring_stims.copy()

            case _:
                pass

        self._trial(grid, stim_list)

    def run_rest(self, n):
        self.draw_bullseye
        self.obj.win.flip()
        core.wait(n)

    def run_experiment(self, trials):
        self.run_rest(1)
        while trials:
            current_trial = trials.pop(0) # from the first to last
            self.run_trial(current_trial)
            self.run_rest(0.5)

    @staticmethod
    def wait_for_n_trs():
        raise NotImplementedError

