# Functions to analyse light curves for GPS flash timing analysis
# Michael Camilleri
# April 2023

import pandas as pd
import numpy as np
from scipy import stats

from sklearn import linear_model

from pathlib import Path

from datetime import datetime as dt
from datetime import time
from datetime import timedelta

import os

# Astropy
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename
from astropy import units as u
from astropy.timeseries import TimeSeries
from astropy.time import Time, TimeDelta
from astropy.visualization import astropy_mpl_style

import matplotlib.pyplot as plt

plt.style.use(astropy_mpl_style)

# ADV utilities
import Adv2
from Adv2.Adv2File import Adv2reader
from Adv2 import AdvLibException

def read_tangra_csv(file):
    '''Read a TANGRA csv light curve file
    Returns as dictionary with the various components
    file_read_from: Local file read from
    filename_from_tangra: The filename from the TANGRA header
    details: The header details from TANGRA
    apertures_raw: The aperture information as-is from TANGRA
    apertures: Processes details of the apertures. Has 1-4 rows depending on how many aperatures were analysed
    light_curve: The light curve, data frame with times converted to datetime objects
    
    Note that the times do not use any date so any times going over UTC midnight might cause problems'''
   
   
    print('Reading TANGRA light curve from file  ',file)

    # Read the header
    header = pd.read_csv(file,nrows=2)
    header.columns=['Tangra']
    filename = header.Tangra[1]
    
    # Read the details 
    details = pd.read_csv(file,skiprows=6,nrows=1)
    details
    
    # Read acquisition delay from the measurement parameters table (row 7-8)
    acquisition_delay = None
    video_format = ''
    try:
        params_header = pd.read_csv(file, skiprows=6, nrows=1)
        params_data = pd.read_csv(file, skiprows=7, nrows=1)
        
        # Extract acquisition delay
        if 'Acquisition Delay (ms)' in params_header.columns:
            delay_col = params_header.columns.get_loc('Acquisition Delay (ms)')
            if delay_col < len(params_data.columns):
                delay_value = params_data.iloc[0, delay_col]
                if pd.notna(delay_value):
                    acquisition_delay = float(delay_value)
        
        # Extract video format
        # Column name might have leading space, so strip all column names
        stripped_cols = {col.strip(): col for col in params_header.columns}
        if 'Video File Format' in stripped_cols:
            original_col_name = stripped_cols['Video File Format']
            format_col = params_header.columns.get_loc(original_col_name)
            if format_col < len(params_data.columns):
                format_value = params_data.iloc[0, format_col]
                if pd.notna(format_value):
                    format_str = str(format_value).strip().upper()
                    # Map Tangra format codes to report format names
                    if format_str == 'ADV' or format_str == 'ADVS':
                        video_format = 'ADVS'
                    elif 'AAV' in format_str:
                        if 'NTSC' in format_str:
                            video_format = 'AAV-NTSC'
                        elif 'PAL' in format_str:
                            video_format = 'AAV-PAL'
                        else:
                            video_format = 'ADVS'
                    elif 'PAL' in format_str or 'CCIR' in format_str:
                        video_format = 'PAL/CCIR'
                    elif 'NTSC' in format_str or 'EIA' in format_str:
                        video_format = 'NTSC/EIA'
                    elif format_str in ['SER', 'AVI', 'MP4', 'FITS']:
                        video_format = format_str
                    else:
                        video_format = format_str
    except Exception as ex:
        print(f"Warning: Could not read acquisition delay or video format: {ex}")
    
    # Find where the light curve data starts
    
    try:
        ttext = pd.read_csv(file,nrows=100,sep='\t',skip_blank_lines =False,header = None)
        ttext[0]= ttext[0].str.replace('BinNo','FrameNo')
        lc_start = ttext[0].str[0:7].to_list().index('FrameNo'  )
    except:
      print("Failed to find FrameNo for start of light curve data")
      print(ttext[0].str[0:7][0:20])
    
    # Read aperture details
    apertures_raw = pd.read_csv(file,skiprows=8,nrows=lc_start - 9 - 3)
    apertures_raw.columns = apertures_raw.columns.str.replace(' ','')
    apertures = apertures_raw[['Object','StartingX','StartingY']]
    
    def readtime(x):
        if x is None or x == '':
            return None
        return(dt.strptime(x,'[%H:%M:%S.%f]'))

    light_curve = pd.read_csv(file,skiprows=lc_start,converters = {"Time (UT)":readtime}, skip_blank_lines=False)
    light_curve.columns = light_curve.columns.str.lower().str.replace('binned measurment','signal').str.replace(' ','_').str.replace('(','').str.replace(')','').str.replace('binno','frameno')
    light_curve.head(3)
    #light_curve.dropna(inplace=True)
    
