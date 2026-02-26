import requests
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta

# --- CONFIG ---
ENDPOINT = "https://api.myday.cloud/legacy/api/aggregate/v2/calendaritem"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("MyHud Schedule Extractor")
        self.root.geometry("750x650")  # Slightly larger to accommodate padding
        self.current_results = []

        # Apply a cleaner theme if available (clam looks nicer on most OS)
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        self.setup_ui()

    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="University Schedule Extractor", font=("Arial", 16, "bold")).pack(pady=(0, 15))

        # --- CONFIGURATION FRAME ---
        config_frame = ttk.LabelFrame(main_frame, text=" Configuration ", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 15))

        # Token Input
        token_frame = ttk.Frame(config_frame)
        token_frame.pack(fill=tk.X, pady=5)
        ttk.Label(token_frame, text="Bearer Token:", width=15).pack(side=tk.LEFT)
        self.token_entry = ttk.Entry(token_frame, show="*")
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Timeframe Selector
        timeframe_frame = ttk.Frame(config_frame)
        timeframe_frame.pack(fill=tk.X, pady=5)
        ttk.Label(timeframe_frame, text="Timeframe:", width=15).pack(side=tk.LEFT)

        self.range_var = tk.StringVar(value="Current Month")
        dropdown = ttk.Combobox(timeframe_frame, textvariable=self.range_var, state="readonly", width=20)
        dropdown['values'] = ("Current Month", "Full Semester", "Custom Range")
        dropdown.pack(side=tk.LEFT, padx=(5, 0))
        dropdown.bind("<<ComboboxSelected>>", self.toggle_pickers)

        # Custom Date Pickers (Initially Hidden)
        self.picker_frame = ttk.Frame(config_frame)
        ttk.Label(self.picker_frame, text="Start:").pack(side=tk.LEFT, padx=(10, 5))
        self.start_cal = DateEntry(self.picker_frame, width=12, background='darkblue', foreground='white',
                                   borderwidth=2)
        self.start_cal.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(self.picker_frame, text="End:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_cal = DateEntry(self.picker_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_cal.pack(side=tk.LEFT)

        # --- ACTION BUTTONS ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        self.fetch_btn = ttk.Button(btn_frame, text="1. Fetch Data", command=self.run_fetch)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="Clear Preview", command=self.clear_preview)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.download_btn = ttk.Button(btn_frame, text="2. Download .ics", command=self.run_download, state="disabled")
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # --- PREVIEW FRAME (With Scrollbar) ---
        preview_frame = ttk.LabelFrame(main_frame, text=" Data Preview ", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Scrollbar setup
        tree_scroll = ttk.Scrollbar(preview_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(preview_frame, columns=("Subject", "Start", "Location"), show='headings', height=10,
                                 yscrollcommand=tree_scroll.set)
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading("Subject", text="Subject")
        self.tree.heading("Start", text="Date/Time")
        self.tree.heading("Location", text="Location")

        self.tree.column("Subject", width=250, anchor=tk.W)
        self.tree.column("Start", width=150, anchor=tk.CENTER)
        self.tree.column("Location", width=150, anchor=tk.W)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Status Label
        self.status_label = tk.Label(main_frame, text="Ready.", fg="gray", font=("Arial", 9, "italic"))
        self.status_label.pack(anchor=tk.W)

    def toggle_pickers(self, event):
        if self.range_var.get() == "Custom Range":
            self.picker_frame.pack(side=tk.LEFT, fill=tk.X, pady=5, padx=10)
        else:
            self.picker_frame.pack_forget()

    def clear_preview(self):
        """Clears the table, resets the data array, and disables download."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.current_results = []
        self.download_btn.config(state="disabled")
        self.status_label.config(text="Preview cleared.", fg="gray")

    def run_fetch(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning("Error", "Please enter a token.")
            return

        # Determine Date Range
        if self.range_var.get() == "Current Month":
            s_dt = datetime.now().replace(day=1)
            e_dt = (s_dt + timedelta(days=32)).replace(day=1)
        elif self.range_var.get() == "Full Semester":
            s_dt = datetime.now()
            e_dt = s_dt + timedelta(days=180)
        else:
            s_dt = self.start_cal.get_date()
            e_dt = self.end_cal.get_date()

        start_iso = s_dt.strftime("%Y-%m-%dT00:00:00Z")
        end_iso = e_dt.strftime("%Y-%m-%dT00:00:00Z")

        # Clear existing table before new fetch
        self.clear_preview()

        self.status_label.config(text="Fetching data...", fg="blue")
        self.root.update()  # Force UI to update status text immediately

        headers = {"Authorization": f"Bearer {token}" if "Bearer" not in token else token, "Accept": "application/json"}
        params = {"$filter": f"End gt datetime'{start_iso}' and Start lt datetime'{end_iso}'"}

        try:
            res = requests.get(ENDPOINT, headers=headers, params=params)
            if res.status_code == 200:
                self.current_results = res.json().get("results", [])
                if not self.current_results:
                    self.status_label.config(text="No events found for this timeframe.", fg="orange")
                    return

                # Fill Table
                for item in self.current_results:
                    # Minor string cleanup for display if needed
                    subj = item.get("Subject", "N/A")
                    start = item.get("Start", "N/A")
                    loc = item.get("Location", "N/A")
                    self.tree.insert("", tk.END, values=(subj, start, loc))

                self.status_label.config(text=f"Successfully fetched {len(self.current_results)} events.", fg="green")
                self.download_btn.config(state="normal")
            else:
                self.status_label.config(text="Fetch failed.", fg="red")
                messagebox.showerror("Error", f"API Error: {res.status_code}\n{res.text}")
        except Exception as e:
            self.status_label.config(text="Fetch failed.", fg="red")
            messagebox.showerror("Error", str(e))

    def run_download(self):
        if not self.current_results:
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".ics", initialfile="uni_schedule.ics")
        if file_path:
            lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MyHudScraper//EN", "METHOD:PUBLISH"]
            for item in self.current_results:
                # Basic error checking in case keys are missing
                if 'Start' not in item or 'End' not in item:
                    continue
                s = item['Start'].replace("-", "").replace(":", "").split("+")[0] + "Z"
                e = item['End'].replace("-", "").replace(":", "").split("+")[0] + "Z"
                lines.extend(["BEGIN:VEVENT", f"UID:{item.get('Id', 'unknown')}", f"DTSTART:{s}", f"DTEND:{e}",
                              f"SUMMARY:{item.get('Subject', '')}", "END:VEVENT"])
            lines.append("END:VCALENDAR")

            try:
                with open(file_path, "w") as f:
                    f.write("\n".join(lines))
                messagebox.showinfo("Success", "Schedule successfully exported as .ics file!")
                self.status_label.config(text=f"File saved to {file_path}", fg="green")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()