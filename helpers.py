import data
import math


def disc_to_hourly_time(disc_time):
    return math.floor(disc_time / data.TIME_UNITS_PER_HOUR)


def convert_hourly_time_to_discretized_time(hourly_time):
    return hourly_time * data.TIME_UNITS_PER_HOUR


def convert_hourly_time_to_time_of_day(hourly_time):
    return hourly_time % 24


def convert_discretized_time_to_time_of_day(disc_time):
    return disc_to_hourly_time(disc_time) % 24


def get_time_in_each_weather_state(start_time, end_time):
    return [get_time_in_weather_state(start_time, end_time, ws) for ws in range(data.WORST_WEATHER_STATE+1)]


def get_time_in_weather_state(start_time, end_time, weather_state):
    curr_time = start_time
    time_spent_in_weather_state = 0
    while curr_time < end_time:
        if weather_state == data.WEATHER_FORECAST_DISC[curr_time]:
            time_spent_in_weather_state += 1
        curr_time += 1
    return time_spent_in_weather_state
