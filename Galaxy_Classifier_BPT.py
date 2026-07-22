import os
import csv
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk


SAVE_FOLDER = r""
OUTPUT_CSV_PATH = os.path.join(SAVE_FOLDER, "output_file.csv")

INPUT_CSV_PATH = r"input_file.csv"

# Quenching-stage maps, filenames: galaxy_{PLATEIFU}_map.png
MAPS_FOLDER = r""

# BPT diagrams, filenames: galaxy_{PLATEIFU}_bpt.png
BPT_FOLDER = r""

os.makedirs(SAVE_FOLDER, exist_ok=True)


class GalaxyClassifierBPT:
    def __init__(self, input_csv, maps_folder, bpt_folder, output_csv):
        print("Starting Galaxy Classifier (BPT-aware)...")
        self.input_csv = input_csv
        self.maps_folder = maps_folder
        self.bpt_folder = bpt_folder
        self.output_csv = output_csv

        self.galaxy_list = self.load_galaxy_ids()

        self.classified_ids = self.get_existing_progress()
        print(f"Already classified: {len(self.classified_ids)}")

        self.queue = [g for g in self.galaxy_list if g not in self.classified_ids]
        print(f"Queue: {len(self.queue)} remaining")

        self.total_count = len(self.galaxy_list)
        self.done_count = len(self.classified_ids)
        self.current_galaxy_id = None
        self.reset_state()

        self.window = tk.Tk()
        self.window.withdraw()

        self.setup_window()
        self.setup_styles()
        self.setup_ui()
        self.bind_keys()
        self.initialize_csv()

        self.window.deiconify()

        if not self.queue:
            messagebox.showinfo("Done", "All galaxies already classified.")
            self.window.destroy()
        else:
            self.load_next_galaxy()

    def setup_window(self):
        self.window.title("Galaxy Classifier - Quenching Stage + BPT")
        self.window.configure(bg="#2b2b2b")
        self.window.geometry("1500x1000")
        self.window.minsize(1300, 900)

        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (1000 // 2)
        self.window.geometry(f"1500x1000+{max(0, x)}+{max(0, y)}")

        self.btn_width = 14
        self.btn_height = 2

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "dark.Horizontal.TProgressbar",
            troughcolor="#1e1e1e",
            background="#4caf50",
            bordercolor="#1e1e1e",
            lightcolor="#4caf50",
            darkcolor="#4caf50"
        )

    def load_galaxy_ids(self):
        ids = []
        try:
            if not os.path.exists(self.input_csv):
                print(f"Input CSV not found: {self.input_csv}")
                return ids

            with open(self.input_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return ids

                reader.fieldnames = [h.strip() for h in reader.fieldnames]

                if "manga_plateifu" not in reader.fieldnames:
                    print("Missing required column: 'manga_plateifu'")
                    print(f"Available columns: {reader.fieldnames}")
                    return []

                for row in reader:
                    pid = row.get("manga_plateifu", "").strip()
                    if pid and pid not in ids:
                        ids.append(pid)

        except Exception as e:
            print(f"CSV read error: {e}")

        print(f"Loaded {len(ids)} galaxies from input CSV.")
        return ids

    def get_existing_progress(self):
        ids = set()
        try:
            if not os.path.exists(self.output_csv):
                print("No existing output CSV found — starting fresh.")
                return ids

            with open(self.output_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    print("Output CSV exists but has no header — treating as empty.")
                    return ids

                fieldnames_stripped = [h.strip() for h in reader.fieldnames]

                if "manga_plateifu" not in fieldnames_stripped:
                    print(f"WARNING: Output CSV does not contain 'manga_plateifu' column.\n"
                          f"  Found columns: {fieldnames_stripped}\n"
                          f"  Treating output as empty to avoid skipping unclassified galaxies.")
                    return ids

                if "Classification_by_eye" not in fieldnames_stripped:
                    print("WARNING: Output CSV is missing 'Classification_by_eye' column — "
                          "file may be corrupted or be the input CSV. Treating as empty.")
                    return ids

                for row in reader:
                    pid = row.get("manga_plateifu", "").strip()
                    classification = row.get("Classification_by_eye", "").strip()
                    if pid and classification:
                        ids.add(pid)
                        print(f"  Already classified: {pid}  ->  {classification}")

        except Exception as e:
            print(f"Error reading progress file: {e}")

        return ids

    def initialize_csv(self):
        fieldnames = [
            "manga_plateifu",
            "Classification_by_eye"
        ]

        if os.path.exists(self.output_csv) and os.path.getsize(self.output_csv) > 0:
            print(f"Output CSV already exists: {self.output_csv} (will append)")
            return

        try:
            with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            print(f"Created new output CSV: {self.output_csv}")
        except Exception as e:
            print(f"CSV init error: {e}")
            messagebox.showerror("CSV Error", f"Could not create CSV:\n{str(e)}")

    def setup_ui(self):
        top_frame = tk.Frame(self.window, bg="#2b2b2b")
        top_frame.pack(fill=tk.X, pady=(5, 2))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            top_frame,
            variable=self.progress_var,
            maximum=self.total_count,
            length=700,
            style="dark.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(pady=(5, 2))

        self.progress_label = tk.Label(
            top_frame,
            text="",
            font=("Arial", 11),
            bg="#2b2b2b",
            fg="lightgray"
        )
        self.progress_label.pack(pady=(0, 5))

        self.galaxy_id_label = tk.Label(
            top_frame,
            text="",
            font=("Consolas", 13, "bold"),
            bg="#2b2b2b",
            fg="#e8e8e8"
        )
        self.galaxy_id_label.pack(pady=(0, 5))

        # Side-by-side image panel: quenching map (left) + BPT diagram (right)
        images_frame = tk.Frame(self.window, bg="black")
        images_frame.pack(pady=(5, 5), fill=tk.BOTH, expand=True)

        map_col = tk.Frame(images_frame, bg="black")
        map_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))

        tk.Label(map_col, text="Quenching Stage Map", font=("Arial", 11, "bold"),
                 bg="black", fg="#ffd700").pack(pady=(4, 2))
        self.map_label = tk.Label(map_col, bg="black", fg="white",
                                   text="Loading image...", font=("Arial", 12))
        self.map_label.pack(expand=True)

        bpt_col = tk.Frame(images_frame, bg="black")
        bpt_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))

        tk.Label(bpt_col, text="BPT Diagram", font=("Arial", 11, "bold"),
                 bg="black", fg="#ffd700").pack(pady=(4, 2))
        self.bpt_label = tk.Label(bpt_col, bg="black", fg="white",
                                   text="Loading image...", font=("Arial", 12))
        self.bpt_label.pack(expand=True)

        self.question_label = tk.Label(
            self.window,
            text="",
            font=("Arial", 14, "bold"),
            bg="#2b2b2b",
            fg="white",
            wraplength=1300
        )
        self.question_label.pack(pady=(5, 5))

        self.button_frame = tk.Frame(self.window, bg="#2b2b2b")
        self.button_frame.pack(pady=(10, 5), fill=tk.X)

        instructions = "KEYS: 1=SF, 2=QnR, 3=cQ, 4=MX, 5=nR, 6=fR, Backspace=Back, Enter=Save, Esc=Quit"
        tk.Label(
            self.window,
            text=instructions,
            font=("Arial", 10, "bold"),
            bg="#2b2b2b",
            fg="#ffd700",
            wraplength=1400
        ).pack(pady=(5, 10))

    def bind_keys(self):
        self.window.bind("<Key>", self.on_keypress)
        self.window.bind("<BackSpace>", self.on_backspace)
        self.window.bind("<Return>", self.on_enter)
        self.window.bind("<Escape>", self.on_escape)

    def reset_state(self):
        self.classification = None
        self.current_step = "classify"

    def load_next_galaxy(self):
        if not self.queue:
            messagebox.showinfo("Complete", "All galaxies classified!")
            self.window.quit()
            return

        self.current_galaxy_id = self.queue.pop(0)
        self.reset_state()

        self.progress_var.set(self.done_count)
        self.progress_label.config(text=f"Progress: {self.done_count}/{self.total_count}")
        self.galaxy_id_label.config(text=f"Galaxy: {self.current_galaxy_id}")

        map_filename = f"galaxy_{self.current_galaxy_id}_map.png"
        map_filepath = os.path.join(self.maps_folder, map_filename)
        self.display_image(map_filepath, self.map_label, map_filename)

        bpt_filename = f"galaxy_{self.current_galaxy_id}_bpt.png"
        bpt_filepath = os.path.join(self.bpt_folder, bpt_filename)
        self.display_image(bpt_filepath, self.bpt_label, bpt_filename)

        self.update_ui()

    def display_image(self, filepath, label_widget, filename):
        if not os.path.exists(filepath):
            label_widget.config(
                image="",
                text=f"IMAGE MISSING:\n{filename}",
                fg="red",
                font=("Arial", 13, "bold")
            )
            label_widget.image = None
            return

        try:
            img = Image.open(filepath)
            self.window.update_idletasks()

            available_width = (self.window.winfo_width() // 2) - 40
            available_height = int(self.window.winfo_height() * 0.55)

            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            if aspect_ratio > 1:
                new_width = min(available_width, 650)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = min(available_height, 800)
                new_width = int(new_height * aspect_ratio)

            new_width = max(new_width, 1)
            new_height = max(new_height, 1)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            label_widget.config(image=photo, text="")
            label_widget.image = photo

        except Exception as e:
            label_widget.config(text=f"Image load error: {str(e)}", fg="orange")

    def clear_buttons(self):
        for widget in self.button_frame.winfo_children():
            widget.destroy()

    def add_button(self, text, command, bg="#4a4a4a"):
        btn = tk.Button(
            self.button_frame,
            text=text,
            command=command,
            font=("Arial", 11, "bold"),
            bg=bg,
            fg="white",
            width=self.btn_width,
            height=self.btn_height,
            activebackground=bg,
            activeforeground="white"
        )
        btn.pack(side=tk.LEFT, padx=8, pady=6)

    def update_ui(self):
        self.clear_buttons()

        if self.current_step == "classify":
            self.question_label.config(
                text="Considering both the quenching map and the BPT diagram, "
                     "how do you want to classify the galaxy?"
            )
            self.add_button("SF [1]", lambda: self.set_type("SF"), "#2e8b57")
            self.add_button("QnR [2]", lambda: self.set_type("QnR"), "#3b7ddd")
            self.add_button("cQ [3]", lambda: self.set_type("cQ"), "#9b59b6")
            self.add_button("MX [4]", lambda: self.set_type("MX"), "#cc8844")
            self.add_button("nR [5]", lambda: self.set_type("nR"), "#888888")
            self.add_button("fR [6]", lambda: self.set_type("fR"), "#cc4444")

        elif self.current_step == "confirm":
            self.question_label.config(
                text=(
                    f"Galaxy {self.current_galaxy_id}\n"
                    f"Selected classification: {self.classification}\n\n"
                    f"Press ENTER or click SAVE to confirm"
                )
            )
            self.add_button("SAVE", self.save_and_next, "#008800")
            self.add_button("Back", self.go_back, "#666666")

    def set_type(self, classification):
        self.classification = classification
        self.current_step = "confirm"
        self.update_ui()

    def go_back(self):
        if self.current_step == "confirm":
            self.current_step = "classify"
            self.classification = None
        self.update_ui()

    def save_and_next(self):
        if not self.classification:
            messagebox.showwarning("Incomplete", "Please choose a classification.")
            return

        row = {
            "manga_plateifu": self.current_galaxy_id,
            "Classification_by_eye": self.classification
        }

        fieldnames = list(row.keys())

        try:
            with open(self.output_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if os.path.getsize(self.output_csv) == 0:
                    writer.writeheader()
                writer.writerow(row)

            self.done_count += 1
            self.classified_ids.add(self.current_galaxy_id)
            self.load_next_galaxy()

        except Exception as e:
            messagebox.showerror("SAVE ERROR", f"Error saving:\n{self.output_csv}\n\n{e}")

    def on_keypress(self, event):
        key = event.char.lower() if event.char else ""

        if self.current_step == "classify":
            if key == "1":
                self.set_type("SF")
            elif key == "2":
                self.set_type("QnR")
            elif key == "3":
                self.set_type("cQ")
            elif key == "4":
                self.set_type("MX")
            elif key == "5":
                self.set_type("nR")
            elif key == "6":
                self.set_type("fR")

    def on_backspace(self, event):
        self.go_back()

    def on_enter(self, event):
        if self.current_step == "confirm":
            self.save_and_next()

    def on_escape(self, event):
        self.window.quit()

    def run(self):
        print("Entering mainloop...")
        self.window.mainloop()
        print(f"FINISHED! Final CSV: {self.output_csv}")
        print(f"Total classified: {self.done_count}/{self.total_count}")


if __name__ == "__main__":
    print("=== GALAXY CLASSIFIER (BPT-aware) STARTING ===")
    app = GalaxyClassifierBPT(INPUT_CSV_PATH, MAPS_FOLDER, BPT_FOLDER, OUTPUT_CSV_PATH)
    app.run()
