from lxml import etree
import pandas as pd
from pandas import ExcelWriter
import matplotlib.pyplot as plt
import cv2
import numpy as np


def get_uncaging_times_coordinates(mark_points_xml_filename):
    tree = etree.parse(mark_points_xml_filename)
    root = tree.getroot()
    delay = root[0][0].attrib['InitialDelay']
    interval = root[0][0].attrib['InterPointDelay']
    duration = root[0][0].attrib['Duration']
    uncaging_times = []
    uncaging_coordinates = []
    for point in root[0][0]:
        uncaging_coordinates.append((point.attrib['X'], point.attrib['Y']))

    for coordinate in range(len(uncaging_coordinates)):
        uncaging_times.append(float(delay) + (float(coordinate) * (float(interval) + float(duration))))

    return (pd.DataFrame({'uncaging_times (ms)': uncaging_times, 'uncaging_coordinates': uncaging_coordinates}))


def get_uncaging_responses(uncaging_times, voltage_recording_df_input, samples_to_save):
    sampling_interval = voltage_recording_df_input['Time(ms)'][1]
    uncaging_times_insamples = [time / sampling_interval for time in uncaging_times]

    uncaging_events_df_list = []

    for pulse in uncaging_times_insamples:
        if pulse - samples_to_save <= 0:
            uncaging_responses = (voltage_recording_df_input['Input 0'].values[0:int(pulse + samples_to_save)])
            uncaging_times_ = (voltage_recording_df_input['Time(ms)'].values[0:int(pulse + samples_to_save)])
        elif pulse - samples_to_save > 0:
            uncaging_responses = (
            voltage_recording_df_input['Input 0'].values[int(pulse - samples_to_save):int(pulse + samples_to_save)])
            uncaging_times_ = (
            voltage_recording_df_input['Time(ms)'].values[int(pulse - samples_to_save):int(pulse + samples_to_save)])
        uncaging_events_df_list.append(
            pd.DataFrame({'uncaging_responses': uncaging_responses, 'uncaging_times': uncaging_times_}))

    events = [i + 1 for i in range(len(uncaging_events_df_list))]

    df = pd.concat(uncaging_events_df_list, keys=events, names=['points'])

    return (df)


def return_grid(array_of_uncaging_points, grid_length, grid_width):
    grid_rows = 0
    uncaging_point = 0
    grid = []
    while grid_rows < grid_width and uncaging_point < len(array_of_uncaging_points):
        grid_row = []
        point_in_row = 0
        while point_in_row < grid_length:
            grid_row.append(array_of_uncaging_points[uncaging_point])
            point_in_row += 1
            uncaging_point += 1
        grid.append(grid_row)
        grid_rows += 1

    return (grid)


def read_and_adjust_recording_data(voltage_recording_xml, voltage_recording_df):
    tree = etree.parse(voltage_recording_xml)
    enabled_ch = tree.xpath('.//Enabled[text()="true"]')
    channel_params = {}
    v_recording = {'Time(ms)': voltage_recording_df['Time(ms)']}
    for ch in enabled_ch:
        channel_divisor = float(ch.getparent().xpath('Unit')[0].xpath('Divisor')[0].text)
        channel_gain = abs(float(ch.getparent().xpath('Unit')[0].xpath('Divisor')[0].text))
        v_recording[ch.getparent().xpath('Name')[0].text] = (voltage_recording_df[
            ch.getparent().xpath('Name')[0].text]) / channel_divisor
        channel_params[ch.getparent().xpath('Name')[0].text + '_Divisor'] = channel_divisor
        channel_params[ch.getparent().xpath('Name')[0].text + '_Gain'] = channel_gain

    voltage_recording_adjusted = pd.DataFrame(v_recording)

    return (voltage_recording_adjusted, channel_params)


def plot_response(point_num, uncaging_responses_df, uncaging_params_df):
    plt.plot(uncaging_responses.loc[point_num]['uncaging_times'],
             uncaging_responses.loc[point_num]['uncaging_responses'])
    plt.axvline(uncaging_params_df['uncaging_times (ms)'].values[point_num - 1], color='purple')
    plt.show()
    return ()


def save_to_excel(list_of_dfs, xls_path):
    writer = ExcelWriter(xls_path)
    for n, df in enumerate(list_of_dfs):
        df.to_excel(writer, 'sheet%s' % n)
    writer.save()
    return (True)