#    print('File name from TANGRA ',filename)
    return {"file_read_from":file, "filename_from_tangra":filename,"details":details,"apertures_raw":apertures_raw,"apertures":apertures,"light_curve":light_curve,"acquisition_delay":acquisition_delay,"video_format":video_format}
    
    


def analyse_timestamps(tangra_object,percentiles=None):
    '''Analyse the timestamps from a TANGRA light curve CSV
    Checks timestamps for errors and variation
    Input: A TANGRA object as read by read_tangra_csv()
    percentile: percentiles of timestamp delays to calculate. e.g [1,99]
    Returns: a single row dataframe with the summary information'''
    lc = tangra_object['light_curve']

    # Check for repeated frames
    # Check the differences between rows - if no difference in the data in the row it may be a repeated frame
    repeated_frames = ((1-(lc.iloc[:,2:].diff()==0).astype(int)).sum(axis=1)==0)
    n_repeated_frames = len(repeated_frames[repeated_frames])
    blank_cells = (((lc.iloc[:,2:].isna()).astype(int)).sum(axis=1)>0)
    n_blank_cells = len(blank_cells[blank_cells])
    
    # Analyse time differences
    times_list = lc['time_ut'].to_list()
    timediffs = lc['time_ut'].diff(1).dt.microseconds/1000
       
    diff_stats = timediffs.agg(['min','max','median','mean','std'])
    diff_stats['first_frame_no'] = lc['frameno'].to_list()[0]
    diff_stats['last_frame_no'] = lc['frameno'].to_list()[-1]
    diff_stats['frame_count'] = lc['frameno'].to_list()[-1] - lc['frameno'].to_list()[0] +1
    diff_stats['no_rows_in_csv'] = len(lc['frameno'].to_list())
    diff_stats['no_rows_missing_signal'] = lc['signal_1'].isna().sum()
 
    diff_stats['exposure_from_row_count']=(times_list[-1] - times_list[0]).total_seconds()/(len(times_list) - 1)*1000
    diff_stats['exposure_from_frame_no']=(times_list[-1] - times_list[0]).total_seconds()/(diff_stats['frame_count'] - 1)*1000
    diff_stats['n_late_frames'] = len(timediffs[timediffs >(diff_stats['median']*1.9)])
    diff_stats['n_delayed_frames'] = len(timediffs[timediffs >(diff_stats['median']*1.1)])
    
    diff_stats['n_dropped_frames'] = np.round((times_list[-1] - (times_list[0]) + timedelta(seconds = diff_stats.no_rows_in_csv *diff_stats['median']/1000 )).total_seconds()/diff_stats['median'])
    
    diff_stats['n_repeated_frames'] =n_repeated_frames
    diff_stats['n_blank_cells'] =n_blank_cells
    
    diff_stats['file_read_from']=tangra_object['file_read_from']
    diff_stats['filename_from_tangra']=tangra_object['filename_from_tangra']
    diff_stats['start_time'] = times_list[0].strftime('%H:%M:%S.%f')[0:12]
    
    # Include video format from Tangra if available
    if 'video_format' in tangra_object:
        diff_stats['video_format'] = tangra_object['video_format']
    
    # Include acquisition delay from Tangra if available
    if 'acquisition_delay' in tangra_object and tangra_object['acquisition_delay'] is not None:
        diff_stats['acquisition_delay'] = tangra_object['acquisition_delay']
    
    # Determine exposure/integration type based on timing consistency
    if diff_stats['std'] < (diff_stats['median'] * 0.1):
        diff_stats['exposure_integration'] = 'Exposure'
    else:
        diff_stats['exposure_integration'] = 'Integration'
    
    diff_stats = pd.DataFrame(diff_stats).transpose().reset_index()
    cols =['file_read_from','filename_from_tangra','start_time','min', 'max', 'median', 'mean', 'std', 'first_frame_no',
       'last_frame_no', 'frame_count', 'no_rows_in_csv',
       'no_rows_missing_signal', 'exposure_from_row_count',
       'exposure_from_frame_no', 'n_late_frames', 'n_delayed_frames','n_dropped_frames','n_repeated_frames','n_blank_cells']
    diff_stats =diff_stats[cols] 

    if percentiles is not None:
        for i in percentiles:
            diff_stats['tdelta_percentile_'+str(i)] = np.percentile(timediffs[1:],i) - diff_stats['median'].squeeze()
    
    diff_stats =diff_stats.rename(columns={'min': 'tdelta_min', 'max': 'tdelta_max','median': 'tdelta_median','mean': 'tdelta_mean','std': 'tdelta_std'})
  
   
    return diff_stats
    
    
