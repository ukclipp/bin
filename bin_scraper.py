# -*- coding: utf-8 -*-
# --- Shropshire Bin Collection Scraper (Generates ICS file) ---
# --- Save this entire code as a .py file (e.g., bin_scraper.py) ---
# --- Requires libraries: pip install requests beautifulsoup4 ics pytz ---

import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import sys # To print errors to stderr
import pytz # For timezone handling

# --- Configuration ---
# !!! UPDATED URL using the property ID you provided !!!
SCRAPER_URL = "https://bins.shropshire.gov.uk/property/100070039508#calendar"
# Output filename (will be saved in the same directory as the script)
OUTPUT_ICS_FILE = "shropshire_bin_collections.ics"
# Add a User-Agent header to mimic a browser and be polite
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# Expected date format in the 'title' attribute (e.g., "Thursday 8, May 2025").
# %A = Full weekday name, %d = Day of month (01-31), %B = Full month name, %Y = Year
DATE_FORMAT = "%A %d, %B %Y" # Note the comma after %d
TIMEZONE = 'Europe/London'

# --- Main Script Logic ---
def scrape_and_generate_ical():
    """Scrapes bin collection dates and generates an .ics file."""
    print(f"Attempting to fetch data from: {SCRAPER_URL}")
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(SCRAPER_URL, headers=headers, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print("Successfully fetched page content.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1) # Exit if page cannot be fetched

    soup = BeautifulSoup(response.text, 'html.parser')
    calendar = Calendar() # Use the ics library Calendar
    events_found = 0

    print("Parsing page content to find collection dates...")

    # --- Find the container elements for each day ---
    collection_blocks = soup.find_all('div', class_='calendar-table-cell')
    print(f"Found {len(collection_blocks)} potential calendar day cells.")

    if not collection_blocks:
         print("Error: Could not find any 'div' elements with class 'calendar-table-cell'.", file=sys.stderr)
         print("The website structure might have changed. Please re-inspect.", file=sys.stderr)
         sys.exit(1)

    # --- Loop through each found day cell ---
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date()

    for element in collection_blocks:
        element_classes = element.get('class', [])
        # Optional: Skip cells marked as 'past-date'
        if 'past-date' in element_classes:
             # print(f"  Skipping cell marked as past date: {element.get('title', 'No Title')}")
             continue # Skip to the next day cell

        try:
            # --- Get date string from the 'title' attribute of the div ---
            date_str_raw = element.get('title')
            if not date_str_raw:
                continue # Skip cells without title

            # --- Get collection type from the text of the li element inside ---
            li_element = element.find('li') # Find the first li inside the div
            if not li_element:
                continue # Skip cells without list item (likely not collection days)
            bin_type_raw = li_element.get_text(strip=True)

            # --- Clean up type name (optional, adjust if needed) ---
            bin_type = bin_type_raw.replace(' Collection', '').strip()

            # --- Parse the date string using the specified DATE_FORMAT ---
            parsed_date = None
            date_part_to_parse = date_str_raw
            if ' - ' in date_str_raw:
                 date_part_to_parse = date_str_raw.split(' - ')[0].strip()

            try:
                parsed_date = datetime.strptime(date_part_to_parse, DATE_FORMAT).date()
            except ValueError:
                 # print(f"  Warning: Could not parse date '{date_part_to_parse}' with format '{DATE_FORMAT}'. Skipping.")
                 continue

            # --- Create iCal event (only for future dates) ---
            if parsed_date >= today and bin_type:
                event = Event()
                event.name = f"{bin_type}" # Use the cleaned type
                event.begin = parsed_date # Assigning date obj makes it all-day
                event.make_all_day() # Explicitly set all-day flag

                calendar.events.add(event)
                events_found += 1
                print(f"  SUCCESS: Added event '{event.name}' on {event.begin}")


        except Exception as e:
            # Catch potential errors during processing of a single cell
            print(f"  Warning: An unexpected error occurred processing cell ({element.get('title', 'No Title')}): {e}. Skipping cell.")
            continue
    # --- End of loop ---

    # --- Output Results ---
    if events_found > 0:
        print(f"\nFound and processed {events_found} future collection dates.")
        # Write the iCal file
        try:
            # Ensure file is written with UTF-8 encoding for compatibility
            with open(OUTPUT_ICS_FILE, 'w', encoding='utf-8') as f:
                 # Use writelines with serialize_iter for potentially better handling of large files/unicode
                f.writelines(calendar.serialize_iter())

            print(f"Successfully created iCalendar file: {OUTPUT_ICS_FILE}")
        except IOError as e:
            print(f"Error writing iCal file '{OUTPUT_ICS_FILE}': {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred while writing the file: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print("\nNo valid future collection dates were successfully parsed from the calendar cells found.")
        print("This could be normal if there are no future dates listed yet, or the website structure changed slightly.")
        # Attempt to write an empty file anyway so the hosted URL doesn't break
        try:
            with open(OUTPUT_ICS_FILE, 'w', encoding='utf-8') as f:
                f.writelines(calendar.serialize_iter()) # Write empty calendar
            print(f"Created empty calendar file: {OUTPUT_ICS_FILE}")
        except IOError as e:
            print(f"Error writing empty iCal file '{OUTPUT_ICS_FILE}': {e}", file=sys.stderr)


# --- Run the Script ---
if __name__ == '__main__':
    # Check Python version (optional but good practice)
    if sys.version_info < (3, 6):
        print("Error: This script requires Python 3.6 or higher.", file=sys.stderr)
        sys.exit(1)

    # Install necessary libraries if missing (basic check)
    try:
        import requests
        from bs4 import BeautifulSoup
        from ics import Calendar
        import pytz
    except ImportError:
        print("Error: Required libraries (requests, beautifulsoup4, ics, pytz) not found.")
        print("Please install them using: pip install requests beautifulsoup4 ics pytz")
        sys.exit(1)

    print("--- Starting Shropshire Bin Calendar ICS Generation ---")
    scrape_and_generate_ical()
    print("\n--- Script finished. ---")