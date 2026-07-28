"""Mental-imagery retinotopy experiment."""

import json
import math
import random
import socket
import sys
import time
from pathlib import Path

from psychopy import core, event, gui, prefs, sound, visual


RUN_DURATION_SECONDS = 5 * 60
SCANNER_DUMMY_TRS = 5
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
        self.mock_scanner_started = False
        self.mock_scanner_last_attempt = float("-inf")

    def log(self, name, **data):
        self.events.append({"time": self.clock.getTime(), "event": name, **data})

    def log_on_flip(self, name, **data):
        self.window.callOnFlip(lambda: self.log(name, **data))

    def show_dialogs(self):
        dialog = gui.Dlg(title="Imagery Retinotopy", alwaysOnTop=True)
        dialog.addField("Subject ID:")
        dialog.addField("Run type", choices=["Practice", "fMRI"])
        dialog.addField("TR (seconds; fMRI only)", initial=DEFAULT_TR_SECONDS)
        dialog.addField(
            "Run number (fMRI only)",
            choices=[f"Run {number}" for number in range(1, MAX_REAL_RUNS + 1)],
        )
        data = dialog.show()
        if not dialog.OK:
            return False

        self.subject_id = data[0] or "unknown"
        self.experiment_type = data[1]
        if self.experiment_type == "fMRI":
            try:
                self.tr_seconds = float(data[2])
                if self.tr_seconds <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                self.tr_seconds = DEFAULT_TR_SECONDS
            self.run_number = int(data[3].removeprefix("Run "))

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
        self.sector_ids = sector_names

        # Ring trials use these masks for outward and inward sweeps.
        ring_names = [f"ring_d_{index:02d}" for index in range(6)]
        self.ring_stimuli = [
            visual.ImageStim(self.window, image=str(STIMULI_DIRECTORY / "rings_d" / f"{name}.png"))
            for name in ring_names
        ]
        self.ring_grid = visual.ImageStim(
            self.window, image=str(STIMULI_DIRECTORY / "ring_grid_d.png")
        )
        self.ring_ids = ring_names

    @staticmethod
    def is_scanner_trigger(key):
        return str(key) == "5"

    def poll_triggers(self):
        for key in event.getKeys():
            if not self.is_scanner_trigger(key):
                continue
            self.tr_count += 1
            self.log("tr", tr_index=self.tr_count, trigger_key=str(key), tr_seconds=self.tr_seconds)

    def start_mock_scanner(self):
        if self.mock_scanner_started:
            return True
        self.mock_scanner_last_attempt = self.clock.getTime()
        try:
            with socket.create_connection(("127.0.0.1", 2333), timeout=0.2) as connection:
                connection.sendall(b"Start")
        except OSError:
            return False
        self.mock_scanner_started = True
        self.log("mock_scanner_start_sent", host="127.0.0.1", port=2333)
        return True

    def wait_for_tr(self, target=None):
        target = target or self.tr_count + 1
        while self.tr_count < target:
            if (
                self.tr_count < SCANNER_DUMMY_TRS
                and not self.mock_scanner_started
                and self.clock.getTime() - self.mock_scanner_last_attempt >= 1
            ):
                self.start_mock_scanner()
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
            grid, stimuli, angles, stimulus_ids = (
                self.sector_grid,
                self.sector_stimuli,
                self.sector_angles,
                self.sector_ids,
            )
        else:
            grid, stimuli, angles, stimulus_ids = (
                self.ring_grid,
                [None, *self.ring_stimuli, None, *reversed(self.ring_stimuli), None],
                None,
                ["blank_grid", *self.ring_ids, "blank_grid", *reversed(self.ring_ids), "blank_grid"],
            )

        self.log("trial_start", condition=condition)
        opacity = 1.0
        opacity_step = 0.9 / len(stimuli)
        previous_state = None
        for index, stimulus in enumerate(stimuli):
            angle = angles[index] if angles else None
            state = {
                "condition": condition,
                "index": index,
                "stimulus_id": stimulus_ids[index],
                "angle": angle,
                "blank_grid": stimulus is None,
            }
            grid.draw()
            opacity -= opacity_step
            if stimulus is not None:
                stimulus.opacity = opacity
                stimulus.draw()
            self.draw_bullseye()
            tone = self.tone_for(index, angle, blank_grid=stimulus is None)
            if previous_state:
                self.log_on_flip("stimulus_offset", **previous_state)
            self.window.callOnFlip(tone.play)
            self.log_on_flip("stimulus_onset", **state)
            self.log_on_flip("reference_flip", **state)
            self.window.flip()
            previous_state = state
            if not self.wait(2):
                self.log("stimulus_offset", **previous_state, reason="run_end")
                return False

        grid.draw()
        self.draw_bullseye()
        self.log_on_flip("stimulus_offset", **previous_state)
        self.log_on_flip("imagery_onset", condition=condition)
        self.window.flip()
        self.log("imagery_start", condition=condition)
        for loop in (1, 2):
            for index in range(len(stimuli)):
                angle = angles[index] if angles else None
                self.tone_for(index, angle, blank_grid=stimuli[index] is None).play()
                self.log(
                    "imagery_tone",
                    condition=condition,
                    loop=loop,
                    index=index,
                    stimulus_id=stimulus_ids[index],
                    angle=angle,
                )
                if not self.wait(2):
                    self.log("imagery_offset", condition=condition, reason="run_end")
                    return False
        self.draw_bullseye()
        self.log_on_flip("imagery_offset", condition=condition)
        self.window.flip()
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
            task_trs = math.ceil(RUN_DURATION_SECONDS / self.tr_seconds)
            self.target_trs = SCANNER_DUMMY_TRS + task_trs
            self.log(
                "scanner_dummy_trigger_wait_start",
                dummy_trs=SCANNER_DUMMY_TRS,
                task_trs=task_trs,
                target_trs=self.target_trs,
                tr_seconds=self.tr_seconds,
            )
            self.start_mock_scanner()
            self.wait_for_tr(SCANNER_DUMMY_TRS)
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
    assert not Experiment.is_scanner_trigger("T")
    assert not Experiment.is_scanner_trigger("num5")
    assert not Experiment.is_scanner_trigger("space")


if __name__ == "__main__":
    self_check() if "--check" in sys.argv else main()
