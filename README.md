# iCalendar Event Analyzer

A Python tool for analyzing iCalendar (.ics) files and aggregating events based on regex patterns within a specified timeframe. Features powerful command-line interface with data visualization capabilities.

## Features

- Read and parse iCalendar (.ics) files from a specified directory
- Match events using customizable regex patterns
- Filter events within a specific time range
- Support for timezone-aware datetime handling
- Aggregated results by pattern categories
- Visual analysis with ASCII charts showing:
  - Event distribution by day of week
  - Total time spent by category
  - Weekly hours over time
- Command-line interface for easy analysis
- Comprehensive test suite with pytest

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

- icalendar >= 5.0.0: iCalendar file parsing
- python-dateutil >= 2.8.2: Advanced date handling
- pytz >= 2023.3: Timezone support
- pytest >= 7.4.0: Testing framework
- termplotlib >= 0.3.5: Terminal-based plotting

## Usage

### As a Python Library

```python
from calendar_analyzer import CalendarAnalyzer
from datetime import datetime
from dateutil import tz
import re

# Initialize analyzer
analyzer = CalendarAnalyzer(calendar_dir="/path/to/calendar/files")

# Define timeframe
start_time = datetime(2024, 12, 1, tzinfo=tz.gettz('America/Los_Angeles'))
end_time = datetime(2024, 12, 31, tzinfo=tz.gettz('America/Los_Angeles'))

# Define patterns
patterns = {
    'meetings': re.compile(r'meeting|sync|standup', re.IGNORECASE),
    'social': re.compile(r'lunch|dinner|party', re.IGNORECASE),
}

# Analyze events
results = analyzer.analyze_events(start_time, end_time, patterns)

# Process results
for pattern_name, events in results.items():
    print(f"\n{pattern_name.title()} ({len(events)} events):")
    for dt, summary in events:
        print(f"{dt.strftime('%Y-%m-%d %H:%M')} - {summary}")
```

### Command Line Interface

The tool provides a powerful CLI for quick analysis:

```bash
python cli.py analyze \
    --calendar-dir /path/to/calendars \
    --start-date "2024-01-01" \
    --end-date "2024-12-31" \
    --patterns "meetings:meeting|sync|standup" "social:lunch|dinner|party" \
    --visualize
```

#### CLI Options:
- `--calendar-dir`: Directory containing .ics files
- `--start-date`: Analysis start date (timezone aware)
- `--end-date`: Analysis end date (timezone aware)
- `--patterns`: Pattern definitions in format "name:regex_pattern"
- `--visualize`: Generate ASCII visualizations
- `--output-format`: Choose output format (text/json)

## Testing

The project includes a comprehensive test suite using pytest. Tests cover:

- Calendar file loading and parsing
- Event analysis and pattern matching
- Time distribution calculations
- Visualization functions
- Edge cases (overlapping events, timezone handling)

Run tests with:
```bash
pytest test_calendar_analyzer.py -v
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
