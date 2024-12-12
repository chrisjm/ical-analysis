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
        results = {name: [] for name in patterns}

        for component in self.calendar.walk('VEVENT'):
            event_start = component.get('dtstart').dt
            event_end = component.get('dtend').dt if component.get('dtend') else None

            # Skip all-day events (events where start is a date, not datetime)
            if not isinstance(event_start, datetime):
                continue

            # Convert timezone if needed
            if event_start.tzinfo is None:
                event_start = event_start.replace(tzinfo=self.local_tz)

            if event_end and not isinstance(event_end, datetime):
                event_end = datetime.combine(event_end,
                                          datetime.max.time(),
                                          tzinfo=self.local_tz)
            elif event_end and event_end.tzinfo is None:
                event_end = event_end.replace(tzinfo=self.local_tz)
            elif not event_end:
                event_end = event_start + timedelta(hours=1)

            if start_time <= event_start <= end_time:
                summary = str(component.get('summary', ''))
                description = str(component.get('description', ''))
                duration = event_end - event_start

                for pattern_name, pattern in patterns.items():
                    # Check both summary and description for matches
                    if pattern.search(summary) or pattern.search(description):
                        results[pattern_name].append((event_start, summary, duration))

        # Sort results by datetime
        for pattern_name in results:
            results[pattern_name].sort(key=lambda x: x[0])

        return results

    def get_day_distribution(self, events_data: Dict[str, List[Tuple[datetime, str, timedelta]]]) -> Dict[str, Dict[str, Dict[str, float]]]:
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

    def find_overlapping_events(self, events_data: Dict[str, List[Tuple[datetime, str, timedelta]]]) -> List[Tuple[str, str, datetime]]:
        """
        Find events that overlap in time.

        Returns:
            List of (event1_summary, event2_summary, overlap_time) tuples
        """
        all_events = []
        for pattern, events in events_data.items():
            for start, summary, duration in events:
                all_events.append((start, start + duration, summary))

        overlaps = []
        for i, (start1, end1, summary1) in enumerate(all_events):
            for start2, end2, summary2 in all_events[i+1:]:
                if start1 < end2 and start2 < end1:
                    overlap_time = min(end1, end2)
                    overlaps.append((summary1, summary2, overlap_time))

        return overlaps

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
    day_dist = analyzer.get_day_distribution(results)
    time_spent = analyzer.get_time_spent(results)
    overlaps = analyzer.find_overlapping_events(results)
    weekly_stats = analyzer.get_weekly_stats(results)

    # Print analytics
    print("\nEvent Distribution by Day:")
    for pattern, dist in day_dist.items():
        print(f"\n{pattern.title()}:")
        for day, stats in dist.items():
            print(f"  {day}: {stats['count']} events, {stats['total_hours']:.1f} hours, {stats['avg_hours']:.1f} hours/event")

    print("\nTime Spent on Each Event Type:")
    for pattern, duration in time_spent.items():
        hours = duration.total_seconds() / 3600
        print(f"{pattern.title()}: {hours:.1f} hours")

    print("\nOverlapping Events:")
    for event1, event2, time in overlaps:
        print(f"{event1} overlaps with {event2} at {time.strftime('%Y-%m-%d %H:%M')}")

    print("\nWeekly Statistics:")
    for pattern, stats in weekly_stats.items():
        print(f"\n{pattern.title()}:")
        for week, week_stats in stats.items():
            print(f"  Week of {week}: {week_stats['total_hours']:.1f} hours, {week_stats['avg_hours']:.1f} hours/day")