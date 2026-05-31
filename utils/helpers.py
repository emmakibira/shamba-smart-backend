from datetime import datetime, timedelta, timezone


def get_month_start_end():
    """Get start and end dates for current month"""
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get first day of next month
    if today.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)
    
    return month_start, month_end
