import requests
from bs4 import BeautifulSoup
import csv
import re
import argparse
from datetime import datetime, timedelta
import os
import time


def convert_currency_to_number(currency_str):
    """
    Convert currency strings like '€944.70m' to numeric values (944700000)
    """
    if not re.search(r'\d', currency_str):
        return 0

    if not currency_str or currency_str == '-':
        return 0

    # Check if the string contains any currency indicators
    if '€' not in currency_str and 'm' not in currency_str and 'k' not in currency_str:
        # If it's not a recognizable currency format, return 0
        try:
            # Try to convert directly to float in case it's just a plain number
            return int(float(currency_str))
        except ValueError:
            # If conversion fails, it's not a number at all
            print(f"Warning: Could not convert '{currency_str}' to a number. Using 0 instead.")
            return 0

    # Remove the euro symbol and any whitespace
    currency_str = currency_str.replace('€', '').strip()

    # Check for million (m) or thousand (k) denominations
    if 'm' in currency_str:
        # Convert millions to full number
        try:
            value = float(currency_str.replace('m', '')) * 1000000
        except ValueError:
            print(f"Warning: Could not convert '{currency_str}' to a number. Using 0 instead.")
            return 0
    elif 'k' in currency_str:
        # Convert thousands to full number
        try:
            value = float(currency_str.replace('k', '')) * 1000
        except ValueError:
            print(f"Warning: Could not convert '{currency_str}' to a number. Using 0 instead.")
            return 0
    else:
        # Just a plain number
        try:
            value = float(currency_str)
        except ValueError:
            print(f"Warning: Could not convert '{currency_str}' to a number. Using 0 instead.")
            return 0

    return int(value)


def parse_percentage(percentage_str):
    """
    Parse percentage strings like '5.1 %' to float values (5.1)
    """
    if not percentage_str or percentage_str == '-':
        return 0.0

    # Check if string contains % or resembles a percentage
    if '%' not in percentage_str and not re.search(r'-?\d+\.?\d*\s*%?', percentage_str):
        print(f"Warning: '{percentage_str}' doesn't look like a percentage. Using 0.0 instead.")
        return 0.0

    # Remove % symbol and convert to float
    try:
        # Extract just the number with regex to handle both positive and negative cases
        match = re.search(r'(-?\d+\.?\d*)', percentage_str)
        if match:
            return float(match.group(1))
    except Exception:
        print(f"Warning: Could not parse '{percentage_str}' as a percentage. Using 0.0 instead.")

    return 0.0


def generate_date_range(start_date, end_date):
    """
    Generate a list of dates in format yyyy-mm-dd (only 1st and 15th of each month)
    between start_date and end_date inclusive

    Args:
        start_date (str): Start date in format yyyy-mm-dd
        end_date (str): End date in format yyyy-mm-dd

    Returns:
        list: List of date strings in format yyyy-mm-dd
    """
    # Parse start and end dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Adjust start date to 1st or 15th
    if start.day < 15:
        # Set to 1st of current month
        start = start.replace(day=1)
    else:
        # Set to 15th of current month
        start = start.replace(day=15)

    dates = []
    current = start

    while current <= end:
        # Add current date to list
        dates.append(current.strftime("%Y-%m-%d"))

        # Move to next date (either 15th or 1st of next month)
        if current.day == 1:
            # Move to 15th of same month
            current = current.replace(day=15)
        else:
            # Move to 1st of next month
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)

    return dates


