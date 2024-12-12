#!/usr/bin/env python3

import argparse
from datetime import datetime, timedelta
import re
from dateutil import parser, tz
from calendar_analyzer import CalendarAnalyzer
import termplotlib as tpl

def valid_date(s):
    """Convert string to datetime, used for argument parsing."""
    try:
        return parser.parse(s).replace(tzinfo=tz.gettz('America/Los_Angeles'))
    except ValueError:
        msg = f"Not a valid date: '{s}'"
        raise argparse.ArgumentTypeError(msg)

def plot_day_stats(distribution):
    """Create ASCII bar charts showing event distribution by day of week."""
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    patterns = list(distribution.keys())

    print("\nEvent Distribution by Day:")
    for pattern in patterns:
        counts = [distribution[pattern][day]['count'] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
        hours = [round(distribution[pattern][day]['total_hours'], 1) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]

        print(f"\n{pattern} - Event Counts:")
        fig = tpl.figure()
        fig.barh(counts, days)
        fig.show()

        print(f"\n{pattern} - Hours Spent:")
        fig = tpl.figure()
        fig.barh(hours, days)
        fig.show()

def plot_weekly_stats(weekly_stats):
    """Create ASCII bar charts showing weekly hours by category."""
    print("\nWeekly Hours by Category:")
    for pattern, weeks in weekly_stats.items():
        # Sort weeks by date
        weeks_sorted = sorted(weeks.items())
        week_labels = [week for week, _ in weeks_sorted]
        hours = [round(week_data['total_hours'], 1) for _, week_data in weeks_sorted]

        print(f"\n{pattern}:")
        fig = tpl.figure()
        fig.barh(hours, week_labels)
        fig.show()

def plot_monthly_stats(monthly_stats):
    """Create ASCII bar charts showing monthly hours by category."""
    print("\nMonthly Hours by Category:")
    for pattern, months in monthly_stats.items():
        # Sort months by date
        months_sorted = sorted(months.items())
        month_labels = [month for month, _ in months_sorted]
        hours = [round(month_data['total_hours'], 1) for _, month_data in months_sorted]

        print(f"\n{pattern}:")
        fig = tpl.figure()
        fig.barh(hours, month_labels)
        fig.show()

def main():
    parser = argparse.ArgumentParser(
        description='Analyze calendar events within a timeframe with optional regex filtering.'
    )

    # Required calendar file argument
    parser.add_argument(
        'calendar_file',
        help='Name of the .ics file in the /calendars directory'
    )

    # Date range arguments
    parser.add_argument(
        '--start',
        type=valid_date,
        help='Start date (e.g., "2024-01-01" or "30 days ago")'
    )
    parser.add_argument(
        '--end',
        type=valid_date,
        help='End date (e.g., "2024-12-31" or "today")'
    )

    # Event filtering
    parser.add_argument(
        '--pattern',
        help='Regex pattern to filter events (searches both summary and description)'
    )

    # Analysis options
    parser.add_argument(
        '--show-day-stats',
        action='store_true',
        help='Show event distribution by day of week'
    )
    parser.add_argument(
        '--show-monthly-stats',
        action='store_true',
        help='Show monthly statistics including total hours, average hours per day, and event counts'
    )
    parser.add_argument(
        '--show-weekly-stats',
        action='store_true',
        help='Show weekly statistics including total and average hours per week'
    )
    parser.add_argument(
        '--show-graphs',
        action='store_true',
        help='Show visualizations of the analyses'
    )

    args = parser.parse_args()

    # Set default dates if not provided - no time limit by default
    now = datetime.now(tz.gettz('America/Los_Angeles'))
    if args.end is None:
        args.end = now
    if args.start is None:
        args.start = datetime(1970, 1, 1, tzinfo=tz.gettz('America/Los_Angeles'))

    # Initialize analyzer with the specified calendar file
    analyzer = CalendarAnalyzer(args.calendar_file)

    # Create patterns dict based on input
    if args.pattern:
        pattern = re.compile(args.pattern, re.IGNORECASE)
        patterns = {'matched_events': pattern}
    else:
        # Default patterns if no specific pattern is provided
        patterns = {
            'meetings': re.compile(r'meeting|sync|standup', re.IGNORECASE),
            'classes': re.compile(r'CSE \d+', re.IGNORECASE),
            'workout': re.compile(r'workout', re.IGNORECASE),
            'social': re.compile(r'lunch|coffee', re.IGNORECASE),
        }

    try:
        # Analyze events
        results = analyzer.analyze_events(args.start, args.end, patterns)

        # Print basic results
        print(f"\nAnalyzing events from {args.start.strftime('%Y-%m-%d')} to {args.end.strftime('%Y-%m-%d')}")

        # Only show individual events if no analysis flags are set
        show_analyses = args.show_day_stats or args.show_monthly_stats or args.show_weekly_stats

        if not show_analyses:
            for pattern_name, events in results.items():
                print(f"\n{pattern_name.title()} ({len(events)} events):")
                for dt, summary, duration in events:
                    print(f"{dt.strftime('%Y-%m-%d %H:%M')} - {summary} ({duration.total_seconds()/3600:.1f}h)")

        # Always show time spent
        time_spent = analyzer.get_time_spent(results)
        print("\nTime Spent on Events:")
        for pattern_name, duration in time_spent.items():
            hours = duration.total_seconds() / 3600
            print(f"{pattern_name.title()}: {hours:.1f} hours")

        # Show additional analyses if requested
        if args.show_day_stats:
            distribution = analyzer.get_day_stats(results)
            print("\nEvent Distribution by Day:")
            for pattern_name, dist in distribution.items():
                print(f"\n{pattern_name.title()}:")
                for day, stats in dist.items():
                    count = stats['count']
                    total = stats['total_hours']
                    avg = stats['avg_hours']
                    print(f"  {day:9} - {count:2d} events, {total:5.1f} hours total ({avg:4.1f}h avg/event)")

        if args.show_monthly_stats:
            monthly_stats = analyzer.get_monthly_stats(results)
            print("\nMonthly Statistics:")
            for pattern_name, stats in monthly_stats.items():
                print(f"\n{pattern_name.title()}:")
                for month, month_stats in sorted(stats.items()):
                    print(f"  Month of {month}: {month_stats['total_hours']:.1f} total hours "
                          f"({month_stats['avg_hours']:.1f}h avg/day), {month_stats['event_count']} events")

        if args.show_weekly_stats:
            weekly_stats = analyzer.get_weekly_stats(results)
            print("\nWeekly Statistics:")
            for pattern_name, stats in weekly_stats.items():
                print(f"\n{pattern_name.title()}:")
                for week, week_stats in sorted(stats.items()):
                    print(f"  Week of {week}: {week_stats['total_hours']:.1f} total hours ({week_stats['avg_hours']:.1f}h avg/day)")

        if args.show_graphs:
            if args.show_day_stats:
                distribution = analyzer.get_day_stats(results)
                plot_day_stats(distribution)

            if args.show_monthly_stats:
                monthly_stats = analyzer.get_monthly_stats(results)
                plot_monthly_stats(monthly_stats)

            if args.show_weekly_stats:
                weekly_stats = analyzer.get_weekly_stats(results)
                plot_weekly_stats(weekly_stats)

    except FileNotFoundError:
        print(f"Error: Calendar file '{args.calendar_file}' not found in /calendars directory")
        return 1
    except Exception as e:
        print(f"Error analyzing calendar: {str(e)}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
