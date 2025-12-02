import os
import shutil
import time
import random
import threading
import json
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import google.generativeai as genai

# --- CONFIGURATION ---
# ⚠️ Your API Key
API_KEY = "API_Key"
genai.configure(api_key=API_KEY)

# Folders
BASE_DIR = os.getcwd()
DUMP_FOLDER = os.path.join(BASE_DIR, "wardrobe_dump")
WARDROBE_FOLDER = os.path.join(BASE_DIR, "my_wardrobe")

# The EXACT categories you requested
VALID_CATEGORIES = ["Shirt", "Tshirt", "Pant", "Shorts", "Shoes"]


# --- BACKEND LOGIC ---

def setup_model():
    """Auto-detects the best model."""
    try:
        found_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for name in found_models:
            if 'flash' in name.lower(): return genai.GenerativeModel(name)
        return genai.GenerativeModel(found_models[0]) if found_models else None
    except:
        return None


model = setup_model()


def find_file_path(filename):
    """Searches for a filename inside the categorized folders."""
    if not os.path.exists(WARDROBE_FOLDER): return None
    for root, dirs, files in os.walk(WARDROBE_FOLDER):
        if filename in files:
            return os.path.join(root, filename)
    return None


def fetch_live_weather(city="Bengaluru"):
    try:
        response = requests.get(f"https://wttr.in/{city}?format=%C+%t", timeout=5)
        return response.text.strip() if response.status_code == 200 else "Unavailable"
    except:
        return "Offline Mode"


def clean_folder_structure():
    """Merges old messy folders into the new clean structure."""
    if not os.path.exists(WARDROBE_FOLDER): return
    corrections = {
        "Pants": "Pant", "Formal_Shirt": "Shirt",
        "Formal_Trousers": "Pant", "Jeans": "Pant", "T-Shirt": "Tshirt"
    }
    for old_name, new_name in corrections.items():
        old_path = os.path.join(WARDROBE_FOLDER, old_name)
        new_path = os.path.join(WARDROBE_FOLDER, new_name)
        if os.path.exists(old_path):
            os.makedirs(new_path, exist_ok=True)
            for f in os.listdir(old_path):
                try:
                    shutil.move(os.path.join(old_path, f), os.path.join(new_path, f))
                except:
                    pass
            try:
                os.rmdir(old_path)
            except:
                pass


# --- TKINTER UI CLASS ---

class SmartWardrobeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("👔 AI Smart Wardrobe (No-Repeat Mode)")
        self.root.geometry("1100x780")
        self.root.configure(bg="#f8f9fa")

        # --- MEMORY FOR HISTORY ---
        # Stores the last 10 outfit combinations to prevent repetition
        self.history = []

        clean_folder_structure()

        # Styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 11), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground="#2c3e50", background="white")

        # --- LEFT PANEL (Controls) ---
        left_panel = tk.Frame(root, bg="white", width=340, padx=25, pady=25)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)

        ttk.Label(left_panel, text="Control Panel", style="Header.TLabel").pack(pady=(0, 30))

        # 1. Sorting
        lbl_sort = tk.LabelFrame(left_panel, text="1. New Clothes?", bg="white", font=("Segoe UI", 12, "bold"),
                                 fg="#34495e", padx=15, pady=15)
        lbl_sort.pack(fill="x", pady=10)

        self.btn_sort = ttk.Button(lbl_sort, text="📥 Sort 'wardrobe_dump'", command=self.start_sorting)
        self.btn_sort.pack(fill="x")
        self.lbl_sort_status = tk.Label(lbl_sort, text="Ready to sort", bg="white", fg="gray", font=("Segoe UI", 9))
        self.lbl_sort_status.pack(pady=5)

        # 2. Recommendation
        lbl_rec = tk.LabelFrame(left_panel, text="2. Stylist", bg="white", font=("Segoe UI", 12, "bold"), fg="#34495e",
                                padx=15, pady=15)
        lbl_rec.pack(fill="x", pady=20)

        # Weather
        tk.Label(lbl_rec, text="Current Weather:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_weather = tk.Label(lbl_rec, text="Fetching...", bg="#ecf0f1", font=("Segoe UI", 10), padx=8, pady=4,
                                    relief="sunken", bd=1)
        self.lbl_weather.pack(fill="x", pady=(2, 15))

        # Occasion (UPDATED: Manual Entry Enabled)
        tk.Label(lbl_rec, text="Occasion (Type or Select):", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.occasion_var = tk.StringVar()

        # Removed state="readonly" so you can type manually
        self.combo_occasion = ttk.Combobox(lbl_rec, textvariable=self.occasion_var, font=("Segoe UI", 10))
        self.combo_occasion['values'] = ("Office", "College", "Job Interview", "Casual Hangout", "Date Night", "Party",
                                         "Travel")
        self.combo_occasion.current(3)
        self.combo_occasion.pack(fill="x", pady=(2, 20))

        # Big Generate Button
        self.btn_rec = ttk.Button(lbl_rec, text="✨ Generate Unique Look", command=self.start_recommendation)
        self.btn_rec.pack(fill="x", pady=10)

        self.lbl_loading = tk.Label(left_panel, text="", bg="white", fg="#e67e22", font=("Segoe UI", 10, "bold"))
        self.lbl_loading.pack(pady=10)

        # --- RIGHT PANEL (Display) ---
        right_panel = tk.Frame(root, bg="#f8f9fa", padx=40, pady=40)
        right_panel.pack(side="right", fill="both", expand=True)

        self.lbl_suggestion_title = tk.Label(right_panel, text="Suggested Look", font=("Segoe UI", 18, "bold"),
                                             bg="#f8f9fa", fg="#2c3e50")
        self.lbl_suggestion_title.pack(anchor="center", pady=(0, 20))

        # Image Slots
        self.img_frame = tk.Frame(right_panel, bg="#f8f9fa")
        self.img_frame.pack(pady=10)

        self.slot_top = self.create_image_slot(self.img_frame, "TOP WEAR")
        self.slot_bottom = self.create_image_slot(self.img_frame, "BOTTOM WEAR")
        self.slot_shoes = self.create_image_slot(self.img_frame, "FOOTWEAR")

        # Text Info
        tk.Label(right_panel, text="Why this works:", font=("Segoe UI", 12, "bold"), bg="#f8f9fa", fg="#34495e").pack(
            anchor="w", pady=(25, 5))
        self.txt_reason = tk.Text(right_panel, height=4, font=("Segoe UI", 11), bg="white", relief="flat", padx=15,
                                  pady=15, wrap="word", highlightthickness=1, highlightbackground="#dcdcdc")
        self.txt_reason.pack(fill="x")
        self.txt_reason.config(state="disabled")

        self.lbl_quote = tk.Label(right_panel, text='""', font=("Georgia", 14, "italic"), bg="#f8f9fa", fg="#7f8c8d")
        self.lbl_quote.pack(pady=20)

        self.update_weather_ui()

    def create_image_slot(self, parent, title):
        frame = tk.Frame(parent, bg="white", bd=0, highlightbackground="#bdc3c7", highlightthickness=1, padx=10,
                         pady=10)
        frame.pack(side="left", padx=15)
        tk.Label(frame, text=title, bg="white", fg="#95a5a6", font=("Segoe UI", 9, "bold")).pack(pady=(0, 5))
        canvas = tk.Canvas(frame, width=200, height=220, bg="#fafafa", highlightthickness=0)
        canvas.pack()
        canvas.create_text(100, 110, text="?", fill="#bdc3c7", font=("Segoe UI", 20))
        return {"canvas": canvas, "frame": frame}

    def update_weather_ui(self):
        def task():
            w = fetch_live_weather()
            self.root.after(0, lambda: self.lbl_weather.config(text=w))

        threading.Thread(target=task, daemon=True).start()

    # --- 1. SORTING LOGIC ---
    def start_sorting(self):
        self.btn_sort.config(state="disabled")
        self.lbl_sort_status.config(text="Processing...", fg="orange")
        threading.Thread(target=self.run_sorter_thread, daemon=True).start()

    def run_sorter_thread(self):
        if not os.path.exists(DUMP_FOLDER): os.makedirs(DUMP_FOLDER)
        files = [f for f in os.listdir(DUMP_FOLDER) if f.lower().endswith(('.jpg', '.png'))]

        if not files:
            self.update_sort_status("No files found.", "red")
            return

        for i, filename in enumerate(files):
            img_path = os.path.join(DUMP_FOLDER, filename)
            try:
                image = Image.open(img_path)
                image.load()

                prompt = """
                Analyze this clothing.
                Classify it into EXACTLY one of these categories:
                1. Shirt (Formal or Casual shirts)
                2. Tshirt (Tees, Polos)
                3. Pant (Jeans, Trousers, Joggers)
                4. Shorts (Shorts, 3/4th pants)
                5. Shoes (Sneakers, Formal shoes, Sandals)

                Format: Category|Color_Description
                Example: Tshirt|Blue_Polo
                """

                response = None
                for _ in range(3):
                    try:
                        response = model.generate_content([prompt, image])
                        break
                    except:
                        time.sleep(5)

                image.close()

                if response:
                    text_result = response.text.strip()
                    if "|" in text_result:
                        cat, desc = text_result.split("|")
                        cat = cat.strip().replace(" ", "")
                        desc = desc.strip().replace(" ", "_")
                    else:
                        cat, desc = "Unsorted", "Item"

                    if "T-Shirt" in cat or "Tee" in cat: cat = "Tshirt"
                    if "Short" in cat or "3/4" in cat: cat = "Shorts"
                    if "Trouser" in cat or "Jean" in cat: cat = "Pant"

                    if cat not in VALID_CATEGORIES:
                        if "Boot" in cat:
                            cat = "Shoes"
                        else:
                            cat = "Unsorted"

                    dest = os.path.join(WARDROBE_FOLDER, cat)
                    os.makedirs(dest, exist_ok=True)

                    new_name = f"{desc}_{random.randint(1000, 9999)}{os.path.splitext(filename)[1]}"
                    shutil.move(img_path, os.path.join(dest, new_name))

                    self.root.after(0, lambda n=new_name: self.lbl_sort_status.config(text=f"Sorted: {n}", fg="green"))
                    time.sleep(3)

            except Exception as e:
                print(e)

        self.update_sort_status("Sorting Complete!", "green")

    def update_sort_status(self, text, color):
        self.root.after(0, lambda: self.finish_sort_ui(text, color))

    def finish_sort_ui(self, text, color):
        self.lbl_sort_status.config(text=text, fg=color)
        self.btn_sort.config(state="normal")

    # --- 2. RECOMMENDATION LOGIC (NO REPEAT MODE) ---
    def start_recommendation(self):
        self.btn_rec.config(state="disabled")
        self.lbl_loading.config(text="🧠 Checking History & Styling...")
        threading.Thread(target=self.run_rec_thread, daemon=True).start()

    def run_rec_thread(self):
        inventory = {}
        if os.path.exists(WARDROBE_FOLDER):
            for cat in os.listdir(WARDROBE_FOLDER):
                path = os.path.join(WARDROBE_FOLDER, cat)
                if os.path.isdir(path):
                    items = os.listdir(path)
                    random.shuffle(items)
                    inventory[cat] = items

        if not inventory:
            self.root.after(0, lambda: messagebox.showerror("Empty", "Please sort images first!"))
            self.root.after(0, lambda: self.reset_rec_ui())
            return

        weather = self.lbl_weather.cget("text")
        occasion = self.occasion_var.get()

        # Retry Loop to ensure uniqueness
        max_retries = 3
        unique_outfit_found = False
        data = {}

        for attempt in range(max_retries):
            # Tell AI about history to avoid it (Optimization)
            history_str = ", ".join([f"({t}+{b})" for t, b, s in self.history])

            prompt = f"""
            Act as a fashion stylist.
            INVENTORY: {json.dumps(inventory)}
            CONTEXT: Weather={weather}, Occasion={occasion}
            PREVIOUSLY WORN COMBINATIONS (Do not repeat): {history_str}

            TASK: Select a fresh outfit (Top, Bottom, Shoes).

            RESPONSE FORMAT (JSON):
            {{
                "top": "filename...",
                "bottom": "filename...",
                "shoes": "filename...",
                "reason": "Complete sentence explaining color coordination.",
                "quote": "Short quote."
            }}
            """

            try:
                response = model.generate_content(prompt)
                text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(text)

                # Check History in Python (Robustness)
                # We create a signature tuple (Top, Bottom, Shoes)
                outfit_signature = (data.get("top"), data.get("bottom"), data.get("shoes"))

                # Check if this exact top+bottom combo was used recently
                combo_check = (data.get("top"), data.get("bottom"))

                is_duplicate = False
                for past_top, past_bottom, past_shoes in self.history:
                    if past_top == data.get("top") and past_bottom == data.get("bottom"):
                        is_duplicate = True
                        break

                if is_duplicate:
                    print(f"⚠️ Duplicate suggested (Attempt {attempt + 1}): {combo_check}. Retrying...")
                    continue  # Try again
                else:
                    # Valid unique outfit!
                    unique_outfit_found = True

                    # Update History
                    self.history.append(outfit_signature)
                    if len(self.history) > 10:  # Keep only last 10
                        self.history.pop(0)
                    break

            except Exception as e:
                print(f"Error: {e}")
                time.sleep(2)

        if unique_outfit_found:
            self.root.after(0, lambda: self.display_outfit(data))
        else:
            # Fallback if AI keeps suggesting the same thing
            self.root.after(0, lambda: self.display_outfit(data))
            print("Could not find unique outfit after retries, showing best guess.")

        self.root.after(0, lambda: self.reset_rec_ui())

    def reset_rec_ui(self):
        self.btn_rec.config(state="normal")
        self.lbl_loading.config(text="")

    def display_outfit(self, data):
        # Update Text
        self.txt_reason.config(state="normal")
        self.txt_reason.delete("1.0", tk.END)
        self.txt_reason.insert("1.0", data.get('reason', ''))
        self.txt_reason.config(state="disabled")
        self.lbl_quote.config(text=f'"{data.get("quote", "")}"')

        # Update Images
        def load_img(filename, canvas):
            path = find_file_path(filename)
            canvas.delete("all")
            if path and os.path.exists(path):
                try:
                    img = Image.open(path)
                    img.thumbnail((200, 220))
                    photo = ImageTk.PhotoImage(img)
                    canvas.create_image(100, 110, image=photo, anchor="center")
                    canvas.image = photo
                except:
                    canvas.create_text(100, 110, text="Error")
            else:
                canvas.create_text(100, 110, text="Not Found", fill="red")

        load_img(data.get("top"), self.slot_top["canvas"])
        load_img(data.get("bottom"), self.slot_bottom["canvas"])
        load_img(data.get("shoes"), self.slot_shoes["canvas"])


# --- RUN APP ---
if __name__ == "__main__":
    if not model:
        print("CRITICAL: No AI Model found.")
    else:
        root = tk.Tk()
        app = SmartWardrobeApp(root)

        root.mainloop()
