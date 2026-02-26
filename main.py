import requests
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import uuid
import threading
import queue

# --- CONFIG ---
ENDPOINT = "https://api.myday.cloud/legacy/api/aggregate/v2/calendaritem"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("MyHud Schedule Extractor")
        self.root.geometry("750x650")
        self.current_results = []
        self.is_dark_mode = False

        self.fetch_queue = queue.Queue()

        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')

        self.setup_ui()

    def setup_ui(self):
        self.main_frame = ttk.Frame(self.root, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.theme_btn = tk.Button(
            self.main_frame,
            text="🌙",
            command=self.toggle_theme,
            font=("Segoe UI Emoji", 14),
            bd=0,
            cursor="hand2"
        )
        self.theme_btn.place(relx=1.0, rely=0.0, anchor='ne')

        ttk.Label(self.main_frame, text="University Schedule Extractor", font=("Arial", 16, "bold")).pack(pady=(0, 15))

        # --- CONFIGURATION FRAME ---
        config_frame = ttk.LabelFrame(self.main_frame, text=" Configuration ", padding=10)
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

        # Custom Date Pickers
        self.picker_frame = ttk.Frame(config_frame)
        ttk.Label(self.picker_frame, text="Start:").pack(side=tk.LEFT, padx=(10, 5))
        self.start_cal = DateEntry(self.picker_frame, width=12, background='darkblue', foreground='white',
                                   borderwidth=2)
        self.start_cal.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(self.picker_frame, text="End:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_cal = DateEntry(self.picker_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_cal.pack(side=tk.LEFT)

        # --- ACTION BUTTONS ---
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)

        self.fetch_btn = ttk.Button(btn_frame, text="1. Fetch Data", command=self.start_fetch_thread)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="Clear Preview", command=self.clear_preview)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.download_btn = ttk.Button(btn_frame, text="2. Download .ics", command=self.run_download, state="disabled")
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # --- PREVIEW FRAME ---
        preview_frame = ttk.LabelFrame(self.main_frame, text=" Data Preview ", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

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

        # --- STATUS & LOADING FRAME ---
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(status_frame, text="Ready.", fg="gray", font=("Arial", 9, "italic"))
        self.status_label.pack(side=tk.LEFT)

        # Help Button explicitly placed on the far right of the status bar
        self.info_btn = tk.Button(
            status_frame,
            text="ℹ️ Help",
            command=self.show_instructions,
            font=("Segoe UI", 9),
            bd=0,
            cursor="hand2"
        )
        self.info_btn.pack(side=tk.RIGHT)

        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate', length=150)

        self.root.configure(bg="#f0f0f0")
        self.theme_btn.config(bg="#f0f0f0", activebackground="#f0f0f0")
        self.info_btn.config(bg="#f0f0f0", activebackground="#f0f0f0")
        self.status_label.config(bg="#f0f0f0")

    def show_instructions(self):
        instructions = (
            "1. Obtain Bearer Token:\n"
            "   • Log in to your university portal in your browser.\n"
            "   • Right-click anywhere on the page and select 'Inspect' (or press F12).\n"
            "   • Navigate to the 'Network' tab.\n"
            "   • Refresh the page or click around, then look through the requests.\n"
            "   • Select one and check the 'Headers' or 'Payload' tab for an 'Authorization' (or 'Authorisation') header. Copy this token.\n\n"
            "2. Launch App: Start this application.\n"
            "3. Configure: Paste your Bearer token and select a timeframe.\n"
            "4. Fetch: Click 'Fetch Data' to preview your schedule.\n"
            "5. Download: Click 'Download .ics' to save the calendar file to your computer."
        )
        messagebox.showinfo("How to use the Extractor", instructions)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode

        if self.is_dark_mode:
            self.theme_btn.config(text="☀️")
            bg_color = "#2d2d2d"
            fg_color = "#ffffff"
            entry_bg = "#404040"
            tree_bg = "#333333"
        else:
            self.theme_btn.config(text="🌙")
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            entry_bg = "#ffffff"
            tree_bg = "#ffffff"

        self.root.configure(bg=bg_color)
        self.theme_btn.config(bg=bg_color, fg=fg_color, activebackground=bg_color, activeforeground=fg_color)
        self.info_btn.config(bg=bg_color, fg=fg_color, activebackground=bg_color, activeforeground=fg_color)
        self.status_label.config(bg=bg_color)

        self.style.configure(".", background=bg_color, foreground=fg_color)
        self.style.configure("TEntry", fieldbackground=entry_bg, foreground=fg_color)
        self.style.configure("TCombobox", fieldbackground=entry_bg, foreground=fg_color)
        self.style.configure("Treeview", background=tree_bg, foreground=fg_color, fieldbackground=tree_bg)
        self.style.map("Treeview", background=[("selected", "#0078D7")], foreground=[("selected", "#ffffff")])
        self.style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        self.style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)

    def toggle_pickers(self, event):
        if self.range_var.get() == "Custom Range":
            self.picker_frame.pack(side=tk.LEFT, fill=tk.X, pady=5, padx=10)
        else:
            self.picker_frame.pack_forget()

    def clear_preview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.current_results = []
        self.download_btn.config(state="disabled")
        self.status_label.config(text="Preview cleared.", fg="gray")

    def start_fetch_thread(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning("Error", "Please enter a token.")
            return

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

        self.clear_preview()
        self.fetch_btn.config(state="disabled")
        self.status_label.config(text="Fetching data from server...",
                                 fg="#0078D7" if not self.is_dark_mode else "#66b3ff")

        self.progress_bar.pack(side=tk.RIGHT, padx=10)
        self.progress_bar.start(10)

        threading.Thread(target=self.fetch_data_worker, args=(token, start_iso, end_iso), daemon=True).start()
        self.root.after(100, self.check_fetch_queue)

    def fetch_data_worker(self, token, start_iso, end_iso):
        headers = {"Authorization": f"Bearer {token}" if "Bearer" not in token else token, "Accept": "application/json"}
        params = {"$filter": f"End gt datetime'{start_iso}' and Start lt datetime'{end_iso}'"}

        try:
            res = requests.get(ENDPOINT, headers=headers, params=params)
            if res.status_code == 200:
                results = res.json().get("results", [])
                self.fetch_queue.put(("success", results))
            else:
                if res.status_code in (401, 403):
                    hint = "Action Required: Your token is missing, invalid, or expired."
                elif res.status_code == 404:
                    hint = "Routing Error: The schedule endpoint could not be found."
                elif res.status_code >= 500:
                    hint = "System Error: The university's server is currently down or struggling."
                else:
                    hint = f"Request Failed (Status Code: {res.status_code})"

                server_msg = ""
                try:
                    error_data = res.json()
                    if isinstance(error_data, dict):
                        extracted = error_data.get("message") or error_data.get("error_description") or error_data.get(
                            "error")
                        if isinstance(extracted, dict):
                            extracted = extracted.get("message", "Unknown API Error")

                        if extracted:
                            server_msg = str(extracted)
                        else:
                            bullets = [f"• {str(k).title()}: {v}" for k, v in error_data.items() if
                                       not isinstance(v, (dict, list))]
                            server_msg = "\n".join(bullets)
                except Exception:
                    raw_text = res.text.strip()
                    if "<html" in raw_text.lower() or "<!doctype" in raw_text.lower():
                        server_msg = "The server returned a web page instead of data. This usually means your session expired and you were redirected to a login screen."
                    else:
                        server_msg = raw_text[:150] + "..." if len(raw_text) > 150 else raw_text

                final_error_display = f"{hint}"
                if server_msg:
                    final_error_display += f"\n\nDetails:\n{server_msg}"

                self.fetch_queue.put(("api_error", final_error_display))

        except requests.exceptions.ConnectionError:
            self.fetch_queue.put(
                ("exception", "Network Error: Could not connect to the server. Please check your internet connection."))
        except Exception as e:
            error_str = str(e)
            if len(error_str) > 150:
                error_str = error_str[:150] + "..."
            self.fetch_queue.put(("exception", f"An unexpected error occurred:\n{error_str}"))

    def check_fetch_queue(self):
        try:
            status, data = self.fetch_queue.get_nowait()

            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.fetch_btn.config(state="normal")

            if status == "success":
                self.current_results = data
                if not self.current_results:
                    self.status_label.config(text="No events found for this timeframe.", fg="orange")
                    return

                for item in self.current_results:
                    subj = item.get("Subject", "N/A")
                    start = item.get("Start", "N/A")
                    loc = item.get("Location", "N/A")
                    self.tree.insert("", tk.END, values=(subj, start, loc))

                self.status_label.config(text=f"Successfully fetched {len(self.current_results)} events.", fg="green")
                self.download_btn.config(state="normal")

            else:
                self.status_label.config(text="Fetch failed.", fg="red")
                messagebox.showerror("Error", data)

        except queue.Empty:
            self.root.after(100, self.check_fetch_queue)

    def run_download(self):
        if not self.current_results:
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".ics", initialfile="uni_schedule.ics")
        if file_path:
            lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MyHudScraper//EN", "METHOD:PUBLISH"]
            for item in self.current_results:
                if not item.get('Start') or not item.get('End'):
                    continue

                try:
                    s_date, s_time = item['Start'].split('T')
                    e_date, e_time = item['End'].split('T')

                    s = f"{s_date.replace('-', '')}T{s_time.replace(':', '')[:6]}Z"
                    e = f"{e_date.replace('-', '')}T{e_time.replace(':', '')[:6]}Z"

                    event_uid = item.get('Id')
                    if not event_uid:
                        event_uid = str(uuid.uuid4())

                    event_lines = [
                        "BEGIN:VEVENT",
                        f"UID:{event_uid}",
                        f"DTSTART:{s}",
                        f"DTEND:{e}",
                        f"SUMMARY:{item.get('Subject', 'No Subject')}"
                    ]

                    loc = item.get('Location')
                    if loc:
                        event_lines.append(f"LOCATION:{loc}")

                    event_lines.extend([
                        "BEGIN:VALARM",
                        "TRIGGER:-PT15M",
                        "ACTION:DISPLAY",
                        "DESCRIPTION:Reminder",
                        "END:VALARM",
                        "END:VEVENT"
                    ])

                    lines.extend(event_lines)

                except Exception as parse_err:
                    print(f"Skipped an event due to parsing error: {parse_err}")
                    continue

            lines.append("END:VCALENDAR")

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                messagebox.showinfo("Success", "Schedule successfully exported as .ics file!")
                self.status_label.config(text=f"File saved to {file_path}", fg="green")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()