def analyse_gps_flash(tangra_object={},col='signal_1', exposure_ms=50,flash_ms=100,background = None, do_plots = False):
    '''Analyse a single column light curve for GPS flashes and calculate the time offset of the timestamps from GPS

    Input: A TANGRA object as read by read_tangra_csv()
    tangra_object: the tangra object to analyse
    col: name of the column with the data to analyse. Could have up to 8 columns in a TANGRA file
    exposure_ms: The nominal exposure time in ms
    flash_ms: The nominal flash duration in ms
    background: Optional. If specified, use as the average background. Otherwise calculated automatically, but may not always work
    
    Output: A processed light curve ready to calculated the delays using calculate_delays()
    '''
    
    lcv = tangra_object['light_curve']
    # Calculate the background if not given
    # Attempts to use the exposure time as a proportion of flash time and 1 PPS frequency 
    # to calculated the proportion of frames that are NOT flashes
    # WIll not always work well
    if background is None:
        background = lcv[col].median()
        background = np.percentile(lcv[col], 100.0 - (exposure_ms/flash_ms + 1.0)/(1000.0/flash_ms)*100.0)
    #print(background)
    # Flag which rows are background
    lcv['background_flag'] = (lcv[col] <= background).astype(float)
    avg_background = lcv[col][lcv['background_flag'] == 1].mean()

    # Create a column that just has the flashes, with average background removed
    lcv['signal_flash'] =(lcv[col] -avg_background)*(1.0-lcv['background_flag'])  
    
    # Label each flash peak with a sequence
    lcv['peaks'] = (lcv['signal_flash'] >0).astype(float)
    lcv['transitions'] = lcv['peaks'].diff().abs()
    lcv['peak_no'] = np.cumsum(lcv.transitions)*lcv['peaks']
    
    # Save the avg background in the file as will need it later
    lcv['avg_background'] = avg_background
    
    #if do_plots:
        
        #lcv.plot('time_ut',['signal_flash'])
        #lcv.plot('time_ut',['peaks'])
        #lcv.plot('time_ut',['transitions'])
        #lcv.plot('time_ut',['peak_no'])
    return lcv[['time_ut','frameno',col,'peak_no','signal_flash','avg_background']]


