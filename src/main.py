"""
=======================================================
Title: Mental imagery retinotopy experiment
Author: Chengran Li
=======================================================

Experiment schedule:
- Wait for scanner dummy volumes (fMRI runs only)
- Show 3 rotating-sector trials and 3 bar-sweep trials in random order
- Show each aperture sequence once
- Repeat the same sequence twice using tones for imagery
"""

import csv
import json
import math
import random
import socket
import sys
import time
from pathlib import Path

import sounddevice
from PIL import Image, PngImagePlugin

from psychopy import core, event, gui, prefs, monitors

# Use the sounddevice backend because PTB cannot load its native audio
# dependencies on the presentation Mac.
prefs.hardware["audioLib"] = ["sounddevice"]
from psychopy import sound, visual


## Experiment settings
SCANNER_DUMMY_TRS = 5
DEFAULT_TR_SECONDS = 2.0
MONITOR_NAME = "7T_Projector_NOVA"
PROJECTOR_SIZE_PIX = (1920, 1200)
PROJECTOR_WIDTH_CM = 30.0
PROJECTOR_DISTANCE_CM = 99.0
GRID_OPACITY_MIN = 0.30
GRID_OPACITY_MAX = 0.70
GRID_OPACITY_PERIOD_SECONDS = 24.0
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STIMULI_DIRECTORY = PROJECT_ROOT / "stimuli"
LOG_DIRECTORY = PROJECT_ROOT / "logs"

## Experiment data and run information
clock = core.Clock()
events = []
trigger_times = []
design_events = []
subject_id = "unknown"
experiment_type = "Practice"
run_number = None
display_screen = 0
tr_seconds = DEFAULT_TR_SECONDS
tr_count = 0
mock_scanner_started = False
mock_scanner_last_attempt = float("-inf")
mock_scanner_trigger_socket = None
trial_number = 0
session_timestamp = time.strftime("%Y%m%d_%H%M%S")
active_grid = None
active_stimulus = None
active_stimulus_opacity = 0.0
pyprf_frame_count = 0


## Event logging
def log(name, **data):
    record = {"time": clock.getTime(), "event": name, **data}
    events.append(record)
    return record


def log_design_event(name, phase, state):
    record = log(name, phase=phase, trial_number=trial_number, **state)
    close_design_event(record["time"])
    design_events.append({
        "condition": "", "index": "", "stimulus_id": "", "angle": "",
        "blank_grid": True, "opacity": 0, **record,
    })
    return record


def close_design_event(timestamp=None):
    if design_events and "offset" not in design_events[-1]:
        design_events[-1]["offset"] = clock.getTime() if timestamp is None else timestamp


def grid_opacity():
    phase = 2 * math.pi * clock.getTime() / GRID_OPACITY_PERIOD_SECONDS
    return GRID_OPACITY_MIN + (GRID_OPACITY_MAX - GRID_OPACITY_MIN) * (0.5 + 0.5 * math.sin(phase))


def draw_scene():
    if active_grid is None:
        return
    active_grid.opacity = grid_opacity()
    active_grid.draw()
    if active_stimulus is not None:
        active_stimulus.opacity = active_stimulus_opacity
        active_stimulus.draw()
    draw_bullseye()
    window.flip()


def aperture_path(condition, stimulus_id, blank_grid):
    if blank_grid:
        return ""
    directory = "sectors_pilot" if condition == "SECTOR" else "vertical_bars"
    return str(Path("stimuli") / directory / f"{stimulus_id}.png")


def sample_for_volume(volume_onset, volume_offset):
    """Return the design sample occupying most of one scanner volume."""
    best_sample = None
    best_overlap = 0.0
    for sample in design_events:
        sample_offset = sample.get("offset", volume_offset)
        overlap_start = max(volume_onset, sample["time"])
        overlap_end = min(volume_offset, sample_offset)
        overlap = max(0.0, overlap_end - overlap_start)
        if overlap > best_overlap:
            best_sample = sample
            best_overlap = overlap
    return best_sample, best_overlap


def pyprf_frame(sample, mask_cache, frame_size):
    """Create the binary spatial-stimulation frame expected by PyPRF."""
    if sample is None or sample["phase"] != "visual" or sample["blank_grid"]:
        return Image.new("L", frame_size, 0)

    mask_path = PROJECT_ROOT / aperture_path(
        sample["condition"], sample["stimulus_id"], sample["blank_grid"]
    )
    if mask_path not in mask_cache:
        with Image.open(mask_path) as image:
            alpha = image.convert("RGBA").getchannel("A")
            mask_cache[mask_path] = alpha.point(lambda value: 255 if value else 0)
    return mask_cache[mask_path].copy()


