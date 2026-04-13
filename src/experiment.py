from psychopy import core, visual
from condition import Condition
from objects import Object

class Experiment:
    def __init__(self):
        self.obj = Object()
        # Create a fixation bullseye
        self._bullseye_inner = visual.Circle(self.obj.win, radius=5, fillColor='green', lineColor=None)
        self._bullseye_outer = visual.Circle(self.obj.win, radius=8, fillColor='black', lineColor=None)

    def draw_bullseye(self):
        pass

    def _trial(self, grid, stim_list):
        # reference phase
        for s in stim_list:
            s.draw()
            self.obj.win.flip()
            core.wait(1)
        grid.draw()
        self.draw_bullseye()
        self.obj.win.flip()
        # Imagery Phase
        for _ in stim_list * 2:
            # TODO: Add sound play
            core.wait(1)

    def run_trial(self, condition: Condition):
        match condition:
            case Condition.SECTOR:
                grid = self.obj.sector_grid
                stim_list = self.obj.sector_stims.copy()
                self._trial(grid, stim_list)
            case _:
                pass

    def run_experiment(self, trials):
        while trials:
            current_trial = self.test_trial.pop()
            self.run_trial(current_trial)

    @staticmethod
    def wait_for_n_trs():
        raise NotImplementedError

    @staticmethod
    def wait_for_n_secs():
        raise NotImplementedError

