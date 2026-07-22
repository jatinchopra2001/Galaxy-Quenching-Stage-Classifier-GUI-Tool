import os
import csv
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk

# LOADING DATA AND SAVING FILES
SAVE_FOLDER = r'' #Location of the folder where you are working/ want to save the work
OUTPUT_CSV_PATH = os.path.join(SAVE_FOLDER, "__") #Enter the name of the csv in place of "___" in which you want to save your work

INPUT_CSV_PATH = r'' #Location of the input csv file (used to loop over the galaxy name)
MAPS_FOLDER = r'' #Location of the folder which has the galaxy images

# FORCE CREATE DIRECTORY
os.makedirs(SAVE_FOLDER, exist_ok=True)

class GalaxyClassifier:
    def __init__(self, input_csv, maps_folder, output_csv):
        print("Starting Galaxy Classifier...")
        self.input_csv = input_csv
        self.maps_folder = maps_folder
        self.output_csv = output_csv
        
        self.galaxy_list = self.load_galaxy_list()
        
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
        self.setup_ui()
        self.bind_keys()
        self.initialize_csv()  # Only creates headers if file doesn't exist
        
        self.window.deiconify()
        
        if not self.queue:
            messagebox.showinfo("Done", "All galaxies already classified!")
            self.window.destroy()
        else:
            self.load_next_galaxy()

    def setup_window(self):
        self.window.title("Galaxy Classifier - by_eye")
        self.window.configure(bg="#2b2b2b")
        self.window.geometry("1400x950")
        self.window.minsize(1200, 850)
        
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.window.winfo_screenheight() // 2) - (950 // 2)
        self.window.geometry(f"1400x950+{max(0,x)}+{max(0,y)}")
        
        self.font_size = 10
        self.big_font = 14
        self.btn_width = 16
        self.btn_height = 2

    def load_galaxy_list(self):
        galaxies = []
        try:
            if not os.path.exists(self.input_csv):
                print(f"Input CSV not found: {self.input_csv}")
                return galaxies

            with open(self.input_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return galaxies
                reader.fieldnames = [h.strip() for h in reader.fieldnames]
                
                col = None
                if "manga_plateifu" in reader.fieldnames:
                    col = "manga_plateifu"
                else:
                    candidates = [h for h in reader.fieldnames if "plateifu" in h.lower()]
                    col = candidates[0] if candidates else None
                    
                if not col:
                    print("No plateifu column found")
                    return galaxies

                for row in reader:
                    val = row.get(col, "").strip()
                    if val:
                        galaxies.append(val)
        except Exception as e:
            print(f"CSV read error: {e}")
        return galaxies

    def get_existing_progress(self):
        ids = set()
        try:
            if os.path.exists(self.output_csv):
                print(f"Reading existing progress from: {self.output_csv}")
                with open(self.output_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        pid = row.get("manga_plateifu", "").strip()
                        if pid:
                            ids.add(pid)
                            
        except Exception as e:
            print(f"Error reading progress: {e}")
        return ids

    def initialize_csv(self):
        """ONLY creates headers if file doesn't exist or is empty"""
        fieldnames = [
            "manga_plateifu", "Classification",
            "incorrect_flag", "artefacts_flag", "multiple_sources_flag", "confused_flag"
        ]
        
        # Check if file exists and has content
        if os.path.exists(self.output_csv) and os.path.getsize(self.output_csv) > 0:
            print(f"✅ CSV already exists: {self.output_csv} (will append)")
            return
        
        try:
            # Create new file with headers OR rewrite empty file
            with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            
        except Exception as e:
            print(f"❌ CSV init error: {e}")
            messagebox.showerror("CSV Error", f"Could not create CSV:\n{str(e)}")

    def setup_ui(self):
        top_frame = tk.Frame(self.window, bg="#2b2b2b")
        top_frame.pack(fill=tk.X, pady=(5, 2))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(top_frame, variable=self.progress_var, 
                                          maximum=self.total_count, length=700)
        self.progress_bar.pack(pady=(5, 2))

        self.progress_label = tk.Label(top_frame, text="", font=("Arial", 11), 
                                     bg="#2b2b2b", fg="lightgray")
        self.progress_label.pack(pady=(0, 5))

        image_frame = tk.Frame(self.window, bg="black")
        image_frame.pack(pady=(5, 5), fill=tk.BOTH, expand=True)

        self.image_label = tk.Label(image_frame, bg="black", fg="white", 
                                  text="Loading image...", font=("Arial", 12))
        self.image_label.pack(expand=True)

        self.question_label = tk.Label(self.window, text="", font=("Arial", 14, "bold"),
                                     bg="#2b2b2b", fg="white", wraplength=1200)
        self.question_label.pack(pady=(5, 5))

        self.flag_frame = tk.Frame(self.window, bg="#202020", relief=tk.SUNKEN, bd=1)
        self.flag_frame.pack(pady=(5, 5), padx=10, fill=tk.X)

        self.flag_labels = {}
        flags_info = [
            ("incorrect_re", "Incorrect_re (I)"),
            ("artefacts", "Artefacts (A)"), 
            ("multiple_sources", "Multiple Sources (M)"),
            ("confused", "Confused (C)")
        ]
        
        for key, text in flags_info:
            lbl = tk.Label(self.flag_frame, text=text, font=("Arial", 11, "bold"),
                         bg="#202020", fg="gray", width=22)
            lbl.pack(side=tk.LEFT, padx=5, pady=4)
            self.flag_labels[key] = lbl

        self.button_frame = tk.Frame(self.window, bg="#2b2b2b")
        self.button_frame.pack(pady=(10, 5), fill=tk.X)

        instructions = "KEYS: 1=SF, 2=QnR, 3=cQ, 4= MX, 5=nR, 6=fR, I/A/M/C=Flags, Backspace=Back, Enter=Save&Next, Esc=Quit"
        tk.Label(self.window, text=instructions, font=("Arial", 10, "bold"),
                bg="#2b2b2b", fg="#ffd700", wraplength=1300).pack(pady=(5, 10))

    def bind_keys(self):
        self.window.bind("<Key>", self.on_keypress)
        self.window.bind("<BackSpace>", self.on_backspace)
        self.window.bind("<Return>", self.on_enter)
        self.window.bind("<Escape>", self.on_escape)

    def reset_state(self):
        self.classification = None
        self.current_step = "classify"
        self.flags = {"incorrect_re": 0, "artefacts": 0, "multiple_sources": 0, "confused": 0}

    def load_next_galaxy(self):
        if not self.queue:
            messagebox.showinfo("Complete", "Thank you so much for Helping me!")
            self.window.quit()
            return

        self.current_galaxy_id = self.queue.pop(0)
        self.reset_state()

        self.progress_var.set(self.done_count)
        self.progress_label.config(text=f"Progress: {self.done_count}/{self.total_count}")

        filename = f"galaxy_{self.current_galaxy_id}_map.png"
        filepath = os.path.join(self.maps_folder, filename)
        
        if os.path.exists(filepath):
            self.display_image(filepath)
        else:
            self.image_label.config(text=f"IMAGE MISSING: {filename}", fg="red", font=("Arial", 14, "bold"))

        self.update_ui()

    def display_image(self, filepath):
        try:
            img = Image.open(filepath)
            self.window.update_idletasks()
            available_width = self.window.winfo_width() - 40
            available_height = self.window.winfo_height() * 0.98
            
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            
            if aspect_ratio > 1:
                new_width = min(available_width, 1350)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = min(available_height, 850)
                new_width = int(new_height * aspect_ratio)
            
            img = img.resize((new_width, new_height), Image.ANTIALIAS)

            photo = ImageTk.PhotoImage(img)
            
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
            
        except Exception as e:
            self.image_label.config(text=f"Image load error: {str(e)}", fg="orange")

    def update_flag_labels(self):
        for key, value in self.flags.items():
            lbl = self.flag_labels[key]
            if value == 1:
                lbl.config(fg="#ffd700", font=("Arial", 12, "bold"))
            else:
                lbl.config(fg="lightgray", font=("Arial", 11, "normal"))

    def clear_buttons(self):
        for widget in self.button_frame.winfo_children():
            widget.destroy()

    def add_button(self, text, command, bg="#4a4a4a"):
        btn = tk.Button(self.button_frame, text=text, command=command,
                       font=("Arial", 11, "bold"),
                       bg=bg, fg="white",
                       width=self.btn_width, height=self.btn_height)
        btn.pack(side=tk.LEFT, padx=8, pady=6)

    def update_ui(self):
        self.update_flag_labels()
        self.clear_buttons()

        if self.current_step == "classify":
            self.question_label.config(text=f"Galaxy: {self.current_galaxy_id}\n\nHow would you classify this galaxy?\n\n[1] SF  [2] QnR  [3] cQ  [4] MX  [5] nR  [6] fR")
            self.add_button("SF [1]", lambda: self.set_classification("SF"))
            self.add_button("QnR [2]", lambda: self.set_classification("QnR"))
            self.add_button("cQ [3]", lambda: self.set_classification("cQ"))
            self.add_button("MX [4]", lambda: self.set_classification("MX"))
            self.add_button("nR [5]", lambda: self.set_classification("nR"))
            self.add_button("fR [6]", lambda: self.set_classification("fR"))

        elif self.current_step == "confirm":
            flags_on = [k[0].upper() for k, v in self.flags.items() if v == 1]
            flags_text = ", ".join(flags_on) if flags_on else "None"
            self.question_label.config(text=f"Galaxy {self.current_galaxy_id}\n{self.classification} | Flags: {flags_text}\n\nPress ENTER to SAVE & NEXT or BACKSPACE to edit")
            self.add_button("SAVE & NEXT", self.save_and_next, "#008800")
            self.add_button("BACKSPACE to Edit", self.go_back, "#666666")

    def set_classification(self, classification):
        self.classification = classification
        self.current_step = "confirm"
        self.update_ui()

    def go_back(self):
        if self.current_step == "confirm":
            self.current_step = "classify"
            self.classification = None
        self.update_ui()

    def toggle_flag(self, flag):
        self.flags[flag] = 1 - self.flags[flag]
        self.update_ui()

    def save_and_next(self):
        if not self.classification:
            messagebox.showwarning("Incomplete", "Please set classification!")
            return

        row = {
            "manga_plateifu": self.current_galaxy_id,
            "Classification": self.classification,
            "incorrect_flag": self.flags["incorrect_re"],
            "artefacts_flag": self.flags["artefacts"],
            "multiple_sources_flag": self.flags["multiple_sources"],
            "confused_flag": self.flags["confused"]
        }

        fieldnames = list(row.keys())
        
        try:
            with open(self.output_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Only write header if file is completely empty
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
        
        # Flags
        if key == "i": self.toggle_flag("incorrect_re")
        elif key == "a": self.toggle_flag("artefacts")
        elif key == "m": self.toggle_flag("multiple_sources")
        elif key == "c": self.toggle_flag("confused")

        # Classifications
        if self.current_step == "classify":
            if key == "1": self.set_classification("SF")
            elif key == "2": self.set_classification("QnR")
            elif key == "3": self.set_classification("cQ")
            elif key == "4": self.set_classification("MX")
            elif key == "5": self.set_classification("nR")
            elif key == "6": self.set_classification("fR")

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
        print(f"🎉 FINISHED! Final CSV: {self.output_csv}")
        print(f"📊 Total classified: {self.done_count}/{self.total_count}")

if __name__ == "__main__":
    print("=== GALAXY CLASSIFIER STARTING ===")
    app = GalaxyClassifier(INPUT_CSV_PATH, MAPS_FOLDER, OUTPUT_CSV_PATH)
    app.run()