def calculate_delays(lcv,peak_no,exposure_ms,flash_ms,y=248,y_lines=496, verbose = False):
    '''Calculate the delay between the timestamps and the start of a single PPS flash event in a light curve
    Method:
    First measure the p
    '''
    # The data for this peak_no
    timediff = pd.DataFrame({'frameno':lcv.frameno+1,'timediff': [i.total_seconds()*1000 for i in lcv.time_ut.diff()]})
    timediff = timediff.fillna(exposure_ms)
    lcv = lcv.merge(timediff,on = 'frameno')
    if verbose:
        print()
        print(lcv.head())
        print(lcv.tail())
    data = lcv[lcv.peak_no == peak_no].copy()
    # Total flux during the signal, with background already removed
    total_flux = data.signal_flash.sum()
    # Flux in the first frame of the signal
    flux1 = data['signal_flash'].to_list()[0]
    
    # Fraction of total flux in first frame give the fraction of the flash_ms time that was in the first frame
    frac_flux_frame1 = flux1/total_flux
    pps_ms_in_frame1 = frac_flux_frame1*flash_ms
    # Scale by the actual ms timestamped for the frame , diff from previous frame timestamp
 #   pps_ms_in_frame1 = frac_flux_frame1*flash_ms*data.timediff.iloc[0]/exposure_ms
 #   if np.isnan(pps_ms_in_frame1):
 #       pps_ms_in_frame1 = frac_flux_frame1*flash_ms
        
    
    # Calculate the end time of the first frame
    # TANGRA uses mid times
    # But need to adjust for vertical y position
    # Top of frame subtract 1/2 exposure_ms
    # Middle of frame no adjustment
    # Bottom of frame add 1/2 exposure_ms
    #rolling_shutter_y_offset = (y/y_lines - 0.5)*exposure_ms
    #if y_lines <= 0 : rolling_shutter_y_offset = exposure_ms/2.0
    # Just add half exposure to get end frame
    rolling_shutter_y_offset = exposure_ms/2.0
    frame1_end = data.time_ut.to_list()[0] + timedelta(seconds = rolling_shutter_y_offset/1000.0)
    
    # The actual UT of the PPS flash. Assumes that the timestamps are accurate to <<1s
    pps_actual_seconds = np.round((frame1_end - dt(1900,1,1)).total_seconds())
    pps_actual_time = dt(1900,1,1) + timedelta(seconds = pps_actual_seconds)

    # The actual time of the end of the frame, which is pps_ms_in_frame1 after pps_actual_time
    frame1_end_actual = pps_actual_time + timedelta(seconds = pps_ms_in_frame1/1000.0)
    # Time offset is just the difference
    time_offset = (frame1_end - frame1_end_actual).total_seconds()*1000.0
    
    # Output number of frames so can choose if using the frame
    n_frames = len(data['frameno'].to_list())
       
    output = pd.DataFrame([peak_no,n_frames,y,y_lines,rolling_shutter_y_offset,total_flux,flux1,frac_flux_frame1,pps_ms_in_frame1,data.time_ut.to_list()[0],frame1_end,pps_actual_time,frame1_end_actual,time_offset,data.timediff.iloc[0]]).transpose()
    output.columns = ['peak_no','n_frames','y','y_lines','y_time_offset','total_flux','flux1','frac_flux_frame1','pps_ms_in_frame1','frame1_mid','frame1_end','pps_actual_time','frame1_end_actual','time_offset','frame1_timestamp_ms']
    return(output)
    


# Functions for automated processing of ADV and FITS files in bulk, with line delay measurements

def open_adv(file_path, file,verbose=False,plot=False):
    '''Open and ADV file and return the reader.
    file_path: File pat
    file: Name of the file
    verbose: If True print file information

    Returns: rdr ADV file reader object
  
    Note that you must close it later'''
  #  from pathlib import Path

  #  from Adv2.Adv2File import Adv2reader

    try:
        # Create a platform agnostic path to your .adv file (use forward slashes)
        file_to_open = str(Path(file_path + file))  # Python will make Windows version as needed

        # Create a 'reader' for the given file
        rdr = Adv2reader(file_to_open)

    except AdvLibException as adverr:
        print(repr(adverr))
        exit()

    except IOError as ioerr:
        print(repr(ioerr))
        exit()
    if verbose:
        print('Opening ADV reader for ',file_to_open)
        print(rdr.CountMainFrames, ' frames in file')

    if plot:
        # View image to check it is OK
# Not that the image will be inverted and reverse, that is OK
        err, image_data, frameInfo, status = read_adv_frame(rdr, frameNumber=0)
        if not err:
            image_data = np.log10(image_data+1)
            plt.figure();
            plt.imshow(image_data, cmap='gray');
            plt.colorbar();
    
    return rdr

def read_adv_frame(rdr, frameNumber):
    ''' Read a single frame from ADV file
    rdr: ADV rdr object already opened
    frameNumber: Number of the frame to read (0 indexed)'''
    err, image_data, frameInfo, status = rdr.getMainImageAndStatusData(frameNumber=1)
    return err, image_data, frameInfo, status

