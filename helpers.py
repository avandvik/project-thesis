import data
import math


def disc_to_current_hour(disc_time):
    return math.floor(disc_time / data.TIME_UNITS_PER_HOUR)


def disc_to_exact_hours(disc_time):
    return disc_time / data.TIME_UNITS_PER_HOUR


def disc_to_daytime(disc_time):
    return hour_to_daytime(disc_to_current_hour(disc_time))


def disc_to_disc_daytime(disc_time):
    return disc_time % (24 * data.TIME_UNITS_PER_HOUR)


def hour_to_disc(hourly_time):
    return hourly_time * data.TIME_UNITS_PER_HOUR


def hour_to_daytime(hourly_time):
    return hourly_time % 24


def get_disc_time_interval(start_hour, end_hour):
    start_time_disc = hour_to_disc(start_hour)
    end_time_disc = hour_to_disc(end_hour)
    return [disc_time for disc_time in range(start_time_disc, end_time_disc)]


def get_time_in_each_weather_state(start_time, end_time):
    return [get_time_in_weather_state(start_time, end_time, ws) for ws in range(data.WORST_WEATHER_STATE+1)]


def get_time_in_weather_state(start_time, end_time, weather_state):
    curr_time = start_time
    time_spent_in_weather_state = 0
    while curr_time < end_time:
        if weather_state == data.WEATHER_FORECAST_DISC[curr_time]:
            time_spent_in_weather_state += 1
        curr_time += 1
    return disc_to_exact_hours(time_spent_in_weather_state)
