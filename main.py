import requests
import tkinter as tk
from tkinter import messagebox, filedialog

# --- CONFIG ---
ENDPOINT = "https://api.myday.cloud/legacy/api/aggregate/v2/calendaritem"

def fetch_data(token):
    if not token.startswith("Bearer "):
        token = f"Bearer {token}"

    # Target timeframe
    params = {
        "$filter": "End gt datetime'2026-02-01T00:00:00Z' and Start lt datetime'2026-03-01T00:00:00Z'"
    }
    headers = {"Authorization": token, "Accept": "application/json"}

    try:
        response = requests.get(ENDPOINT, headers=headers, params=params)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        return None


def create_ics_manual(results):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MyDayScraper//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    for item in results:
        start = item['Start'].replace("-", "").replace(":", "").split("+")[0] + "Z"
        end = item['End'].replace("-", "").replace(":", "").split("+")[0] + "Z"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{item['Id']}",
            f"DTSTAMP:{start}",
            f"DTSTART:{start}",
            f"DTEND:{end}",
            f"SUMMARY:{item.get('Subject', 'No Title')}",
            f"LOCATION:{item.get('Location', 'TBD')}",
            f"DESCRIPTION:Link: {item.get('ItemLink', 'N/A')}",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines)


def run_app():
    token = token_entry.get().strip()
    if not token:
        messagebox.showwarning("Missing Input", "Please paste your Bearer token first.")
        return

    # Update UI to show progress
    status_label.config(text="🚀 Fetching from MyDay...", fg="blue")
    root.update()

    # Fetch
    data = fetch_data(token)

    if data and "results" in data:
        results = data["results"]
        if not results:
            status_label.config(text="⚠️ No events found in this date range.", fg="orange")
            return

        # Generate content
        ics_content = create_ics_manual(results)

        # Auto-download / Save File Dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".ics",
            initialfile="university_schedule.ics",
            title="Download/Save ICS File",
            filetypes=[("iCalendar Files", "*.ics"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(ics_content)
                status_label.config(text=f"✅ Success! Saved {len(results)} events.", fg="green")
                messagebox.showinfo("Success", f"ICS successfully downloaded to:\n{file_path}")
            except Exception as e:
                status_label.config(text="❌ Error saving file.", fg="red")
                messagebox.showerror("File Error", f"Could not write to file:\n{e}")
        else:
            status_label.config(text="⚠️ Download cancelled.", fg="orange")
    else:
        status_label.config(text="❌ Failed to fetch data. Check token.", fg="red")
        messagebox.showerror("API Error", "Failed to fetch data. Your token may have expired or network is down.")


# --- GUI SETUP ---
root = tk.Tk()
root.title("MyDay Schedule Downloader")
root.geometry("420x220")
root.resizable(False, False)
root.eval('tk::PlaceWindow . center') # Centers the window

# Title
tk.Label(root, text="University ICS Extractor", font=("Helvetica", 14, "bold")).pack(pady=(15, 5))

# Token Input Frame
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Bearer Token:").pack(side=tk.LEFT, padx=5)
# show="*" masks the input like a password field
token_entry = tk.Entry(frame, width=30, show="*")
token_entry.pack(side=tk.LEFT, padx=5)

# Execute Button
btn = tk.Button(root, text="Fetch & Download .ics", command=run_app, bg="#4CAF50", fg="black", font=("Helvetica", 10, "bold"))
btn.pack(pady=10)

# Status Label
status_label = tk.Label(root, text="Ready.", fg="gray")
status_label.pack(pady=5)

# Start GUI Loop
if __name__ == "__main__":
    root.mainloop()