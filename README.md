# Mental imagery retinotopy

This PsychoPy experiment presents rotating polar-angle sectors and horizontal
sweeps of a vertical bar. Each trial contains a visible reference sequence,
followed by two tone-paced imagery repetitions of the same sequence.

The experiment has two modes:

- **Practice:** runs from the computer clock in a window.
- **fMRI:** runs fullscreen and advances from scanner triggers.

The program entry point is `src/main.py`.

## Quick start

Install the environment once:

```sh
uv sync
```

Start the experiment:

```sh
uv run python src/main.py
```

Press **Escape** at any time to stop safely and save the available data.

## Mock-scanner test

For a complete run with TR = 2 seconds, open one terminal and start:

```sh
mock_scanner --tr 2 --volumes 274 --trigger 5 --gui
```

In a second terminal, from this project directory, start:

```sh
uv run python src/main.py
```

In the setup dialog select:

- the subject ID;
- `fMRI` as the run type;
- `2.0` as the TR;
- the run number you want to record;
- the presentation display;
- the correct stereo audio output.

The experiment contacts the mock scanner on TCP port `2333`. Mock triggers are
then received on UDP port `2334`, avoiding unreliable synthesized keyboard input
on macOS.

## Real-scanner run

Do not start `mock_scanner`. Start the experiment normally:

```sh
uv run python src/main.py
```

The program accepts the keyboard character `5` as the physical scanner trigger.
It discards the first five triggers as dummy volumes and starts the task at
trigger 6. Trigger 6 is time zero in the task-relative output columns.

If triggers stop, the current display remains visible until another trigger is
received or Escape is pressed.

## Setup dialog

| Field | Meaning |
|---|---|
| Subject ID | Saved in every output filename and table. |
| Run type | `Practice` or `fMRI`. |
| TR | Scanner repetition time in seconds; used only for fMRI. |
| Run number | Positive integer entered manually; used only for fMRI. |
| Display index | `0` is the primary display. |
| Audio output | Select the projector/HDMI output in the scanner room. |

An invalid fMRI TR falls back to `2.0` seconds. Canceling the dialog exits before
the presentation window opens.

## Participant instructions

Before the run, tell the participant to:

1. Keep looking at the central green fixation point.
2. Watch the visible sector or bar move through its sequence.
3. When the visible mask disappears, imagine the same movement twice.
4. Use each tone to advance the imagined mask to its next position.
5. Remain still; no button response is required.

The script does not contain an instruction screen or collect behavioral reports,
so the operator must give these instructions verbally.

## Run structure

Every run contains three `SECTOR` trials and three `BAR` trials. Their order is
randomized once and saved as `trial_schedule` in the JSON log.

The complete order is:

1. Five dummy scanner volumes in fMRI mode.
2. Trigger 6 starts the task.
3. Initial fixation rest.
4. Six randomized trials, each followed by fixation rest.
5. Data are checkpointed during each rest.
6. Final data and PyPRF files are written before the window closes.

There are 7 rest periods: one before trial 1 and one after every trial.

### Sector trial

The visible phase presents 12 clockwise 60-degree wedge positions, starting at
the top:

```text
90, 60, 30, 0, 330, 300, 270, 240, 210, 180, 150, 120 degrees
```

Each position lasts 2 seconds. The physical wedge gradually fades from opacity
`0.925` to `0.100`. The imagery phase removes the wedge but retains the sector
grid and repeats the same 12-position tone sequence twice.

- Visual phase: 24 seconds
- Imagery phase: 48 seconds
- Total sector trial: 72 seconds

### Bar trial

The visible phase presents a vertical bar moving left to right and then right to
left:

```text
blank, 00, 01, 02, 03, 04, 05, 06,
blank,
06, 05, 04, 03, 02, 01, 00, blank
```

Each position lasts 2 seconds. `vertical_bar_03` is the central bar. The imagery
phase removes the bar, retains the bar grid, and repeats the same 17-position
tone sequence twice.

- Visual phase: 34 seconds
- Imagery phase: 68 seconds
- Total bar trial: 102 seconds

## Tones

- Low tone: 440 Hz for ordinary positions.
- High tone: 880 Hz for sector cardinal positions, the central bar, and blank
  bar-transition positions.
- Tone duration: 250 ms, stereo.

During the visual phase, the tone is scheduled on the same PsychoPy flip as the
mask. During imagery, the tone command marks the position onset. These are
software timestamps, not measurements of physical acoustic onset.