def save_pyprf_frames(run_label, timestamp):
    """Save one PyPRF-compatible stimulus-location PNG per retained volume."""
    global pyprf_frame_count

    task_triggers = trigger_times[SCANNER_DUMMY_TRS:]
    run_end = next(
        (record["time"] for record in reversed(events)
         if record["event"] in {"display_cleared", "experiment_end"}),
        None,
    )
    volume_intervals = []
    for index, onset in enumerate(task_triggers):
        following = task_triggers[index + 1] if index + 1 < len(task_triggers) else None
        offset = following if following is not None else run_end
        if offset is None or offset <= onset:
            break
        sample, overlap = sample_for_volume(onset, offset)
        volume_intervals.append((onset, offset, sample, overlap))

    if not volume_intervals:
        return

    frame_directory = LOG_DIRECTORY / f"pyprf_{subject_id}_{run_label}_{timestamp}_frames"
    frame_directory.mkdir(exist_ok=True)
    Image.init()
    frame_size = (500, 500)
    mask_cache = {}

    for index in range(pyprf_frame_count, len(volume_intervals)):
        sample = volume_intervals[index][2]
        frame = pyprf_frame(sample, mask_cache, frame_size)
        frame.save(frame_directory / f"frame_{index + 1:03d}.png", format="PNG")
    pyprf_frame_count = len(volume_intervals)

    manifest_path = frame_directory / "manifest.csv"
    with manifest_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "frame", "tr_index", "trigger_time_seconds", "seconds_from_task_start",
            "volume_duration_seconds", "phase", "condition", "stimulus_id",
            "blank_grid", "aperture_path", "trial_number", "opacity",
            "dominant_overlap_seconds",
        ])
        writer.writeheader()
        task_start = task_triggers[0]
        for index, (onset, offset, sample, overlap) in enumerate(volume_intervals, start=1):
            writer.writerow({
                "frame": f"frame_{index:03d}.png",
                "tr_index": SCANNER_DUMMY_TRS + index,
                "trigger_time_seconds": f"{onset:.6f}",
                "seconds_from_task_start": f"{onset - task_start:.6f}",
                "volume_duration_seconds": f"{offset - onset:.6f}",
                "phase": "" if sample is None else sample["phase"],
                "condition": "" if sample is None else sample["condition"],
                "stimulus_id": "" if sample is None else sample["stimulus_id"],
                "blank_grid": True if sample is None else sample["blank_grid"],
                "aperture_path": "" if sample is None else aperture_path(
                    sample["condition"], sample["stimulus_id"], sample["blank_grid"]
                ),
                "trial_number": "" if sample is None else sample["trial_number"],
                "opacity": "" if sample is None else sample["opacity"],
                "dominant_overlap_seconds": f"{overlap:.6f}",
            })


## Experiment information window
def show_dialogs():
    global subject_id, experiment_type, run_number, tr_seconds, display_screen

    outputs = list(dict.fromkeys(device["name"] for device in sounddevice.query_devices()
                                 if device["max_output_channels"] >= 2))
    if not outputs:
        raise RuntimeError("No stereo audio output is available. Connect the presentation audio device.")
    preferred = next((name for name in outputs if "hdmi" in name.lower()), None)
    if preferred is None:
        preferred = next((name for name in outputs if "macbook" in name.lower()), outputs[0])
    outputs.remove(preferred)
    outputs.insert(0, preferred)
    dialog = gui.Dlg(title="Imagery Retinotopy", alwaysOnTop=True)
    dialog.addField("Subject ID:")
    dialog.addField("Run type", choices=["Practice", "fMRI"])
    dialog.addField("TR (seconds; fMRI only)", initial=DEFAULT_TR_SECONDS)
    dialog.addField("Run number (fMRI only)", initial=1)
    dialog.addField("Presentation display index (0=primary)", initial=0)
    dialog.addField("Audio output (select HDMI/projector when connected)", choices=outputs)
    data = dialog.show()
    if not dialog.OK:
        return False

    prefs.hardware["audioDevice"] = [data[5]]
    display_screen = int(data[4])
    if display_screen < 0:
        raise ValueError("Presentation display index must be nonnegative")
    subject_id = data[0] or "unknown"
    experiment_type = data[1]
    if experiment_type == "fMRI":
        try:
            tr_seconds = float(data[2])
            if not math.isfinite(tr_seconds) or tr_seconds <= 0:
                raise ValueError
        except (TypeError, ValueError):
            tr_seconds = DEFAULT_TR_SECONDS
        run_number = int(data[3])
        if run_number < 1:
            raise ValueError("Run number must be a positive integer")

    log(
        "dialog_complete",
        subject_id=subject_id,
        experiment_type=experiment_type,
        run_number=run_number,
        display_screen=display_screen,
        audio_device=data[5],
        tr_seconds=tr_seconds if experiment_type == "fMRI" else None,
    )
    return True