def read_row_flux(rdr,frameStart=0,frameEnd=None,agg_rows = 10, verbose=False, plot=False):
    ''' Read frames from an ADV file and process row fluxes ready for flash timing processing

    rdr: ADV reader object
    frameStart: first frame to read. Defaults to 0
    frameEnd: last frame to read. Defaults to last frame
    agg_rows: Number of rows to aggregate. Default of 10 groups ten rows together for faster processing
    verbose: If True print information
    plot: If True plot the rowmeans to see the sequence of flashes  '''

    # Read the image frames and calculate row average flux
    nframes = rdr.CountMainFrames
    if frameEnd is None:
        frameEnd = nframes -1

    if frameEnd > (nframes + 1):
        frameEnd = nframes -1

    err, image_data, frameInfo, status = rdr.getMainImageAndStatusData(frameNumber=frameStart)
    
    row_means = np.zeros([nframes,image_data.shape[0]])
    fnums = np.zeros(nframes)
    timestamps = np.zeros(nframes,Time)
    exps = np.zeros(1)
    if verbose: 
        print(nframes,' image frames')
        print('Reading from frames', frameStart , ' to ', frameEnd)
        print('Image size ',image_data.shape)

    for i,fnum in enumerate(range(frameStart,frameEnd+1)):
        if verbose and i% 100 == 0:
            print(i,end=",")
        err, image_data, frameInfo, status = rdr.getMainImageAndStatusData(frameNumber=fnum)
    
        # Trimmed mean to avoid saturation and the odd star
        row_means[i] = stats.trim_mean(image_data, proportiontocut = 0.05, axis=1)

        fnums[i] = fnum
        # TImestamp converted to mid frame based on shutter
        timestamps[i] = Time(frameInfo.DateString +'T'+frameInfo.StartOfExposureTimestampString.replace('[','').replace(']','')[:-3],format='isot',scale='utc') + TimeDelta(frameInfo.Shutter/2/86400,scale='ut1')
        # Convert to mid frame timesamp
        exps  = frameInfo.Exposure/1e9
    # Plot the time series of one of the rows to check it has GPS flashesand check if any major problems
    if plot:
        plt.plot(row_means.mean(axis=1));
        plt.title('Timeseries of frame row means showing GPS flashes');
    
    # Convert to an AstroPy TimeSeries
    # Each column is a single Y line from the sensor
    ts = TimeSeries(time=timestamps,data = {'0':row_means[:,0]})
    for i in (range(row_means[0].shape[0])):
        ts[f'{int(i)}'] = row_means[:,i]
    
    
    # Convert to Pandas for processing
    ts_df = ts.to_pandas()
    # Aggregate lines for faster processing
    # Aggregate every 10 lines
    # Note that uses simple rounding so top and bottom lines may not be correct
    ts_df2 = ts_df.transpose().copy()
    rownos = [round(int(i)/agg_rows)*agg_rows for i in ts_df.columns]
    ts_df2['frameno'] = rownos

    ts_df3 = ts_df2.groupby('frameno').mean()

    ts_df3 = ts_df3.transpose()
    ts_df3.reset_index(inplace=True)
    ts_df3['time'] = ts_df.index
    ts_df3.reset_index(inplace=True)

    
    return timestamps, fnums, exps, ts_df3


def analyse_line_flashes(ts,exposure=40,flash_ms = 100,verbose=True):
    ''' Analyse the gps flashes for a series of lines in an image sequence
    
    ts: A data frame of time series processed by read_row_flux from an image stream
    exposure: The frame exposure time in ms
    flash_ms: The duration of the GPS flash in ms
    verbose: If try print out progress indicator
    
    Returns: flash_object - a dictionary of dataframes with peaks extracted ready for processing of time delays.
    
    These are identified with the frame line'''
    
    # First process the light curves to find and tag the flashes
    flash_objects = {}
    for i,j in enumerate(ts.columns[2:]):
        if verbose:
            print(j,end=",")
            if i% 40 == 0:
                print()
        data = ts[['index','time',j]].copy()
        data.columns = ['frameno','time_ut',f'{j}']
        this_tangra_object = {'light_curve':data}
        obj_name = f'{j}'
        
        flash_objects[f'{j}' +":"+obj_name] = analyse_gps_flash(this_tangra_object,obj_name,exposure_ms = exposure,flash_ms=flash_ms)
    return flash_objects

