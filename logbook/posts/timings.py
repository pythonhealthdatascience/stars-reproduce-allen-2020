from datetime import datetime


def min_hour(time):
    '''
    Creates a string with time in minutes, or hours and minutes

    Parameters:
    -----------
    time: int
        Time in minutes

    Returns:
    --------
    string: str
        String stating the time in minutes, or hours and minutes
    '''
    return f'{int(time)}m, or {int(time)//60}h {int(time)%60}m'


def calculate_times(used_to_date, times):
    '''
    Calculates the time used today, total time used, and time remaining.

    Parameters:
    -----------
    used_to_date: int
        Total time used prior to that day in minutes
    times: list
        List of tuples with 24h times
        Example: [('11.01', '12.13'), ('14.45', '14.59')]
    '''
    FMT = '%H.%M'
    total_min = 0
    for t in times:
        # Convert to datetime object
        h0 = datetime.strptime(t[0], FMT)
        h1 = datetime.strptime(t[1], FMT)
        # Find difference in minutes and add to total
        total_min += (h1 - h0).total_seconds() / 60

    # Time in hours and minutes
    print(f'Time spent today: {min_hour(total_min)}')

    # Total time used
    total_used = total_min + used_to_date
    print(f'Total used to date: {min_hour(total_used)}')

    # Find time remaining
    max = 40*60
    remain_min = max - total_used
    print(f'Time remaining: {min_hour(remain_min)}')

    # Find proportion out of 40 hours
    print(f'Used {round((total_min+used_to_date)/max*100,1)}% of 40 hours max')
