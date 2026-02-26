# ical-export-uni (MyHud Schedule Extractor)

A proof-of-concept desktop application built with Python and `tkinter`, aimed at extracting university schedules from the MyHud website (via MyDay API) and exporting them into `.ics` (iCalendar) format.

## What it does

This application provides a simple graphical user interface to:

1. Connect to the MyHud calendar API (`https://api.myday.cloud/legacy/api/aggregate/v2/calendaritem`).
2. Fetch university schedule events based on a specified timeframe (Current Month, Full Semester, or Custom Date Range).
3. Preview the fetched schedule data in a table (Subject, Date/Time, Location).
4. Export the schedule to an `.ics` file. This allows users to easily import their university timetable into external calendars like Google Calendar, Apple Calendar, or Microsoft Outlook.

## How to run

### Prerequisites

Ensure you have Python 3 installed. You will also need to install the required Python packages. We recommend using a virtual environment:

```bash
pip install -r requirements.txt
```

*(Note: `tkinter` is usually included with standard Python installations. If it is missing, you may need to install it via your OS package manager, e.g., `sudo apt-get install python3-tk` on Ubuntu/Debian, or `brew install python-tk` on macOS).*

### Execution

Run the script from your terminal:

```bash
python main.py
```

*(Use `python3` instead of `python` depending on your environment).*

### Usage

1. **Obtain Bearer Token:** You will need a valid Bearer token from the MyHud website. You can extract this from the Network tab in your browser's developer tools when logged in to your university portal.
2. **Launch App:** Start the application.
3. **Configure:** Enter your Bearer token and select a timeframe.
4. **Fetch:** Click **Fetch Data** to preview your schedule.
5. **Download:** Click **Download .ics** to save the `.ics` file to your computer.

## Future Improvements (Post-Hackathon)

Since this project was built rapidly as a hackathon proof-of-concept, there are several areas for future improvement:

- **Automated Authentication:** Currently, the user must manually extract and paste a Bearer token from the MyHud website. Integrating a proper login flow or an automated authentication method (like browser automation) to fetch the token would vastly improve the user experience.
- **Direct Calendar Integration:** Instead of just downloading a `.ics` file, implement direct API integrations (like Google Calendar API or Microsoft Graph API) to sync events seamlessly without a manual import step.
- **Pagination Support:** If the timeframe is extremely large and returns more results than the API limit per request, pagination cursor handling must be implemented.
- **Modern UI Framework:** Migrate from `tkinter` to a modern web app (e.g., React/Next.js) or a cross-platform desktop framework (e.g., Electron, Tauri, PyQt) for a richer, more polished UI.
- **Robust Error Handling & Retries:** Improve API error handling with automatic retry logic for network timeouts or rate limits, and provide more descriptive, user-friendly error messages in the GUI.
