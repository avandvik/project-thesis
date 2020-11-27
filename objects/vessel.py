class Vessel:

    def __init__(self, index, name, return_time, capacity, is_spot_vessel):
        """
        :param index: Unique identifier for the vessel, also serving as index of vessel list in data.py (starts at 0).
        :param name: Shortened name of the vessel.
        :param return_time: The hour in the planning horizon (end of planning horizon) the vessel must be back.
        :param capacity: The capacity (in m2) on the vessel's deck.
        :param is_spot_vessel: True if the vessel is a spot vessel.
        """
        self.index = index
        self.name = name
        self.return_time = return_time
        self.capacity = capacity
        self._is_spot_vessel = is_spot_vessel

    def is_spot_vessel(self):
        return self._is_spot_vessel

    def get_hourly_return_time(self):
        return self.return_time

    def get_capacity(self):
        return self.capacity

    def get_index(self):
        return self.index

    def __str__(self):
        return self.name