def analyse_line_gps_flashes(flash_objects,exposure=40,flash_ms=100,lines = -1,verbose=False):
    '''  Analyse GPS flashes for a series of lines from frames
    flash_objects: flash objects output from analyse_line_flash
    exposure: The frame expousre in ms
    flash_ms: The duration of the GPS flash in ms
    lines: the total number of lines in each frame (-1 indicates global shutter). Not currently used
    
    Returns: Dataframe with the calculated GPS offsets for each flash and frame line'''

    # Analyse the gps flashtimes
    flash_data = pd.DataFrame()
    
    if verbose: print('Sensor Lines: ',lines)
    for ii,i in enumerate(flash_objects.keys()):
        # Split the keys
        file_key = i.split(":")[0]
        object_key = i.split(":")[1]
        object_no = int(object_key)
        if verbose:
            print(file_key,end=',')
            if ii%40 == 0:
                print()
    # Grab the prepared GPS flash data
        lc1 = flash_objects[i]
        peaks = lc1.peak_no.unique()
        peaks = peaks[peaks>0]
        peaks1 = list(peaks.astype('int'))
        #print(i, " with peaks" , peaks1,"with sensor lines", lines)
        for j in peaks1:
                dels= calculate_delays(lc1, j, exposure_ms = exposure, flash_ms = flash_ms,y=object_no, y_lines=lines)
                #dels= calculate_delays(lc1, j, exposure_ms = timestamps.iloc[ind].tdelta_median, flash_ms = 100,y=lines, y_lines=lines)
                dels['file_key'] = file_key
                dels['object_key'] = object_key
                dels['object_no'] = object_no
                dels['exposure_ms'] = exposure
                flash_data = pd.concat([flash_data,dels])
    return flash_data

def line_delay_regression(flash_data):
    ''' Fit a regression model to the gps flash line delays'''
    # Calculate the delays using linear regression
    x = np.array(flash_data.y)
    x = x.reshape(x.shape[0],1)
    #x=flash_data[['frame1_mid','y']]
    y = np.array(flash_data.time_offset)
    #model = linear_model.LinearRegression(fit_intercept=True).fit(x, y)
    model = linear_model.RANSACRegressor(residual_threshold = 10).fit(x, y)
    # points used for model, e.g. not outliers
    inlier_mask = model.inlier_mask_
    res = f'Offset of {round(model.estimator_.intercept_,1)} ms plus {round(model.estimator_.coef_[0],3)} ms per line'
    print(res)

    # Be careful with outliers
    ax = flash_data.plot('y','time_offset',kind='scatter', title=res)
    plt.plot(x, model.predict(x),color='black',linewidth=3);
    flash_data[~inlier_mask].plot('y','time_offset',kind='scatter', title=res,color='red',ax=ax);

    #flash_data.plot('y','time_offset',kind='scatter',xlim=[0,390],ylim=[0,30], title=res);
    #plt.plot(x, model.predict(x),color='black',linewidth=3);
    return res
 