def scrape_bundesliga_market_values(date=None, use_local_file=False):
    """
    Scrape Bundesliga club market values from transfermarkt.com

    Args:
        date (str): Date in format yyyy-mm-dd, must be yyyy-mm-01 or yyyy-mm-15
        use_local_file (bool): Whether to use a local file for testing instead of web scraping

    Returns:
        dict: Dictionary with headers and data
    """
    # Validate date format if provided
    if date:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
            day = parsed_date.day
            if day not in [1, 15]:
                raise ValueError("Date must have day as either 01 or 15")
        except ValueError as e:
            print(f"Error with date format: {e}")
            print("Using current date instead")
            date = None

    # URL construction
    base_url = "https://www.transfermarkt.com/bundesliga/marktwerteverein/wettbewerb/L1"
    if date:
        url = f"{base_url}/stichtag/{date}"
    else:
        url = base_url

    # Headers to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Scraping data from: {url}")

        if use_local_file:
            # For debugging with local file
            with open('paste.txt', 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Actual web scraping
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise exception for bad status codes
            content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        # Find the main table
        table = soup.select_one('div.responsive-table table.items')
        if not table:
            print("Table not found. Check if the HTML structure has changed.")
            return None

        # Get header rows
        headers = []
        header_row = table.select_one('thead tr')
        if not header_row:
            print("Header row not found. Check if the HTML structure has changed.")
            return None

        for th in header_row.select('th'):
            # Skip hidden columns or use a placeholder for empty headers
            if th.get('class') and 'hide' in th.get('class'):
                continue
            header_text = th.get_text(strip=True)
            # If header has a link, extract just the text
            if not header_text:
                header_text = "Rank"  # Default for the # column
            elif "Club" in header_text:
                header_text = "Club"
            # Standardize value columns to just "Value" - handles all date formats
            elif re.search(r'Value \w+ \d+', header_text) or "value" in header_text.lower():
                header_text = "Value"
            headers.append(header_text)

        # Clean up headers (remove duplicate columns)
        # Now handle potential duplicates caused by standardizing column names
        final_headers = []
        value_count = 0

        for h in headers:
            if h == "Value":
                # For each "Value" column, create a unique name
                value_count += 1
                if value_count > 1:
                    final_headers.append(f"Value_{value_count}")
                else:
                    final_headers.append("Value")
            elif h not in final_headers:
                final_headers.append(h)

        headers = final_headers

        # Get team data
        teams_data = []
        for row in table.select('tbody tr'):
            if row.get('class') and ('thead' in row.get('class') or 'tfoot' in row.get('class')):
                continue  # Skip header and footer rows

            # Extract cells data
            cells_data = []
            for td in row.select('td'):
                if td.get('class') and 'no-border-rechts' in td.get('class') and 'zentriert' in td.get('class'):
                    continue  # Skip hidden cells

                # Extract text (removing newlines and extra spaces)
                cell_text = td.get_text(strip=True)
                cells_data.append(cell_text)

            # Skip rows with insufficient data
            if len(cells_data) < 2:
                continue

            # Process the row data
            row_data = {}

            # Map data to appropriate headers
            # Initialize with empty values in case columns are missing
            for header in headers:
                row_data[header] = ""

            # Map the extracted cells to headers - being careful with indexes
            for i, header in enumerate(headers):
                if i < len(cells_data):
                    if "Value" in header:
                        # Convert currency to number safely
                        row_data[header] = convert_currency_to_number(cells_data[i])
                    elif "%" in header and i < len(cells_data):
                        # Convert percentage to float safely
                        row_data[header] = parse_percentage(cells_data[i])
                    else:
                        row_data[header] = cells_data[i]

            # Only add rows with data
            if row_data and "Club" in row_data and row_data["Club"]:
                teams_data.append(row_data)

        return {"headers": headers, "data": teams_data}

    except Exception as e:
        print(f"Error scraping data: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_to_csv(data, filename="bundesliga_market_values.csv", date=None):
    """
    Save the extracted data to a CSV file with a date column
    """
    if not data or "headers" not in data or "data" not in data:
        print("No data to save")
        return False

    try:
        # Add date to headers if not present
        headers = ["Date"] + data["headers"]
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # Write headers only if file is new
            if not file_exists:
                writer.writeheader()
            
            # Add date to each row
            for row in data["data"]:
                row_with_date = {"Date": date} if date else {"Date": ""}
                row_with_date.update(row)
                writer.writerow(row_with_date)
                
        print(f"Data saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scrape Bundesliga market values')
    parser.add_argument('--date-from', type=str, default='2024-10-01',
                        help='Start date in format yyyy-mm-dd')
    parser.add_argument('--date-to', type=str, default='2025-10-01',
                        help='End date in format yyyy-mm-dd')
    parser.add_argument('--output-file', type=str, default='bundesliga_market_values.csv',
                        help='Output CSV file for all data')
    parser.add_argument('--use-local-file', action='store_true',
                        help='Use local file for testing instead of web scraping')
    parser.add_argument('--delay', type=int, default=5,
                        help='Delay between requests in seconds')

    args = parser.parse_args()

    # Generate dates to scrape
    dates = generate_date_range(args.date_from, args.date_to)

    print(f"Will scrape data for {len(dates)} dates between {args.date_from} and {args.date_to}")

    # Scrape data for each date
    for i, date in enumerate(dates):
        print(f"Processing date {i + 1}/{len(dates)}: {date}")

        # Scrape the data
        data = scrape_bundesliga_market_values(date, args.use_local_file)

        # Save to CSV
        if data:
            save_to_csv(data, args.output_file, date)
        else:
            print(f"No data scraped for date {date}.")

        # Add a delay between requests to avoid being blocked
        if i < len(dates) - 1 and not args.use_local_file:
            print(f"Waiting {args.delay} seconds before next request...")
            time.sleep(args.delay)


if __name__ == "__main__":
    main()