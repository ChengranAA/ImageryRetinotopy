"""Mental-imagery retinotopy experiment."""

import json
import math
import random
import sys
import time
from pathlib import Path

from psychopy import core, event, gui, prefs, sound, visual


RUN_DURATION_SECONDS = 5 * 60
MAX_REAL_RUNS = 10
DEFAULT_TR_SECONDS = 2.0
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STIMULI_DIRECTORY = PROJECT_ROOT / "stimuli"
LOG_DIRECTORY = PROJECT_ROOT / "logs"


class Experiment:
    def __init__(self):
        self.clock = core.Clock()
        self.events = []
        self.subject_id = "unknown"
        self.experiment_type = "Practice"
        self.run_number = None
        self.tr_seconds = DEFAULT_TR_SECONDS
        self.tr_count = 0
        self.target_trs = None

    def log(self, name, **data):
        self.events.append({"time": self.clock.getTime(), "event": name, **data})

    def show_dialogs(self):
        participant_dialog = gui.Dlg(title="Imagery Retinotopy", alwaysOnTop=True)
        participant_dialog.addField("Subject ID:")
        participant_dialog.addField("Experiment Type", choices=["fMRI", "Practice"])
        participant = participant_dialog.show()
        if not participant_dialog.OK:
            return False

        self.subject_id = participant[0] or "unknown"
        self.experiment_type = participant[1]
        if self.experiment_type == "fMRI":
            run_dialog = gui.Dlg(title="fMRI run setup", alwaysOnTop=True)
            run_dialog.addField("TR (seconds):")
            run_dialog.addField(
                "Run number",
                choices=[f"Run {number}" for number in range(1, MAX_REAL_RUNS + 1)],
            )
            run_data = run_dialog.show()
            if not run_dialog.OK:
                return False
            try:
                self.tr_seconds = float(run_data[0])
                if self.tr_seconds <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                self.tr_seconds = DEFAULT_TR_SECONDS
            self.run_number = int(run_data[1].removeprefix("Run "))

        confirmation = gui.Dlg(title="Confirm run", alwaysOnTop=True)
        if self.experiment_type == "fMRI":
            confirmation.addText(f"Real run: {self.run_number} of {MAX_REAL_RUNS}")
        else:
            confirmation.addText("Practice run — system-clock timing")
        confirmation.show()
        if not confirmation.OK:
            return False

        self.log(
            "dialog_complete",
            subject_id=self.subject_id,
            experiment_type=self.experiment_type,
            run_number=self.run_number,
            tr_seconds=self.tr_seconds if self.experiment_type == "fMRI" else None,
        )
        return True

    def create_stimuli(self):
        self.window = visual.Window(
            size=(1080, 720),
            fullscr=False,
            units="pix",
            backgroundImage=str(STIMULI_DIRECTORY / "noise_gaussian_1920x1080.png"),
        )
        self.bullseye_outer = visual.Circle(self.window, radius=8, fillColor="black", lineColor=None)
        self.bullseye_inner = visual.Circle(self.window, radius=5, fillColor="green", lineColor=None)
        self.low_tone = sound.Sound(value=440, secs=0.250, stereo=True)
        self.high_tone = sound.Sound(value=880, secs=0.250, stereo=True)

        sector_names = [f"sector_a_{(2 - offset) % 12:02d}" for offset in range(12)]
        self.sector_angles = [((2 - offset) * 30.0 + 30.0) % 360 for offset in range(12)]
        self.sector_stimuli = [
            visual.ImageStim(self.window, image=str(STIMULI_DIRECTORY / "sectors_a_pilot" / f"{name}.png"))
            for name in sector_names
        ]
        self.sector_grid = visual.ImageStim(
            self.window, image=str(STIMULI_DIRECTORY / "sector_grid_a_pilot.png")
        )

        # Ring trials use these masks for outward and inward sweeps.
        ring_names = [f"ring_d_{index:02d}" for index in range(6)]
        self.ring_stimuli = [
            visual.ImageStim(self.window, image=str(STIMULI_DIRECTORY / "rings_d" / f"{name}.png"))
            for name in ring_names
        ]
        self.ring_grid = visual.ImageStim(
            self.window, image=str(STIMULI_DIRECTORY / "ring_grid_d.png")
        )

    @staticmethod
    def is_scanner_trigger(key):
        return str(key).lower() in {"5", "t", "num5"}

    def poll_triggers(self):
        for key in event.getKeys():
            if not self.is_scanner_trigger(key):
                continue
            self.tr_count += 1
            self.log("tr", tr_index=self.tr_count, trigger_key=str(key), tr_seconds=self.tr_seconds)

    def wait_for_tr(self, target=None):
        target = target or self.tr_count + 1
        while self.tr_count < target:
            self.poll_triggers()
            if self.tr_count >= self.target_trs:
                return False
            core.wait(0.001)
        return True

    def wait(self, seconds):
        if self.target_trs is None:
            core.wait(seconds)
            return True
        return self.wait_for_tr(self.tr_count + max(1, math.ceil(seconds / self.tr_seconds)))

    def draw_bullseye(self):
        self.bullseye_outer.draw()
        self.bullseye_inner.draw()

    def rest(self, seconds):
        self.draw_bullseye()
        self.window.flip()
        self.log("rest_start", duration=seconds)
        self.wait(seconds)
        self.log("rest_end")

    def tone_for(self, index, angle=None, blank_grid=False):
        if blank_grid:
            return self.high_tone
        if angle is None:
            return self.low_tone
        return self.high_tone if round(angle) % 90 == 0 else self.low_tone

    def run_trial(self, condition):
        if condition == "SECTOR":
            grid, stimuli, angles = self.sector_grid, self.sector_stimuli, self.sector_angles
        else:
            grid, stimuli, angles = self.ring_grid, [
                None,
                *self.ring_stimuli,
                None,
                *reversed(self.ring_stimuli),
                None,
            ], None

        self.log("trial_start", condition=condition)
        opacity = 1.0
        opacity_step = 0.9 / len(stimuli)
        for index, stimulus in enumerate(stimuli):
            angle = angles[index] if angles else None
            grid.draw()
            opacity -= opacity_step
            if stimulus is not None:
                stimulus.opacity = opacity
                stimulus.draw()
            self.draw_bullseye()
            tone = self.tone_for(index, angle, blank_grid=stimulus is None)
            self.window.callOnFlip(tone.play)
            self.window.flip()
            self.log(
                "reference_flip",
                condition=condition,
                index=index,
                angle=angle,
                blank_grid=stimulus is None,
            )
            if not self.wait(2):
                return False

        grid.draw()
        self.draw_bullseye()
        self.window.flip()
        self.log("imagery_start", condition=condition)
        for loop in (1, 2):
            for index in range(len(stimuli)):
                angle = angles[index] if angles else None
                self.tone_for(index, angle, blank_grid=stimuli[index] is None).play()
                self.log("imagery_tone", condition=condition, loop=loop, index=index, angle=angle)
                if not self.wait(2):
                    return False
        self.log("trial_end", condition=condition)
        return True

    def save_log(self):
        LOG_DIRECTORY.mkdir(exist_ok=True)
        run_label = "practice" if self.run_number is None else f"run{self.run_number:02d}"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = LOG_DIRECTORY / f"log_{self.subject_id}_{self.experiment_type}_{run_label}_{timestamp}.json"
        path.write_text(json.dumps(self.events, indent=2))
        print(f"Log saved to {path}")

    def run(self):
        is_fmri = self.experiment_type == "fMRI"
        if is_fmri:
            self.target_trs = math.ceil(RUN_DURATION_SECONDS / self.tr_seconds)
            self.log("scanner_trigger_wait_start", target_trs=self.target_trs, tr_seconds=self.tr_seconds)
            self.wait_for_tr()
            self.log("scanner_run_start", tr_index=self.tr_count)

        trials = ["SECTOR"] * 5 + ["RING"] * 5
        random.shuffle(trials)
        self.log("experiment_start", timing_source="scanner_trigger" if is_fmri else "system_clock")
        self.rest(1)
        for condition in trials:
            if self.target_trs is not None and self.tr_count >= self.target_trs:
                break
            if not self.run_trial(condition):
                self.log("trial_interrupted", condition=condition)
                break
            self.rest(1)

        if is_fmri and self.tr_count < self.target_trs:
            self.log("fMRI_run_padding_start", remaining_trs=self.target_trs - self.tr_count)
            self.wait_for_tr(self.target_trs)
            self.log("scanner_run_end", tr_index=self.tr_count)
        self.log("experiment_end")
        self.save_log()
        self.window.close()


def main():
    prefs.hardware["audioDevice"] = ["PTB"]
    event.globalKeys.add(key="escape", func=core.quit, name="shutdown")
    experiment = Experiment()
    if experiment.show_dialogs():
        experiment.create_stimuli()
        experiment.run()


def self_check():
    assert Experiment.is_scanner_trigger("5")
    assert Experiment.is_scanner_trigger("T")
    assert not Experiment.is_scanner_trigger("space")


if __name__ == "__main__":
    self_check() if "--check" in sys.argv else main()
