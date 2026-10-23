# Imagery and visual perception retinotopy

This PsychoPy experiment uses tone-paced sequences of rotating polar-angle
sectors, horizontal sweeps of a vertical bar, and vertical sweeps of a
horizontal bar. The dialog selects a visible guide followed by imagery, pure
imagery, or visual perception. All three designs start each trial with a
four-second grid and two-tone preview.

The run type selects timing:

- **Practice:** runs from the computer clock in a window.
- **fMRI:** runs fullscreen and advances from scanner triggers.

The design selects what the participant sees:

- **Visual guide + imagery:** one visible mask sequence, then two imagined
  repetitions with the grid and tones.
- **Pure imagery:** three imagined repetitions with the grid and tones; no
  sector or bar mask appears.
- **Visual perception:** three visible mask repetitions with the grid and tones;
  each nonblank mask stays at full opacity for its position interval.

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
mock_scanner --tr 1 --volumes 320 --trigger 5 --gui
```

In a second terminal, from this project directory, start:

```sh
uv run python src/main.py
```

In the setup dialog select:

- the subject ID;
- `fMRI` as the run type;
- `Visual guide + imagery`, `Pure imagery`, or `Visual perception` as the design;
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
| Design | Visible guide followed by imagery, pure imagery, or visual perception. |
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
3. Use the grid and two low tones to prepare for each trial.
4. In visual-guide runs, watch the mask sequence once, then imagine it twice.
   In pure-imagery runs, imagine the sequence three times without a visible mask.
   In visual-perception runs, watch the visible sequence three times.
5. Use each position tone to advance to the next position.
6. Remain still; no button response is required.

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
4. Three randomized trials, each with a four-second grid and tone preview. The
   first two are followed by 10 TRs of fixation and
   the final trial is followed by 5 TRs of fixation.
5. Data are checkpointed during each rest.
6. Final data and PyPRF files are written before the window closes.

There are 4 rest periods: 1 TR before trial 1, 10 TRs after each of the first two
trials, and 5 TRs after the final trial.

### Sector trial

The sector sequence covers 12 clockwise 60-degree wedge positions, starting at
the top:

```text
90, 60, 30, 0, 330, 300, 270, 240, 210, 180, 150, 120 degrees
```

Each position lasts 2 seconds. Visual-guide runs show the wedge sequence once,
then cue two imagery repetitions. Pure-imagery runs cue three repetitions without
showing wedges. Visual-perception runs show the wedge sequence three times at
full opacity. The sector grid remains visible during all three designs.

- Visual-guide sequence: 24 seconds visible + 48 seconds imagery
- Pure-imagery sequence: 72 seconds imagery
- Visual-perception sequence: 72 seconds visible
- Preview: 4 seconds; total trial: 76 seconds in every design

### Vertical-bar trial

The vertical-bar sequence moves left to right and then right to left:

```text
blank, 00, 01, 02, 03, 04, 05, 06,
blank,
06, 05, 04, 03, 02, 01, 00, blank
```

Each position lasts 2 seconds. `vertical_bar_03` is the central bar.
The vertical-bar grid remains visible. Visual-guide runs show the bar sequence
once and cue two imagery repetitions; pure-imagery runs cue three repetitions
without showing bars. Visual-perception runs show three visible repetitions at
full opacity for every nonblank bar position.

- Visual-guide sequence: 34 seconds visible + 68 seconds imagery
- Pure-imagery sequence: 102 seconds imagery
- Visual-perception sequence: 102 seconds visible
- Preview: 4 seconds; total trial: 106 seconds in every design

### Horizontal-bar trial

The horizontal-bar sequence moves from bottom to top and then top to bottom. It
uses the same sequence structure as the vertical-bar trial:

```text
blank, 00, 01, 02, 03, 04, 05, 06,
blank,
06, 05, 04, 03, 02, 01, 00, blank
```

Each imagined position lasts 2 seconds. `horizontal_bar_03` is the central bar.
The horizontal-bar grid remains visible. The sequence timing and repetitions
match the vertical-bar trial.

- Visual-guide sequence: 34 seconds visible + 68 seconds imagery
- Pure-imagery sequence: 102 seconds imagery
- Visual-perception sequence: 102 seconds visible
- Preview: 4 seconds; total trial: 106 seconds in every design

## Tones

- Low tone: 440 Hz for ordinary positions.
- High tone: 880 Hz for sector cardinal positions, the central bar, and blank
  bar-transition positions.
- Tone duration: 250 ms, stereo.
- Preview: two low tones, two seconds apart, with the trial grid visible.

Visible-position tones are scheduled on the mask flip. Imagery tone commands mark
the cued position onsets. These are software timestamps, not measurements of
physical acoustic onset.

## Timing at TR = 1 second

| Component | Total |
|---|---:|
| One sector sequence | 72 s |
| Two bar sequences | 204 s |
| Three grid and tone previews | 12 s |
| Initial rest | 1 s |
| Two inter-trial rests | 20 s |
| Final rest | 5 s |
| **Task from trigger 6** | **314 s (5:14)** |

The five dummy intervals add 5 seconds. A complete fMRI run therefore uses about
320 triggers and lasts approximately 5:19 from trigger 1 through the final rest.
Each 2-second position spans two scanner volumes at TR = 1 second.

For other TR values, the program uses:

```text
preview tone gap   = max(1, ceil(2 / TR))
position interval  = max(1, ceil(2 / TR))
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
- Grid opacity: constant 1.0

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
- `fmri_prf_design_<subject>_runNN_<timestamp>.csv` — preview, visual, imagery, and rest
  design intervals;
