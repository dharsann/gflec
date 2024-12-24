from datetime import datetime

def convert_date(nanoseconds):
    seconds = nanoseconds / 1e9
    date = datetime.utcfromtimestamp(seconds)
    date_filt = datetime.date(date)
    return date_filt