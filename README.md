# Galaxy Quenching-Stage Classifier GUI Tool

Interactive Tkinter GUI for the visual classification of MaNGA galaxies by quenching stage, using PNG maps (and, optionally, BPT diagrams). Built for post-merger / committee-style morphological classification.

The tool loads galaxy IDs from an input CSV, displays the corresponding image(s), records your classification, and auto-saves progress to an output CSV as you go.

## Scripts

| Script | Description |
|---|---|
| `Galaxy_Classifier.py` | Classifies galaxies from a single quenching-stage map per galaxy. |
| `Galaxy_Classifier_BPT.py` | Same workflow, but displays the quenching-stage map **and** the BPT diagram side by side, so both can be considered when classifying. |

Both scripts save only the galaxy ID and your `Classification_by_eye` label — no other classifier's labels are shown or written.

## Features

- Keyboard-driven and mouse-driven classification
- Visual progress bar with live statistics
- Auto-resizes images to fit the window
- Immediate auto-save after every galaxy (no data lost if you quit early)
- Handles missing images gracefully (flags them instead of crashing)
- Resume support — automatically skips galaxies already classified in the output CSV
- Centered window, dark theme

## Classification Labels

| Key | Label | Meaning |
|---|---|---|
| `1` | SF  | Star-forming |
| `2` | QnR | Quenched, no rejuvenation |
| `3` | cQ  | Centrally quenched |
| `4` | MX  | Mixed |
| `5` | nR  | Not resolved / no ring |
| `6` | fR  | Fully rejuvenated |

Adjust these in the `update_ui` / `on_keypress` methods if your project uses different classes.

## Prerequisites

- Python 3.8+
- Dependencies: `pillow` (Tkinter, `csv`, and `os` are part of the standard library)

```bash
pip install pillow
```

## File Structure

### 1. Input CSV (`INPUT_CSV_PATH`)

Must contain a column with galaxy IDs:

- Preferred column name: `manga_plateifu`
- If your CSV uses a different column name, edit the corresponding line in the script (`load_galaxy_ids` / `load_galaxy_rows`).
- Galaxy IDs in this column **must match the image filenames exactly**.

### 2. Quenching-stage map images (`MAPS_FOLDER`)

Naming convention: `galaxy_{PLATEIFU}_map.png`

### 3. BPT diagram images (`BPT_FOLDER`, `Galaxy_Classifier_BPT.py` only)

Naming convention: `galaxy_{PLATEIFU}_bpt.png`

Update the naming pattern in `load_next_galaxy` if your files are named differently.

### 4. Output CSV (`OUTPUT_CSV_PATH`)

Created automatically on first run with the columns:

```
manga_plateifu, Classification_by_eye
```

If the file already exists, the tool appends to it and resumes from where you left off.

## Setup

1. Install dependencies (see above).
2. Open the script you want to use and update the paths at the top:

```python
SAVE_FOLDER = r"/your/output/folder"
OUTPUT_CSV_PATH = os.path.join(SAVE_FOLDER, "your_results.csv")
INPUT_CSV_PATH = r"/path/to/galaxy_list.csv"
MAPS_FOLDER = r"/path/to/quenching_map/png/images"
BPT_FOLDER = r"/path/to/bpt/png/images"   # Galaxy_Classifier_BPT.py only
```

3. Run the script:

```bash
python Galaxy_Classifier.py
# or
python Galaxy_Classifier_BPT.py
```

## Controls

| Key / Action | Effect |
|---|---|
| `1`–`6` | Select classification (SF / QnR / cQ / MX / nR / fR) |
| `Enter` | Save current classification and move to the next galaxy |
| `Backspace` | Go back and change your selection before saving |
| `Esc` | Quit the app (progress up to the last save is preserved) |

## Notes

- Classification is saved immediately once you press `Enter`/click `SAVE` — closing the app at any point will not lose already-saved work.
- If an image is missing, the panel will show `IMAGE MISSING: <filename>` instead of crashing, so you can flag it and keep going.
