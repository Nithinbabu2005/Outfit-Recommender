README.md
Here is the markdown content for your README.md file.

Markdown

# 👔 AI Smart Wardrobe Manager

A Python-based desktop application that uses **Google Gemini AI** to organize your digital wardrobe and suggest outfits based on real-time weather and specific occasions.

## 🚀 Features

* **🤖 AI Auto-Sorting:** Simply drop mixed photos of your clothes into a dump folder. The AI uses Computer Vision to recognize them and sort them into folders (Shirt, Pant, Shoes, etc.).
* **🌦️ Live Weather Integration:** Automatically fetches current weather conditions (e.g., Bengaluru) to ensure suggestions are practical.
* **🧠 Infinite Stylist Mode:** Generates unique outfit combinations every time.
* **🚫 No-Repeat History:** Remembers the last 10 suggestions to ensure you don't get the same outfit recommendation repeatedly.
* **🎨 UI Dashboard:** A clean Tkinter interface to manage sorting and styling in one place.

## 🛠️ Setup & Installation

### 1. Prerequisites
* Python 3.10+ installed.
* A **Google Gemini API Key** (Free). Get it [here](https://aistudio.google.com/).

### 2. Installation
1.  Clone or download this repository.
2.  Install the required dependencies:
    ```bash
    pip install google-generativeai pillow requests
    ```
3.  Open `main_ui.py` and paste your API Key in the configuration section:
    ```python
    API_KEY = "PASTE_YOUR_KEY_HERE"
    ```

## 📖 How to Use

### Step 1: Add Your Clothes
1.  Take photos of your clothes (try to keep the background simple).
2.  Paste all these images into the **`wardrobe_dump`** folder.

### Step 2: Sort the Wardrobe
1.  Run the application:
    ```bash
    python main_ui.py
    ```
2.  Click the **"📥 Sort 'wardrobe_dump'"** button on the left panel.
3.  Wait as the AI scans your images and moves them into `my_wardrobe/` sorted by category.

### Step 3: Get an Outfit
1.  The app automatically fetches the weather.
2.  Select an **Occasion** from the dropdown (or type your own, e.g., "Friend's Birthday").
3.  Click **"✨ Generate Unique Look"**.
4.  The AI will display a Top, Bottom, and Shoe combination along with a "Stylist Note" explaining why the colors work together.

## 📂 Troubleshooting

* **Error: "Quota Exceeded (429)"**: The app uses the free Gemini tier. If you sort too many images at once, it might pause briefly. The app has a built-in auto-retry system to handle this.
* **Images not showing?**: Ensure your image filenames don't contain special characters or emojis. The sorter automatically renames them to fix this, but existing files might need checking.
* **Weather not updating?**: Check your internet connection. The app defaults to "Offline Mode" if it can't reach the weather service.

## 🔮 Future Enhancements
* Add a "Laundry" status to exclude dirty clothes from suggestions.
* Mobile App integration.
