# Mental imagery retinotopy

This PsychoPy experiment uses tone-paced imagery of rotating polar-angle
sectors, horizontal sweeps of a vertical bar, and vertical sweeps of a
horizontal bar. Each trial starts directly with three imagery repetitions. The
sector and bar grids remain visible, but no sector or bar mask is shown.

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

For a complete run with TR = 1 second, open one terminal and start:

```sh
mock_scanner --tr 1 --volumes 308 --trigger 5 --gui
```

In a second terminal, from this project directory, start:

```sh
uv run python src/main.py
```

In the setup dialog select:

- the subject ID;
- `fMRI` as the run type;
- `1.0` as the TR;
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

An invalid fMRI TR falls back to `1.0` second. Canceling the dialog exits before
the presentation window opens.

## Participant instructions

Before the run, tell the participant to:

1. Keep looking at the central green fixation point.
2. Use the visible grid to identify the sector, vertical-bar, or horizontal-bar
   trial.
3. Start imagining immediately when the tone sequence begins; no visible sector
   or bar will be presented first.
4. Use each tone to advance the imagined mask to its next position through three
   complete repetitions.
5. Remain still; no button response is required.

The script does not contain an instruction screen or collect behavioral reports,
so the operator must give these instructions verbally.

## Run structure

Every run contains one `SECTOR`, one `VERTICAL_BAR`, and one `HORIZONTAL_BAR`
trial. Their order is randomized once and saved as `trial_schedule` in the JSON
log.

The complete order is:

1. Five dummy scanner volumes in fMRI mode.
2. Trigger 6 starts the task.
3. Initial fixation rest.
4. Three randomized trials; the first two are followed by 10 TRs of fixation and
   the final trial is followed by 5 TRs of fixation.
5. Data are checkpointed during each rest.
6. Final data and PyPRF files are written before the window closes.

There are 4 rest periods: 1 TR before trial 1, 10 TRs after each of the first two
trials, and 5 TRs after the final trial.

### Sector imagery trial

Imagine 12 clockwise 60-degree wedge positions, starting at the top:

```text
90, 60, 30, 0, 330, 300, 270, 240, 210, 180, 150, 120 degrees
```

Each imagined position lasts 2 seconds. The sector grid remains visible, no
wedge is displayed, and the 12-position tone sequence repeats three times.

- Imagery phase: 72 seconds
- Total sector trial: 72 seconds

### Vertical-bar imagery trial

Imagine a vertical bar moving left to right and then right to left:

```text
blank, 00, 01, 02, 03, 04, 05, 06,
blank,
06, 05, 04, 03, 02, 01, 00, blank
```

Each imagined position lasts 2 seconds. `vertical_bar_03` is the central bar.
The vertical-bar grid remains visible, no bar is displayed, and the same
17-position tone sequence repeats three times.

- Imagery phase: 102 seconds
- Total vertical-bar trial: 102 seconds

### Horizontal-bar imagery trial

Imagine a horizontal bar moving from bottom to top and then top to bottom. It
uses the same sequence structure as the vertical-bar trial:

```text
blank, 00, 01, 02, 03, 04, 05, 06,
blank,
06, 05, 04, 03, 02, 01, 00, blank
```

Each imagined position lasts 2 seconds. `horizontal_bar_03` is the central bar.
The horizontal-bar grid remains visible, no bar is displayed, and the same
17-position tone sequence repeats three times.

- Imagery phase: 102 seconds
- Total horizontal-bar trial: 102 seconds

## Tones

- Low tone: 440 Hz for ordinary positions.
- High tone: 880 Hz for sector cardinal positions, the central bar, and blank
  bar-transition positions.
- Tone duration: 250 ms, stereo.

The imagery tone command marks each imagined-position onset. These are software
timestamps, not measurements of physical acoustic onset.

## Timing at TR = 1 second

| Component | Total |
|---|---:|
| One sector imagery phase | 72 s |
| Two bar imagery phases | 204 s |
| Initial rest | 1 s |
| Two inter-trial rests | 20 s |
| Final rest | 5 s |
| **Task from trigger 6** | **302 s (5:02)** |

The five dummy intervals add 5 seconds. A complete fMRI run therefore uses 308
triggers and lasts approximately 5:07 from trigger 1 through the final rest.
Each 2-second imagery position spans two scanner volumes.

For other TR values, the program uses:

```text
imagery position   = max(1, ceil(2 / TR))
initial rest       = max(1, ceil(1 / TR))
inter-trial rest   = 10 TRs
final rest         = 5 TRs
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
- `fmri_prf_design_<subject>_runNN_<timestamp>.csv` — imagery and rest
  design intervals;
- `fmri_volumes_<subject>_runNN_<timestamp>.csv` — design overlap per volume;
- `pyprf_<subject>_runNN_<timestamp>_frames/` — binary PyPRF masks and
  `manifest.csv`.

After removing the first five dummy volumes, a complete TR = 1 second run has
303 task volumes and 303 PyPRF frames. Imagery, rest, and blank-transition
frames remain black; imagined spatial identities are recorded in the event and
design tables.

## Before collecting real data

Complete this checklist in the scanner room:

- Confirm the selected projector display and 1920 × 1200 presentation.
- Confirm physical stimulus size and viewing distance.
- Confirm that the scanner produces one `5` trigger per TR.
- Confirm the TR entered in the dialog matches the acquisition protocol.
- Confirm HDMI/projector audio and that 440/880 Hz cues are distinguishable.
- Run a short trigger test and inspect the JSON and trigger CSV.
- Confirm that the first five fMRI volumes will be removed before matching the
  data to the 303 PyPRF frames.

## Verification status

The mock-scanner path previously completed the former 452-trigger, ten-trial run
at TR = 2 seconds. It produced all timing tables and 447 PyPRF frames without an
experiment error. A later checkpoint-timing test found all non-rest samples between
1.991 and 2.013 seconds and confirmed that checkpoint writing is contained in
the recorded rest. The new 308-trigger, imagery-only schedule at TR = 1 second
still requires a complete mock-scanner run.

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
