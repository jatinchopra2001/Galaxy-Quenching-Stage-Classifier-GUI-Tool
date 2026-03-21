# Galaxy-Classifier-GUI-Tool
This project is created to classify galaxies based on their quenching stage. It requires inital input CSV file and the quenching stage maps.

Overview
Interactive Tkinter GUI for visual classification of MaNGA galaxies using PNG maps. Designed for committee-style morphological classification of post-merger candidates.

Loads galaxy IDs from input CSV → displays PNG images → records classifications + quality flags → saves to output CSV.

Key Features
 * Keyboard-driven and mouse-driven

 * Visual progress bar + statistics

 * Auto-resizes images to fit the screen

 * Immediate auto-save per galaxy

 * Handles missing images

 * Supports resume capability - skips already classified galaxies.

 * Centred window + dark theme

Prerequisites & File Structure
1. Input CSV (INPUT_CSV_PATH)
   
   **Required**: Column with galaxy names (plateifu IDs):
- Preferred: `manga_plateifu`
- If another format, then please edit the code with the name-format of your galaxies
- Galaxy ID from this column MUST match PNG filenames exactly.

2. PNG Images (MAPS_FOLDER)
   **Naming format**: `galaxy_{PLATEIFU}_map.png`, change it if needed
   
Setup Instructions
 * Install dependencies: pillow, pandas, numpy.
 * Update paths (top of script):

   SAVE_FOLDER = r"/your/output/folder"
   
   OUTPUT_CSV_PATH = os.path.join(SAVE_FOLDER, "your_results.csv"
   
   INPUT_CSV_PATH = r"/path/to/galaxy_list.csv"
   
   MAPS_FOLDER = r"/path/to/png/images"
   


   
