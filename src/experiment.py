from psychopy import core, gui, event
from condition import Condition
from objects import Object
import json
import csv
import time
import os

class Experiment:
    def __init__(self):
        self.dlg = gui.Dlg(title="Imagery Retinotopy", alwaysOnTop=True)
        self.data = None
        self.run_time = None
        # Timing logging
        self.clock = core.Clock()
        self.log = []
        self.partial_csv_path = None

    def log_event(self, event_name, **kwargs):
        """Log an event with current time and optional data."""
        entry = {
            'time': self.clock.getTime(),
            'event': event_name,
        }
        if kwargs:
            entry.update(kwargs)
        self.log.append(entry)

    def save_log(self):
        """Save the log to a JSON file."""
        if not self.data:
            subject_id = 'unknown'
            exp_type = 'unknown'
        else:
            subject_id = self.data[0] or 'unknown'
            exp_type = self.data[1] or 'unknown'
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"log_{subject_id}_{exp_type}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(self.log, f, indent=2)
        return filename

    def save_partial_csv(self, filename: str = None):
        """Save the current in-memory event log to a CSV file (partial save).

        Behavior:
        - On the first call during a run (when filename is None) a consistent
          filename is created and stored in `self.partial_csv_path`. Subsequent
          calls with filename=None reuse that same file (so partial saves are
          persisted to the same path across the run).
        - If an explicit filename is provided it will be used; if relative it
          will be placed inside `partial_logs/`. The explicit filename will
          also be stored as `self.partial_csv_path` if not already set.
        - The CSV columns are inferred from the union of keys seen in the logged
          event dictionaries so far. The file is overwritten on each save to
          reflect the current in-memory log (partial snapshot).
        """
        # Create destination directory
        partial_dir = os.path.join(os.getcwd(), "partial_logs")
        os.makedirs(partial_dir, exist_ok=True)

        # Determine filename and ensure consistency across calls
        if filename is None:
            # If we already created a partial file path earlier in this run, reuse it
            if self.partial_csv_path is None:
                if not self.data:
                    subject_id = "unknown"
                    exp_type = "unknown"
                else:
                    subject_id = self.data[0] or "unknown"
                    exp_type = self.data[1] or "unknown"
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                self.partial_csv_path = os.path.join(partial_dir, f"partial_{subject_id}_{exp_type}_{timestamp}.csv")
            filename = self.partial_csv_path
        else:
            # if a relative path was provided, place inside partial_dir
            if not os.path.isabs(filename):
                filename = os.path.join(partial_dir, filename)
            # remember explicit filename for subsequent calls if not set
            if self.partial_csv_path is None:
                self.partial_csv_path = filename

        # If no events logged yet, still create a header with at least time,event
        if not self.log:
            fieldnames = ["time", "event"]
        else:
            # Build a sorted union of keys across all log entries to keep column order stable
            keys = set()
            for entry in self.log:
                keys.update(entry.keys())
            # prefer time,event ordering at the front
            ordered = []
            if "time" in keys:
                ordered.append("time"); keys.remove("time")
            if "event" in keys:
                ordered.append("event"); keys.remove("event")
            ordered.extend(sorted(keys))
            fieldnames = ordered

        # Write CSV (overwrite on each call to reflect current in-memory log)
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for entry in self.log:
                # ensure all keys present
                row = {k: entry.get(k, "") for k in fieldnames}
                writer.writerow(row)

        return filename

    def save_partial_trial(self, trial_number: int, condition: str = None, extra: dict = None):
        """Append a single row summarizing a trial to the partial CSV.

        The CSV will contain one row per trial (appended). If the partial CSV for
        this run does not yet exist it will be created and a header will be written.
        Basic columns: trial_number, timestamp, condition, events_in_run, extra_keys...
        `extra` can be used to supply additional summary fields for that trial.
        """
        # Ensure partial CSV path is set
        partial_dir = os.path.join(os.getcwd(), "partial_logs")
        os.makedirs(partial_dir, exist_ok=True)
        if self.partial_csv_path is None:
            # Create a consistent filename for this run
            if not self.data:
                subject_id = "unknown"
                exp_type = "unknown"
            else:
                subject_id = self.data[0] or "unknown"
                exp_type = self.data[1] or "unknown"
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.partial_csv_path = os.path.join(partial_dir, f"partial_{subject_id}_{exp_type}_{timestamp}.csv")

        # Build the row to write
        ts = self.clock.getTime()
        row = {
            "trial_number": trial_number,
            "timestamp": ts,
            "condition": condition or "",
            "events_in_run": len(self.log)
        }
        # Add any extra summary fields (convert lists/tuples to semicolon-separated strings)
        if extra:
            for k, v in extra.items():
                # avoid overwriting core fields
                if k not in row:
                    if isinstance(v, (list, tuple)):
                        # convert list/tuple into semicolon-separated string
                        try:
                            row[k] = ';'.join(str(x) for x in v)
                        except Exception:
                            row[k] = str(v)
                    else:
                        row[k] = v

        # Determine header order (core fields first, then extras)
        fieldnames = ["trial_number", "timestamp", "condition", "events_in_run"]
        # include extras discovered now
        extras = [k for k in row.keys() if k not in fieldnames]
        extras_sorted = sorted(extras)
        fieldnames.extend(extras_sorted)

        # If file does not exist, create and write header; otherwise append
        file_exists = os.path.exists(self.partial_csv_path)
        write_header = not file_exists
        # Use append mode for per-trial rows
        with open(self.partial_csv_path, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            # Ensure row has all fields and convert list/tuple values to semicolon-separated strings
            full_row = {}
            for k in fieldnames:
                val = row.get(k, "")
                if isinstance(val, (list, tuple)):
                    try:
                        full_row[k] = ';'.join(str(x) for x in val)
                    except Exception:
                        full_row[k] = str(val)
                else:
                    full_row[k] = val
            writer.writerow(full_row)

        return self.partial_csv_path

    def get_objects(self):
        self.obj = Object()

    def draw_bullseye(self):
        self.obj.bullseye_outer.draw()
        self.obj.bullseye_inner.draw()

    @staticmethod
    def _is_cardinal_angle(angle_degrees):
        """Return whether an angle is one of 0°, 90°, 180°, or 270°."""
        return angle_degrees is not None and round(angle_degrees) % 90 == 0

    def _sound_for_position(self, angle_degrees, idx):
        """Use the high cue at cardinal polar angles, otherwise the low cue."""
        if angle_degrees is None:
            # Preserve the prior behaviour for non-polar conditions (e.g. rings).
            return self.obj.sound2 if idx == 0 else self.obj.sound1, ('sound2' if idx == 0 else 'sound1')
        return self.obj.sound2 if self._is_cardinal_angle(angle_degrees) else self.obj.sound1, (
            'sound2' if self._is_cardinal_angle(angle_degrees) else 'sound1'
        )

    def _trial(self, grid, stim_list, condition_name, stim_angles=None):
        # reference phase
        self.log_event('reference_phase_start', condition=condition_name, stim_count=len(stim_list))
        # collect flip timestamps for this trial (experiment-relative)
        trial_flip_times = []

        opacity_step = ((100 - 10) / len(stim_list)) / 100
        current_opacity = 1.0
        for idx, s in enumerate(stim_list):
            angle_degrees = stim_angles[idx] if stim_angles is not None else None
            grid.draw()
            current_opacity = current_opacity - opacity_step
            s.opacity = current_opacity
            s.draw()
            self.draw_bullseye()
            cue_sound, sound_played = self._sound_for_position(angle_degrees, idx)
            # Start the cue on the same display refresh as the sector onset.
            self.obj.win.callOnFlip(cue_sound.play)

            # Capture flip timestamp (experiment-relative) immediately before/after flip
            flip_time = self.clock.getTime()
            self.obj.win.flip()
            # Use the clock time recorded right after flip for best precision relative to experiment clock
            flip_time = self.clock.getTime()
            trial_flip_times.append(flip_time)

            self.log_event('reference_flip', condition=condition_name, idx=idx,
                           angle_degrees=angle_degrees, opacity=current_opacity,
                           sound=sound_played, flip_time=flip_time)
            core.wait(2)

        # Imagery Phase
        self.log_event('imagery_phase_start', condition=condition_name)
        grid.draw()
        self.draw_bullseye()
        # Capture flip timestamp for imagery-phase flip
        flip_time = self.clock.getTime()
        self.obj.win.flip()
        flip_time = self.clock.getTime()
        trial_flip_times.append(flip_time)

        self.log_event('imagery_phase_flip', condition=condition_name, flip_time=flip_time)
        # first loop
        self.log_event('imagery_loop1_start', condition=condition_name)
        for idx, _ in enumerate(stim_list):
            angle_degrees = stim_angles[idx] if stim_angles is not None else None
            cue_sound, sound_played = self._sound_for_position(angle_degrees, idx)
            cue_sound.play()
            self.log_event('imagery_sound', condition=condition_name, loop=1, idx=idx,
                           angle_degrees=angle_degrees, sound=sound_played)
            core.wait(2)

        # second loop
        self.log_event('imagery_loop2_start', condition=condition_name)
        for idx, _ in enumerate(stim_list):
            angle_degrees = stim_angles[idx] if stim_angles is not None else None
            cue_sound, sound_played = self._sound_for_position(angle_degrees, idx)
            cue_sound.play()
            self.log_event('imagery_sound', condition=condition_name, loop=2, idx=idx,
                           angle_degrees=angle_degrees, sound=sound_played)
            core.wait(2)

        self.log_event('trial_end', condition=condition_name)

        # record last trial info for partial per-trial saving (experiment-relative timestamps)
        self.last_trial_info = {
            "flip_times": trial_flip_times,
            "trial_timestamp": self.clock.getTime()
        }

    def run_trial(self, condition: Condition):
        # clear the variable (just in case)
        grid = None
        stim_list = None
        stim_angles = None
        condition_name = condition.name
        self.log_event('trial_start', condition=condition_name)
        match condition:
            case Condition.SECTOR:
                grid = self.obj.sector_grid
                stim_list = self.obj.sector_stims.copy()
                stim_angles = self.obj.sector_center_degrees.copy()

            case Condition.RING:
                grid = self.obj.ring_grid
                stim_list = self.obj.ring_stims.copy()

            case Condition.BAR_HORIZONTAL:
                grid = self.obj.bar_horizontal_grid
                stim_list = self.obj.bar_horizontal_stims.copy()

            case Condition.BAR_VERTICAL:
                grid = self.obj.bar_vertical_grid
                stim_list = self.obj.bar_vertical_stims.copy()

            case _:
                pass

        self._trial(grid, stim_list, condition_name, stim_angles=stim_angles)

    def show_dlg(self):
        self.dlg.addField("Subject ID:")
        self.dlg.addField("Experiment Type", choices = ["fMRI", "Practice"])
        self.dlg.addField("TR:")
        self.data = self.dlg.show()
        self.log_event('dlg_shown', subject_id=self.data[0] if self.data else None,
                       experiment_type=self.data[1] if self.data and len(self.data)>1 else None,
                       tr=self.data[2] if self.data and len(self.data)>2 else None)
        return self.dlg.OK

    def run_rest(self, n):
        self.log_event('rest_start', duration=n)
        self.draw_bullseye
        flip_time = self.clock.getTime()
        self.obj.win.flip()
        self.log_event('rest_flip', flip_time=flip_time)
        core.wait(n)
        self.log_event('rest_end')

    def run_experiment(self, trials):
        self.log_event('experiment_start', total_trials=len(trials))
        self.run_rest(1)
        trial_count = 0
        while trials:
            trial_count += 1
            current_trial = trials.pop(0) # from the first to last
            self.log_event('next_trial', trial_number=trial_count, condition=current_trial.name)
            self.run_trial(current_trial)
            # Save one-row-per-trial summary immediately after each trial
            try:
                # include the condition name as a trial summary field
                partial_file = self.save_partial_trial(trial_count, condition=current_trial.name, extra=(self.last_trial_info if hasattr(self, 'last_trial_info') else None))
                print(f"Partial per-trial log appended to {partial_file}")
            except Exception:
                # tolerate any file I/O errors so the experiment can continue
                pass
            self.run_rest(1.0)
        self.log_event('experiment_end')
        self.run_time = self.clock.getTime()
        log_file = self.save_log()
        print(f"Log saved to {log_file}")

    @staticmethod
    def wait_for_n_trs(number): # this function is used to act like a clock to count the time by scanner inputs
        counter = 0
        while counter < number:
            keys = event.getKeys()
            if '5' in keys:
                counter += 1
                global TR_counter_global
                TR_counter_global += 1
