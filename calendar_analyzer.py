import os
from datetime import datetime, timezone, timedelta
import re
from icalendar import Calendar
from dateutil import tz
from typing import Dict, List, Pattern, Tuple

class CalendarAnalyzer:
    def __init__(self, calendar_file: str):
        """Initialize analyzer with path to calendar file."""
        self.calendar_file = os.path.join(os.getcwd(), calendar_file)
        self.local_tz = tz.gettz('America/Los_Angeles')
        self._calendar = None

    @property
    def calendar(self) -> Calendar:
        """Lazy load the calendar file."""
        if self._calendar is None:
            self._calendar = self.load_calendar()
        return self._calendar

    def load_calendar(self) -> Calendar:
        """Load an iCalendar file and return a Calendar object."""
        with open(self.calendar_file, 'rb') as f:
            return Calendar.from_ical(f.read())

    def analyze_events(self,
                      start_time: datetime,
                      end_time: datetime,
                      patterns: Dict[str, Pattern]) -> Dict[str, List[Tuple[datetime, str, timedelta]]]:
        """
        Analyze calendar events between start_time and end_time, matching events against regex patterns.

        Args:
            start_time: Start of the analysis period
            end_time: End of the analysis period
            patterns: Dictionary of pattern name to compiled regex pattern

        Returns:
            Dictionary mapping pattern names to lists of (datetime, event_summary, duration) tuples
        """
        # Initialize events_data with empty lists for all patterns
        events_data = {pattern_name: [] for pattern_name in patterns}

        for component in self.calendar.walk():
            if component.name == "VEVENT":
                # Skip events without start time
                dtstart = component.get('dtstart')
                if not dtstart:
                    continue
                event_start = dtstart.dt

                # Handle events without end time by using start time + 1 hour
                dtend = component.get('dtend')
                if not dtend:
                    event_end = event_start + timedelta(hours=1)
                else:
                    event_end = dtend.dt

                summary = str(component.get('summary', ''))

                # Check if this is an all-day event (date instead of datetime)
                is_all_day = not isinstance(component.get('dtstart').dt, datetime)

                # Convert to datetime if date
                if isinstance(event_start, datetime):
                    event_start = event_start.replace(tzinfo=timezone.utc).astimezone(self.local_tz)
                else:
                    event_start = datetime.combine(event_start, datetime.min.time(), tzinfo=self.local_tz)

                if isinstance(event_end, datetime):
                    event_end = event_end.replace(tzinfo=timezone.utc).astimezone(self.local_tz)
                else:
                    event_end = datetime.combine(event_end, datetime.min.time(), tzinfo=self.local_tz)

                # Skip if event is outside analysis period
                if event_end < start_time or event_start > end_time:
                    continue

                # Set duration to zero for all-day events, otherwise calculate normally
                duration = timedelta(0) if is_all_day else (event_end - event_start)

                # Match against patterns
                for pattern_name, regex in patterns.items():
                    match = regex.search(summary)
                    if match:  # Only process if we found a match
                        events_data[pattern_name].append((event_start, summary, duration))

        return events_data

    def get_day_stats(self, events_data: Dict[str, List[Tuple[datetime, str, timedelta]]]) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Get distribution of events by day of week for each pattern.

        Returns:
            Dictionary mapping pattern names to day distribution dictionaries.
            Each day contains:
                - count: number of events
                - total_hours: total time spent
                - avg_hours: average time per event
        """
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        distribution = {
            pattern: {
                day: {'count': 0, 'total_hours': 0.0, 'avg_hours': 0.0}
                for day in days
            }
            for pattern in events_data
        }

        for pattern, events in events_data.items():
            for event_start, _, duration in events:
                day = days[event_start.weekday()]
                hours = duration.total_seconds() / 3600

                distribution[pattern][day]['count'] += 1
                distribution[pattern][day]['total_hours'] += hours

        # Calculate averages
        for pattern in distribution:
            for day in days:
                count = distribution[pattern][day]['count']
                if count > 0:
                    distribution[pattern][day]['avg_hours'] = (
                        distribution[pattern][day]['total_hours'] / count
                    )

        return distribution

    def get_time_spent(self, events_data: Dict[str, List[Tuple[datetime, str, timedelta]]]) -> Dict[str, timedelta]:
        """
        Calculate total time spent on each event type.

        Returns:
            Dictionary mapping pattern names to total duration
        """
        time_spent = {}

        for pattern, events in events_data.items():
            total_duration = sum((duration for _, _, duration in events), timedelta())
            time_spent[pattern] = total_duration

        return time_spent

    def get_weekly_stats(self, events_data: Dict[str, List[Tuple[datetime, str, timedelta]]]) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Calculate weekly statistics for each pattern.

        Returns:
            Dictionary mapping pattern names to week statistics.
            Each week contains:
                - total_hours: total time spent in the week
                - avg_hours: average hours per day in that week
        """
        weekly_stats = {}

        for pattern, events in events_data.items():
            weekly_stats[pattern] = {}

            for event_start, _, duration in events:
                # Get the Monday of the week for this event
                monday = event_start - timedelta(days=event_start.weekday())
                week_key = monday.strftime('%Y-%m-%d')

                if week_key not in weekly_stats[pattern]:
                    weekly_stats[pattern][week_key] = {
                        'total_hours': 0.0,
                        'avg_hours': 0.0
                    }

                hours = duration.total_seconds() / 3600
                weekly_stats[pattern][week_key]['total_hours'] += hours

            # Calculate average hours per day for each week
            for week in weekly_stats[pattern].values():
                week['avg_hours'] = week['total_hours'] / 7

        return weekly_stats

    def get_monthly_stats(self, events_data: Dict[str, List[Tuple[datetime, str, timedelta]]]) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Calculate monthly statistics for each pattern.

        Returns:
            Dictionary mapping pattern names to month statistics.
            Each month contains:
                - total_hours: total time spent in the month
                - avg_hours: average hours per week in that month
                - event_count: number of events in that month
        """
        monthly_stats = {}

        for pattern, events in events_data.items():
            monthly_stats[pattern] = {}

            for event_start, _, duration in events:
                # Get the first day of the month for this event
                month_key = event_start.strftime('%Y-%m')

                if month_key not in monthly_stats[pattern]:
                    monthly_stats[pattern][month_key] = {
                        'total_hours': 0.0,
                        'avg_hours': 0.0,
                        'event_count': 0
                    }

                hours = duration.total_seconds() / 3600
                monthly_stats[pattern][month_key]['total_hours'] += hours
                monthly_stats[pattern][month_key]['event_count'] += 1

            # Calculate average hours per week for each month
            for month_key, stats in monthly_stats[pattern].items():
                # Get number of days in this month
                year, month = map(int, month_key.split('-'))
                if month == 12:
                    next_month = datetime(year + 1, 1, 1)
                else:
                    next_month = datetime(year, month + 1, 1)
                days_in_month = (next_month - datetime(year, month, 1)).days
                
                # Calculate number of weeks in the month (can be fractional)
                weeks_in_month = days_in_month / 7.0
                
                # Calculate average hours per week
                stats['avg_hours'] = stats['total_hours'] / weeks_in_month

        return monthly_stats

if __name__ == '__main__':
    # Example usage with analytics
    analyzer = CalendarAnalyzer('calendar.ics')

    # Define analysis timeframe
    start_time = datetime(2024, 12, 11, 19, 22, 55,
                         tzinfo=tz.gettz('America/Los_Angeles'))
    end_time = datetime(2024, 12, 31, 23, 59, 59,
                       tzinfo=tz.gettz('America/Los_Angeles'))

    # Define patterns to match
    patterns = {
        'meetings': re.compile(r'meeting|sync|standup', re.IGNORECASE),
        'classes': re.compile(r'CSE \d+', re.IGNORECASE),
        'workout': re.compile(r'workout', re.IGNORECASE),
        'social': re.compile(r'lunch|coffee', re.IGNORECASE),
    }

    # Get event matches
    results = analyzer.analyze_events(start_time, end_time, patterns)

    # Get analytics
    day_dist = analyzer.get_day_stats(results)
    time_spent = analyzer.get_time_spent(results)
    weekly_stats = analyzer.get_weekly_stats(results)
    monthly_stats = analyzer.get_monthly_stats(results)

    # Print analytics
    print("\nEvent Distribution by Day:")
    for pattern, dist in day_dist.items():
        print(f"\n{pattern}:")
        for day, stats in dist.items():
            print(f"  {day}: {stats['count']} events, {stats['total_hours']:.1f} hours, {stats['avg_hours']:.1f} hours/event")

    print("\nTime Spent on Each Event Type:")
    for pattern, duration in time_spent.items():
        hours = duration.total_seconds() / 3600
        print(f"{pattern}: {hours:.1f} hours")

    print("\nWeekly Statistics:")
    for pattern, stats in weekly_stats.items():
        print(f"\n{pattern}:")
        for week, week_stats in stats.items():
            print(f"  Week of {week}: {week_stats['total_hours']:.1f} hours, {week_stats['avg_hours']:.1f} hours/day")

    print("\nMonthly Statistics:")
    for pattern, stats in monthly_stats.items():
        print(f"\n{pattern}:")
        for month, month_stats in stats.items():
            print(f"  Month of {month}: {month_stats['total_hours']:.1f} hours, {month_stats['avg_hours']:.1f} hours/day, {month_stats['event_count']} events")
