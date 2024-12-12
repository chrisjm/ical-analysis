#!/usr/bin/env python3

import argparse
from datetime import datetime, timedelta
import re
from dateutil import parser, tz
from calendar_analyzer import CalendarAnalyzer

def valid_date(s):
    """Convert string to datetime, used for argument parsing."""
    try:
        return parser.parse(s).replace(tzinfo=tz.gettz('America/Los_Angeles'))
    except ValueError:
        msg = f"Not a valid date: '{s}'"
        raise argparse.ArgumentTypeError(msg)

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
        help='Start date (e.g., "2024-01-01" or "30 days ago"). Defaults to 30 days ago.'
    )
    parser.add_argument(
        '--end',
        type=valid_date,
        help='End date (e.g., "2024-12-31" or "today"). Defaults to today.'
    )
    
    # Event filtering
    parser.add_argument(
        '--pattern',
        help='Regex pattern to filter events (searches both summary and description)'
    )
    
    # Analysis options
    parser.add_argument(
        '--show-distribution',
        action='store_true',
        help='Show event distribution by day of week'
    )
    parser.add_argument(
        '--show-time-spent',
        action='store_true',
        help='Show total time spent on matching events'
    )
    parser.add_argument(
        '--show-overlaps',
        action='store_true',
        help='Show overlapping events'
    )
    parser.add_argument(
        '--show-weekly-stats',
        action='store_true',
        help='Show weekly statistics including total and average hours per week'
    )
    
    args = parser.parse_args()
    
    # Set default dates if not provided
    now = datetime.now(tz.gettz('America/Los_Angeles'))
    if args.end is None:
        args.end = now
    if args.start is None:
        args.start = now - timedelta(days=30)
    
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
        show_analyses = args.show_distribution or args.show_time_spent or args.show_overlaps or args.show_weekly_stats
        if not show_analyses:
            for pattern_name, events in results.items():
                print(f"\n{pattern_name.title()} ({len(events)} events):")
                for dt, summary, duration in events:
                    print(f"{dt.strftime('%Y-%m-%d %H:%M')} - {summary} ({duration.total_seconds()/3600:.1f}h)")
        
        # Show additional analyses if requested
        if args.show_distribution:
            distribution = analyzer.get_day_distribution(results)
            print("\nEvent Distribution by Day:")
            for pattern_name, dist in distribution.items():
                print(f"\n{pattern_name.title()}:")
                for day, stats in dist.items():
                    count = stats['count']
                    total = stats['total_hours']
                    avg = stats['avg_hours']
                    print(f"  {day:9} - {count:2d} events, {total:5.1f} hours total ({avg:4.1f}h avg/event)")
        
        if args.show_time_spent:
            time_spent = analyzer.get_time_spent(results)
            print("\nTime Spent on Events:")
            for pattern_name, duration in time_spent.items():
                hours = duration.total_seconds() / 3600
                print(f"{pattern_name.title()}: {hours:.1f} hours")
        
        if args.show_overlaps:
            overlaps = analyzer.find_overlapping_events(results)
            if overlaps:
                print("\nOverlapping Events:")
                for event1, event2, time in overlaps:
                    print(f"{time.strftime('%Y-%m-%d %H:%M')} - '{event1}' overlaps with '{event2}'")
            else:
                print("\nNo overlapping events found.")

        if args.show_weekly_stats:
            weekly_stats = analyzer.get_weekly_stats(results)
            print("\nWeekly Statistics:")
            for pattern_name, stats in weekly_stats.items():
                print(f"\n{pattern_name.title()}:")
                for week, week_stats in sorted(stats.items()):
                    print(f"  Week of {week}: {week_stats['total_hours']:.1f} total hours ({week_stats['avg_hours']:.1f}h avg/day)")
    
    except FileNotFoundError:
        print(f"Error: Calendar file '{args.calendar_file}' not found in /calendars directory")
        return 1
    except Exception as e:
        print(f"Error analyzing calendar: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