def reduce_adv_light_curve(file,file_path,global_shutter=False, nlines =10, ignore_header_lines = 0, ignore_footer_lines = 0, verbose=False, invert= False):
    """Process ADV video to a light curve to analyse GPS flashes
    file: ADV file to process
    file_path: File path to file
    global_shutter: flag indicate a global shutter camera, so no interline delays.
    nlines: Number of sensor Y lines to average. -1 means do the whole frame
    ignore_header_lines: Number of rows at the head of the frame to ignore, for exmple if it has on screen timestamps
    ignore_footer_lines: Number of rows at the foot of the frame to ignore, for exmple if it has on screen timestamps
    verbose: If true print out more information
    invert: Invert the signal if the signal is OFF for start of PPS. If True invert and infer the max and min levels. If a number use that as the max level for substraction/inversion
    """

    # Open the ADV file for reading
    try:
        # Create a platform agnostic path to your .adv file (use forward slashes)
        file_to_open = str(Path(file_path + file))  # Python will make Windows version as needed

        # Create a 'reader' for the given file
        rdr = Adv2reader(file_to_open)

    except AdvLibException as adverr:
        print(repr(adverr))
        exit()

    except IOError as ioerr:
        print(repr(ioerr))
        exit()

    # Read the ADV file and calculate row average flux
    nframes = rdr.CountMainFrames
    # Read first frame so can set up 
    err, image_data, frameInfo, status = rdr.getMainImageAndStatusData(frameNumber=0)
    if verbose:
        print("Image Shape ",image_data.shape[0], " by ", image_data.shape[0])

    row_means = np.zeros([nframes,image_data.shape[0] - ignore_header_lines - ignore_footer_lines ])
    fnums = np.zeros(nframes)
    timestamps = np.zeros(nframes,Time)
    exps = np.zeros(1)
    print(nframes,' image frames')
    for i,fnum in enumerate(range(nframes)):
        if i% 100 == 0:
            print(i,end=",")
        err, image_data, frameInfo, status = rdr.getMainImageAndStatusData(frameNumber=fnum)

        # Remove header and footer
        if ignore_header_lines > 0 or ignore_footer_lines > 0:
            image_data = image_data[ignore_header_lines:(image_data.shape[0] - ignore_footer_lines)]

        # Trimmed mean to avoid saturation and the odd star
        row_means[i] = stats.trim_mean(image_data, proportiontocut = 0.05, axis=1)

        fnums[i] = fnum
        # TImestamp converted to mid frame based on shutter
        timestamps[i] = Time(frameInfo.DateString +'T'+frameInfo.StartOfExposureTimestampString.replace('[','').replace(']','')[:-3],format='isot',scale='utc') + TimeDelta(frameInfo.Shutter/2/86400,scale='ut1')
        # Convert to mid frame timesamp
        exps  = frameInfo.Exposure/1e9

    # Plot the time series of one of the rows to check it has GPS flashes and check if any major problems
    if verbose:
        plt.plot([i.to_datetime() for i in timestamps],row_means.mean(axis=1));

    # Convert to an AstroPy TimeSeries
    # Each column is a single Y line from the sensor
    ts = TimeSeries(time=timestamps,data = {'0':row_means[:,0]})
    for i in (range(row_means[0].shape[0])):
        ts[f'{int(i)}'] = row_means[:,i]

    # Convert to Pandas for processing
    ts_df =ts.to_pandas()
    # Aggregate lines for faster processing
    # Aggregate every nline lines
    # Note that uses simple rounding so top and bottom lines may not be correct
    ts_df2 = ts_df.transpose().copy()
    rownos = [round(int(i)/nlines) for i in ts_df.columns]
    ts_df2['frameno'] = rownos
    # Do entire frame if global shutter or nlines = -1
    if global_shutter or nlines == -1:
        ts_df2['frameno'] = -1
    ts_df3 = ts_df2.groupby('frameno').mean()

    ts_df3 = ts_df2.groupby('frameno').mean()

    ts_df3 = ts_df3.transpose()
    ts_df3.reset_index(inplace=True)
    ts_df3['time'] = ts_df.index
    ts_df3.reset_index(inplace=True)

    # Invert the signal if required
    if invert:
        if invert >1:
            ts_df3.loc[:,ts_df3.columns[2]:] =  invert - ts_df3.loc[:,ts_df3.columns[2]:]
        else:
            colmax = ts_df3.loc[:,ts_df3.columns[2]:].max().squeeze()
            ts_df3.loc[:,ts_df3.columns[2]:] =  colmax - ts_df3.loc[:,ts_df3.columns[2]:]


    # Analyse the gps flashes
    # First process the light curves to find and tag the flashes
    light_curves = {}
    flash_objects = {}
    for i,j in enumerate(ts_df3.columns[2:]):
        print(j,end=",")
        if i% 40 == 0:
            print()
        data = ts_df3[['index','time',j]].copy()
        data.columns = ['frameno','time_ut',f'{j}']
        this_tangra_object = {'light_curve':data,'exposure_ms':float(exps)*1000,'line':j}
        obj_name = f'{j}'
        light_curves[f'{file}' +":"+obj_name] = this_tangra_object
        #flash_objects[f'{file}' +":"+obj_name] = lc.analyse_gps_flash(this_tangra_object,obj_name,exposure_ms = float(exps)*1000,flash_ms=100)
    #rdr.close()
    return light_curves