## Window, sound and stimulus setup
def create_stimuli():
    global window, bullseye_outer, bullseye_inner, low_tone, high_tone
    global sector_angles, sector_stimuli, sector_grid, sector_ids
    global bar_stimuli, bar_grid, bar_ids

    mon7t = monitors.Monitor(MONITOR_NAME)
    mon7t.setSizePix(PROJECTOR_SIZE_PIX)
    mon7t.setWidth(PROJECTOR_WIDTH_CM)
    mon7t.setDistance(PROJECTOR_DISTANCE_CM)
    window = visual.Window(
        size=PROJECTOR_SIZE_PIX if experiment_type == "fMRI" else (1080, 720),
        fullscr=experiment_type == "fMRI",
        screen=display_screen,
        units="pix",
        monitor=mon7t,
        backgroundImage=str(STIMULI_DIRECTORY / "noise_gaussian_1920x1080.png"),
    )
    log("display_metadata", monitor=MONITOR_NAME, display_screen=display_screen,
        geometry_source="user_supplied_projector_specifications",
        window_size_pix=list(map(int, window.size)), fullscreen=window.fullscr,
        screen_width_cm=window.monitor.getWidth(),
        viewing_distance_cm=window.monitor.getDistance(),
        monitor_size_pix=window.monitor.getSizePix(),
        calibration_verified=False, stimulus_size_pix=[500, 500],
        grid_opacity_min=GRID_OPACITY_MIN, grid_opacity_max=GRID_OPACITY_MAX,
        grid_opacity_period_seconds=GRID_OPACITY_PERIOD_SECONDS,
        aperture_channel="alpha", imagery_timing_reference="tone_command")
    bullseye_outer = visual.Circle(window, radius=8, fillColor="black", lineColor=None)
    bullseye_inner = visual.Circle(window, radius=5, fillColor="green", lineColor=None)
    low_tone = sound.Sound(value=440, secs=0.250, stereo=True)
    high_tone = sound.Sound(value=880, secs=0.250, stereo=True)

    sector_ids = [f"sector_{(2 - offset) % 12:02d}" for offset in range(12)]
    sector_angles = [((2 - offset) * 30.0 + 30.0) % 360 for offset in range(12)]
    sector_stimuli = [
        visual.ImageStim(window, image=str(STIMULI_DIRECTORY / "sectors_pilot" / f"{name}.png"))
        for name in sector_ids
    ]
    sector_grid = visual.ImageStim(window, image=str(STIMULI_DIRECTORY / "sector_grid_pilot.png"))

    bar_ids = [f"vertical_bar_{index:02d}" for index in range(7)]
    bar_stimuli = [
        visual.ImageStim(window, image=str(STIMULI_DIRECTORY / "vertical_bars" / f"{name}.png"))
        for name in bar_ids
    ]
    bar_grid = visual.ImageStim(window, image=str(STIMULI_DIRECTORY / "vertical_bar_grid.png"))


## Scanner timing
def is_scanner_trigger(key):
    return str(key) == "5"


def record_trigger(timestamp, source):
    global tr_count
    tr_count += 1
    trigger = log(
        "tr", time=timestamp, tr_index=tr_count, trigger_key="5",
        trigger_source=source, tr_seconds=tr_seconds,
    )
    trigger_times.append(trigger["time"])


def poll_triggers():
    for key, timestamp in event.getKeys(timeStamped=clock):
        if key == "escape":
            raise KeyboardInterrupt
        if experiment_type == "fMRI" and is_scanner_trigger(key) and not mock_scanner_started:
            record_trigger(timestamp, "keyboard")

    if experiment_type != "fMRI" or mock_scanner_trigger_socket is None:
        return
    while True:
        try:
            trigger = mock_scanner_trigger_socket.recv(16)
        except BlockingIOError:
            break
        if trigger.strip() == b"5":
            record_trigger(clock.getTime(), "mock_scanner_udp")


