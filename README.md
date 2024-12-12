# iCalendar Event Analyzer

A Python tool for analyzing iCalendar (.ics) files and aggregating events based on regex patterns within a specified timeframe.

## Features

- Read iCalendar files from a specified directory
- Match events using customizable regex patterns
- Filter events within a specific time range
- Support for timezone-aware datetime handling
- Aggregated results by pattern categories

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

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

## Testing

Run tests using pytest:
```bash
pytest test_calendar_analyzer.py
```

## Requirements

- Python 3.7+
- icalendar>=5.0.0
- python-dateutil>=2.8.2
- pytz>=2023.3
- pytest>=7.4.0