## Timing at TR = 2 seconds

| Component | Total |
|---|---:|
| Three sector visual phases | 72 s |
| Three sector imagery phases | 144 s |
| Three bar visual phases | 102 s |
| Three bar imagery phases | 204 s |
| Seven rests | 14 s |
| **Task from trigger 6** | **536 s (8:56)** |

The five dummy intervals add 10 seconds. A complete fMRI run therefore uses 274
triggers and lasts approximately 9:06 from trigger 1 through the final rest.

For other TR values, the program uses:

```text
stimulus intervals = max(1, ceil(2 / TR))
rest intervals     = max(1, ceil(1 / TR))
```

A TR that does not divide 2 seconds can therefore lengthen individual samples.

## Display configuration

- PsychoPy monitor name: `7T_Projector_NOVA`
- Expected projector resolution: 1920 × 1200 pixels
- Projected width: 30 cm
- Viewing distance: 99 cm
- Stimulus images: 500 × 500 pixels
- fMRI mode: fullscreen on the selected display
- Practice mode: 1080 × 720 window
- Background: `stimuli/noise_gaussian_1920x1080.png`
- Fixation: green center inside a black outer circle
- Grid opacity: sinusoidal cycle from 0.30 to 0.70 every 24 seconds

These geometry values are configuration values, not proof of physical
calibration. Confirm them on the actual projector before data collection.

## Stimulus generators

Run generator scripts from the project root. Their filenames describe the
geometry they create:

| Geometry | Grid generator | Mask generator |
|---|---|---|
| Sectors | `00_generate_sector_grid.py` | `01_generate_sectors.py` |
| Pilot sectors | `00_generate_sector_grid_pilot.py` | — |
| Vertical bars | `00_generate_vertical_bar_grid.py` | `01_generate_vertical_bars.py` |
| Horizontal bars | `00_generate_horizontal_bar_grid.py` | `01_generate_horizontal_bars.py` |
| Rings | `00_generate_ring_grid.py` | `01_generate_rings.py` |

Generated directories, image filenames, archive names, and spatial identifiers
also use these geometry names without A/B/C/D suffixes.

## Output files

Generated results are written to `logs/`, which is intentionally ignored by
Git.

Practice mode writes:

- `log_<subject>_Practice_practice_<timestamp>.json`

fMRI mode writes:

- `log_<subject>_fMRI_runNN_<timestamp>.json` — complete event history;
- `fmri_triggers_<subject>_runNN_<timestamp>.csv` — trigger times and indices;
- `fmri_events_<subject>_runNN_<timestamp>.csv` — event-to-trigger mapping;
- `fmri_prf_design_<subject>_runNN_<timestamp>.csv` — visual, imagery, and rest
  design intervals;
- `fmri_volumes_<subject>_runNN_<timestamp>.csv` — design overlap per volume;
- `pyprf_<subject>_runNN_<timestamp>_frames/` — binary PyPRF masks and
  `manifest.csv`.

After removing the first five dummy volumes, a complete TR = 2 second run has
269 task volumes and 269 PyPRF frames. Visual aperture frames are white on black.
Imagery, rest, and blank-transition frames are black.

## Before collecting real data

Complete this checklist in the scanner room:

- Confirm the selected projector display and 1920 × 1200 presentation.
- Confirm physical stimulus size and viewing distance.
- Confirm that the scanner produces one `5` trigger per TR.
- Confirm the TR entered in the dialog matches the acquisition protocol.
- Confirm HDMI/projector audio and that 440/880 Hz cues are distinguishable.
- Run a short trigger test and inspect the JSON and trigger CSV.
- Confirm that the first five fMRI volumes will be removed before matching the
  data to the 269 PyPRF frames.

## Verification status

The mock-scanner path previously completed the former 452-trigger, ten-trial run
at TR = 2 seconds. It produced all timing tables and 447 PyPRF frames without an
experiment error. A later checkpoint-timing test found all non-rest samples between
1.991 and 2.013 seconds and confirmed that checkpoint writing is contained in
the recorded rest. The shortened 274-trigger, six-trial schedule still requires
a complete mock-scanner run.

The software is ready for mock-scanner and operator testing. Real data collection
still requires projector, audio, and physical scanner-trigger acceptance in the
scanner room.

Syntax check:

```sh
uv run python -m py_compile src/main.py
```

Scanner-key self-check on a machine with a graphical display:

```sh
uv run python src/main.py --check
```