def open_mock_scanner_trigger_socket():
    global mock_scanner_trigger_socket
    if mock_scanner_trigger_socket is not None:
        return
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.bind(("127.0.0.1", 2334))
    receiver.setblocking(False)
    mock_scanner_trigger_socket = receiver
    log("mock_scanner_trigger_receiver_open", host="127.0.0.1", port=2334)


def start_mock_scanner():
    global mock_scanner_started, mock_scanner_last_attempt
    if mock_scanner_started:
        return True
    mock_scanner_last_attempt = clock.getTime()
    try:
        open_mock_scanner_trigger_socket()
        with socket.create_connection(("127.0.0.1", 2333), timeout=0.2) as connection:
            connection.sendall(b"Start")
    except OSError:
        return False
    mock_scanner_started = True
    log("mock_scanner_start_sent", host="127.0.0.1", port=2333)
    return True


def wait_for_tr(target=None):
    target = target or tr_count + 1
    while tr_count < target:
        if (
            tr_count < SCANNER_DUMMY_TRS
            and not mock_scanner_started
            and clock.getTime() - mock_scanner_last_attempt >= 1
        ):
            start_mock_scanner()
        draw_scene()
        poll_triggers()
        core.wait(0.001)
    return True


def wait(seconds):
    if experiment_type != "fMRI":
        end = clock.getTime() + seconds
        while clock.getTime() < end:
            draw_scene()
            poll_triggers()
            core.wait(0.001)
        return True
    # Account for pulses queued during drawing, sound calls, or saving before
    # choosing a future trigger boundary for this newly displayed sample.
    poll_triggers()
    return wait_for_tr(tr_count + max(1, math.ceil(seconds / tr_seconds)))


def draw_bullseye():
    bullseye_outer.draw()
    bullseye_inner.draw()


def rest(seconds, checkpoint=False):
    global active_grid, active_stimulus
    active_grid = None
    active_stimulus = None
    draw_bullseye()
    window.callOnFlip(lambda: log_design_event("rest_start", "rest", {}))
    window.flip()
    if checkpoint:
        save_log()
    wait(seconds)
    log("rest_end")


def tone_for(angle=None, blank_grid=False, middle_bar=False):
    if blank_grid or middle_bar or (angle is not None and round(angle) % 90 == 0):
        return high_tone
    return low_tone


## Visual presentation and imagery
def run_trial(condition):
    global active_grid, active_stimulus, active_stimulus_opacity

    if condition == "SECTOR":
        grid, stimuli, angles, stimulus_ids = sector_grid, sector_stimuli, sector_angles, sector_ids
    else:
        grid = bar_grid
        stimuli = [None, *bar_stimuli, None, *reversed(bar_stimuli), None]
        angles = None
        stimulus_ids = ["blank_grid", *bar_ids, "blank_grid", *reversed(bar_ids), "blank_grid"]

    log("trial_start", condition=condition, trial_number=trial_number)
    opacity = 1.0
    opacity_step = 0.9 / len(stimuli)
    previous_state = None

    for index, stimulus in enumerate(stimuli):
        angle = angles[index] if angles else None
        middle_bar = condition == "BAR" and stimulus_ids[index] == "vertical_bar_03"
        state = {
            "condition": condition,
            "index": index,
            "stimulus_id": stimulus_ids[index],
            "angle": angle,
            "blank_grid": stimulus is None,
        }
        opacity -= opacity_step
        state["opacity"] = opacity if stimulus is not None else 0
        active_grid = grid
        active_stimulus = stimulus
        active_stimulus_opacity = state["opacity"]
        if previous_state:
            window.callOnFlip(lambda state=previous_state: log("stimulus_offset", **state))
        window.callOnFlip(tone_for(angle, stimulus is None, middle_bar).play)
        window.callOnFlip(lambda state=state: log_design_event("stimulus_onset", "visual", state))
        window.callOnFlip(lambda state=state: log("reference_flip", **state))
        draw_scene()
        previous_state = state
        wait(2)

    active_grid = grid
    active_stimulus = None
    window.callOnFlip(lambda state=previous_state: log("stimulus_offset", **state))
    window.callOnFlip(close_design_event)
    window.callOnFlip(lambda: log("imagery_onset", condition=condition))
    draw_scene()
    log("imagery_start", condition=condition)

    for loop in (1, 2):
        for index, stimulus in enumerate(stimuli):
            angle = angles[index] if angles else None
            middle_bar = condition == "BAR" and stimulus_ids[index] == "vertical_bar_03"
            tone_for(angle, stimulus is None, middle_bar).play()
            state = {
                "condition": condition,
                "index": index,
                "stimulus_id": stimulus_ids[index],
                "angle": angle,
                "blank_grid": stimulus is None,
                "opacity": 0,
            }
            log_design_event(
                "imagery_tone",
                "imagery",
                {"loop": loop, **state},
            )
            wait(2)

    active_grid = None
    active_stimulus = None
    draw_bullseye()
    window.callOnFlip(lambda: log("imagery_offset", condition=condition))
    window.callOnFlip(close_design_event)
    window.flip()
    log("trial_end", condition=condition)
    return True


