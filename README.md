# Bundesliga Market Value Scraper

A powerful tool for scraping and tracking Bundesliga club market values from [Transfermarkt.com](Transfermarkt.com) over time.

## Overview

This Python script extracts market valuation data for Bundesliga football clubs from the Transfermarkt website. It allows you to collect historical market value data at regular intervals (1st and 15th of each month) and saves the results to a CSV file for further analysis.

## Features

- Scrape current and historical market values for all Bundesliga clubs
- Collect data from specified date ranges (from past to future dates)
- Convert currency strings (€, m, k) to numeric values automatically
- Handle percentages correctly
- Append to existing CSV files to build historical datasets
- Configurable delay between requests to respect website's access policies
- Option to use local test files during development

## Requirements

- Python 3.6+
- Required Python packages:
  - requests
  - beautifulsoup4
  - csv (standard library)
  - re (standard library)
  - argparse (standard library)
  - datetime (standard library)
  - os (standard library)
  - time (standard library)

## Installation

1. Clone this repository or download the script:

```bash
git clone https://github.com/yourusername/bundesliga-market-value-scraper.git
cd bundesliga-market-value-scraper
```

2. Install the required dependencies:

```bash
pip install requests beautifulsoup4
```

## Usage

Basic usage with default options:

```bash
python transfer-markt-scraping.py
```

This will scrape data for dates between 2024-10-01 and 2025-10-01 (default) and save to `bundesliga_market_values.csv`.

### Command-line Options

The script supports several command-line arguments:

```bash
python transfer-markt-scraping.py --date-from 2023-01-01 --date-to 2023-12-31 --output-file bundesliga_data.csv --delay 10
```

| Option | Description | Default |
|--------|-------------|---------|
| `--date-from` | Start date (YYYY-MM-DD) | 2024-10-01 |
| `--date-to` | End date (YYYY-MM-DD) | 2025-10-01 |
| `--output-file` | Output CSV filename | bundesliga_market_values.csv |
| `--use-local-file` | Use local HTML file (paste.txt) for testing | False |
| `--delay` | Delay between requests in seconds | 5 |

## Output Format

The script generates a CSV file with the following columns:

- **Date**: The date for which the market value was recorded (YYYY-MM-DD)
- **Rank**: The club's ranking by market value
- **Club**: The club's name
- **Value**: Total market value of the club (in euros, as a number)
- Additional columns may appear depending on the data available from Transfermarkt

Sample output:

```
Date,Rank,Club,Value
2023-01-01,1,Bayern Munich,927000000
2023-01-01,2,Borussia Dortmund,572500000
...
```

## How It Works

1. The script generates a list of dates (1st and 15th of each month) within the specified range
2. For each date, it:
   - Constructs the URL for Transfermarkt with the specific date
   - Sends an HTTP request with appropriate headers to avoid blocking
   - Parses the HTML response to extract club names and market values
   - Converts currency strings to numbers
   - Adds the data to a CSV file with the date

## Data Handling

The script includes robust data handling features:

- **Currency Conversion**: Converts values like "€944.70m" to numeric values (944,700,000)
- **Percentage Handling**: Correctly parses percentage strings like "5.1%" to float values (5.1)
- **Date Validation**: Ensures dates are correctly formatted and adjusts to the 1st or 15th of the month

## Limitations and Ethics

- Please use this script responsibly and respect Transfermarkt's terms of service
- The default delay between requests is set to 5 seconds to avoid overloading the server
- The script may need updates if Transfermarkt changes their HTML structure
- This tool is intended for personal research and educational purposes only

## Error Handling

The script includes comprehensive error handling:
- Validates date formats
- Handles connection errors gracefully
- Reports parsing issues and continues execution
- Skips problematic rows rather than failing completely

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Transfermarkt. Use at your own risk and responsibility.
