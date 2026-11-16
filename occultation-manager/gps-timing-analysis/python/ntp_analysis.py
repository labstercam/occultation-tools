# Functions for analyzing NTP timing data
# Read NTP log files and extract timing information

import pandas as pd

import matplotlib.pyplot as plt

from datetime import datetime, timedelta


## Functions to read NTP log files


def read_ntp_peerstats(file_path, file):
    data = pd.read_csv(file_path +file,delimiter = ' ',header=None)
    data.columns = ['MJD','sec_frac','address','status','Offset (ms)','delay','dispersion','jitter']
# Convert from Modified Julian Date
    data['Date'] = [datetime.strptime('1958-11-17','%Y-%m-%d') + timedelta(days=i) for i in data['MJD']]
    data['Time'] = [timedelta(seconds =float(i)) for i in data['sec_frac'] ]
    data['Time'] = data['Date'] + data['Time']
    data['Time Rounded'] = [timedelta(minutes =round(i/60)) for i in data['sec_frac'] ]
    data['Time Rounded'] = data['Date'] + data['Time Rounded']
    data
    data['Offset (ms)'] = data['Offset (ms)']*1000 
    data['delay'] = data['delay']*1000 
    data['dispersion'] = data['dispersion']*1000 
    data['jitter'] = data['jitter']*1000 
    data = data[['Date','Time','address','Offset (ms)','delay','dispersion','jitter','Time Rounded']]
    data['Source file'] = file_path +'/'+file
    return data


def mjd_to_date(mjd, seconds):
    """Convert Modified Julian Date and seconds past midnight to datetime."""
    jd = mjd + 2400000.5
    date = datetime(1858, 11, 17)  + timedelta(days=jd - 2400000.5)
    return date + timedelta(seconds=seconds)

def process_loopstats(file_path):
    """Process NTP loopstats logfile and return DataFrame with converted timestamps."""
    columns = ['MJD', 'Seconds', 'Offset', 'Frequency', 'Jitter', 'Stability', 'Interval']
    df = pd.read_csv(file_path, sep='\\s+', names=columns)

    # Convert MJD and Seconds to datetime
    df['Timestamp'] = df.apply(lambda row: mjd_to_date(row['MJD'], row['Seconds']), axis=1)

    # Drop MJD and Seconds columns
    df.drop(['MJD', 'Seconds'], axis=1, inplace=True)
    return df

def visualize_performance(df,metric='Offset',day=None, **kwargs):
    """Visualize time performance metrics (Offset and Frequency) over time."""
    if day is None:
        day = datetime.combine(datetime.today().date(), datetime.min.time())
    if type(day) != list:
        day = [day,day+timedelta(days=1)]

    plt.figure(figsize=(12, 6))
    ax = plt.plot(df['Timestamp'], df[metric], label=metric)
    
    plt.xlim(day)

    if 'ylim' in kwargs:
        plt.ylim(kwargs.pop('ylim'))
    
    plt.title(f'{metric} Over Time')
    plt.xlabel('Timestamp')
    plt.ylabel(metric)
    plt.legend()
    plt.grid(True)
    plt.show()

def generate_regular_timeseries(df, metric, freq='H', plot=False):

    """Generate regular time series from irregular data and plot it."""
    df.set_index('Timestamp', inplace=True)
#    regular_ts = df[metric].resample(freq).mean()
    regular_ts = pd.DataFrame([df[metric].resample(freq).min(),df[metric].resample(freq).max()]).mean(axis=0).ffill(limit=10).bfill(limit=10)
    if plot:
        plt.figure(figsize=(12, 6))
        plt.plot(regular_ts.index, regular_ts.values, label=f'Regular {metric} Time Series')
        plt.title(f'Regular {metric} Time Series')
        plt.xlabel('Timestamp')
        plt.ylabel(metric)
        plt.legend()
        plt.grid(True)
        plt.show()
    return(regular_ts)