## Save experiment data
def save_fmri_timing_csv(run_label, timestamp):
    if not trigger_times:
        return

    first_trigger_time = trigger_times[0]
    task_start_time = trigger_times[SCANNER_DUMMY_TRS] if len(trigger_times) > SCANNER_DUMMY_TRS else None
    trigger_path = LOG_DIRECTORY / f"fmri_triggers_{subject_id}_{run_label}_{timestamp}.csv"
    with trigger_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "subject_id", "run_number", "tr_seconds", "tr_index",
                "trigger_time_seconds", "seconds_from_first_trigger",
                "seconds_from_task_start", "phase",
            ],
        )
        writer.writeheader()
        for index, trigger_time in enumerate(trigger_times, start=1):
            writer.writerow({
                "subject_id": subject_id,
                "run_number": run_number,
                "tr_seconds": tr_seconds,
                "tr_index": index,
                "trigger_time_seconds": f"{trigger_time:.6f}",
                "seconds_from_first_trigger": f"{trigger_time - first_trigger_time:.6f}",
                "seconds_from_task_start": "" if task_start_time is None else f"{trigger_time - task_start_time:.6f}",
                "phase": "dummy" if index <= SCANNER_DUMMY_TRS else "task",
            })

    event_path = LOG_DIRECTORY / f"fmri_events_{subject_id}_{run_label}_{timestamp}.csv"
    with event_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "event", "event_time_seconds", "seconds_from_first_trigger",
                "seconds_from_task_start", "tr_index", "details_json",
            ],
        )
        writer.writeheader()
        for record in events:
            event_time = record["time"]
            if event_time < first_trigger_time:
                continue
            current_tr = sum(trigger_time <= event_time for trigger_time in trigger_times)
            details = {key: value for key, value in record.items() if key not in {"time", "event"}}
            writer.writerow({
                "event": record["event"],
                "event_time_seconds": f"{event_time:.6f}",
                "seconds_from_first_trigger": f"{event_time - first_trigger_time:.6f}",
                "seconds_from_task_start": "" if task_start_time is None else f"{event_time - task_start_time:.6f}",
                "tr_index": current_tr,
                "details_json": json.dumps(details),
            })
    print(f"fMRI timing CSVs saved to {trigger_path} and {event_path}")

    design_path = LOG_DIRECTORY / f"fmri_prf_design_{subject_id}_{run_label}_{timestamp}.csv"
    with design_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "phase", "condition", "loop", "index", "stimulus_id", "angle", "blank_grid",
                "aperture_path", "onset_seconds_from_first_trigger", "onset_seconds_from_task_start",
                "tr_index", "duration_seconds", "trial_number", "opacity", "offset_seconds_from_first_trigger",
            ],
        )
        writer.writeheader()
        for sample in design_events:
            sample_time = sample["time"]
            if sample_time < first_trigger_time:
                continue
            offset = sample.get("offset")
            writer.writerow({
                "phase": sample["phase"],
                "condition": sample["condition"],
                "loop": sample.get("loop", ""),
                "index": sample["index"],
                "stimulus_id": sample["stimulus_id"],
                "angle": sample["angle"],
                "blank_grid": sample["blank_grid"],
                "aperture_path": aperture_path(sample["condition"], sample["stimulus_id"], sample["blank_grid"]),
                "onset_seconds_from_first_trigger": f"{sample_time - first_trigger_time:.6f}",
                "onset_seconds_from_task_start": "" if task_start_time is None else f"{sample_time - task_start_time:.6f}",
                "tr_index": sum(trigger_time <= sample_time for trigger_time in trigger_times),
                "duration_seconds": "" if offset is None else f"{offset - sample_time:.6f}",
                "offset_seconds_from_first_trigger": "" if offset is None else f"{offset - first_trigger_time:.6f}",
                "trial_number": sample["trial_number"],
                "opacity": sample["opacity"],
            })
    print(f"fMRI pRF design saved to {design_path}")
    volume_path = LOG_DIRECTORY / f"fmri_volumes_{subject_id}_{run_label}_{timestamp}.csv"
    with volume_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "tr_index", "phase", "onset_seconds_from_first_trigger",
            "duration_seconds", "boundary_source", "samples_json",
        ])
        writer.writeheader()
        for index, onset in enumerate(trigger_times):
            following = trigger_times[index + 1] if index + 1 < len(trigger_times) else None
            run_end = next((e["time"] for e in reversed(events)
                            if e["event"] in {"display_cleared", "experiment_end"}), None)
            offset = following if following is not None else run_end
            overlaps = []
            if offset is not None:
                for sample_index, sample in enumerate(design_events):
                    end = sample.get("offset", offset)
                    start = max(onset, sample["time"])
                    end = min(offset, end)
                    if end > start:
                        overlaps.append({"design_row": sample_index + 1,
                                         "phase": sample["phase"],
                                         "stimulus_id": sample["stimulus_id"],
                                         "onset_within_volume": start - onset,
                                         "duration_seconds": end - start})
            writer.writerow({"tr_index": index + 1,
                             "phase": "dummy" if index < SCANNER_DUMMY_TRS else "task",
                             "onset_seconds_from_first_trigger": onset - first_trigger_time,
                             "duration_seconds": "" if offset is None else offset - onset,
                             "boundary_source": "next_trigger" if following is not None else "run_end" if offset is not None else "pending",
                             "samples_json": json.dumps(overlaps)})

    save_pyprf_frames(run_label, timestamp)