- `fmri_volumes_<subject>_runNN_<timestamp>.csv` — design overlap per volume;
- `pyprf_<subject>_runNN_<timestamp>_frames/` — binary model masks and
  `manifest.csv`.

The frame directory contains one PNG per **raw BOLD volume**. `frame_001.png`
matches volume 1, and `manifest.csv` has the same `tr_index` as the BOLD volume.
The first five dummy frames, rests, previews, and blank-bar positions are black.
In both imagery designs, nonblank imagery frames show the cued sector or bar
position for the pRF model, even though no mask is displayed to the participant.
Visible-guide intervals are black in that imagery model. In visual-perception
runs, nonblank visual frames show the displayed sector or bar; every mask stays
at full opacity on screen. The manifest and JSON log identify the selected
design. The trigger, design, and volume CSVs also include `design_mode`. At TR =
1 second, a complete run is expected to produce 320 frames and 320 trigger rows.
The final volume interval uses the entered TR because no later trigger marks its
end; the volume CSV labels this boundary `nominal_last_tr`.

This matches the one-frame-per-BOLD-volume convention used by the MATLAB
`run_prf*.m` loaders without shifting or padding the frames. The visual-guide
run's visual phase remains black in the model input so the fit uses imagery cues
only; the visual-perception model uses the visible positions instead. Compare
the actual manifest and BOLD volume counts before fitting. Direct loading
requires the acquisition to save one BOLD volume per received trigger and
preprocessing to retain the same volumes. The experiment cannot establish
that absolute alignment from software triggers alone.

## Before collecting real data

Complete this checklist in the scanner room:

- Confirm the selected projector display and 1920 × 1200 presentation.
- Confirm physical stimulus size and viewing distance.
- Confirm that the scanner produces one `5` trigger per TR.
- Confirm the TR entered in the dialog matches the acquisition protocol.
- Confirm HDMI/projector audio and that 440/880 Hz cues are distinguishable.
- Run a short trigger test and inspect the JSON and trigger CSV.
- Confirm that trigger 1 corresponds to raw BOLD volume 1 and that preprocessing
  retained the five dummy volumes before matching to the model frames.

## Verification status

An earlier design completed a mock-scanner run and checkpoint-timing test. The
three selectable designs and their full-volume model exports still require a
complete mock-scanner run each, followed by checks against the saved timing
tables and BOLD acquisition metadata.

Real data collection also requires projector, audio, and physical scanner-trigger
acceptance in the scanner room.

Syntax check:

```sh
uv run python -m py_compile src/main.py
```

Scanner-key self-check on a machine with a graphical display:

```sh
uv run python src/main.py --check
```