def save_log():
    LOG_DIRECTORY.mkdir(exist_ok=True)
    run_label = "practice" if run_number is None else f"run{run_number:02d}"
    timestamp = session_timestamp
    path = LOG_DIRECTORY / f"log_{subject_id}_{experiment_type}_{run_label}_{timestamp}.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(events, indent=2))
    temporary.replace(path)
    print(f"Log saved to {path}")
    if experiment_type == "fMRI":
        save_fmri_timing_csv(run_label, timestamp)


## Main experiment loop
def run_experiment():
    global trial_number
    is_fmri = experiment_type == "fMRI"
    if is_fmri:
        event.clearEvents(eventType="keyboard")
        log(
            "scanner_dummy_trigger_wait_start",
            dummy_trs=SCANNER_DUMMY_TRS,
            tr_seconds=tr_seconds,
        )
        start_mock_scanner()
        wait_for_tr(SCANNER_DUMMY_TRS + 1)
        log("scanner_run_start", tr_index=tr_count)

    trials = ["SECTOR"] * 3 + ["BAR"] * 3
    random.shuffle(trials)
    log("trial_schedule", conditions=trials)
    log("experiment_start", timing_source="scanner_trigger" if is_fmri else "system_clock")
    rest(1)
    for trial_number, condition in enumerate(trials, start=1):
        run_trial(condition)
        rest(1, checkpoint=True)

    close_design_event()
    if is_fmri:
        log("scanner_run_end", tr_index=tr_count)
    log("experiment_end")


def self_check():
    assert is_scanner_trigger("5")
    assert not is_scanner_trigger("T")
    assert not is_scanner_trigger("num5")
    assert not is_scanner_trigger("space")


def main():
    if show_dialogs():
        try:
            create_stimuli()
            run_experiment()
        except KeyboardInterrupt:
            log("experiment_aborted", reason="escape_or_interrupt")
        except Exception as error:
            log("experiment_error", error=repr(error))
            raise
        finally:
            if mock_scanner_trigger_socket is not None:
                mock_scanner_trigger_socket.close()
            has_window = "window" in globals()
            if has_window:
                window.clearBuffer()
                window.callOnFlip(close_design_event)
                window.flip()
                log("display_cleared")
            try:
                save_log()
            finally:
                if has_window:
                    window.close()


if __name__ == "__main__":
    self_check() if "--check" in sys.argv else main()
