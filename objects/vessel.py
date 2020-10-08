class Vessel:

    def __init__(self, index, name, return_day, deck_capacity, bulk_capacity, is_spot_vessel):
        """
        :param index: Unique identifier for the vessel, also serving as index of vessel list in data.py (starts at 0).
        :param name: Shortened name of the vessel.
        :param return_day: The day in the planning period the vessel must be back at the depot.
        :param deck_capacity: The capacity (in m2) on the vessel's deck.
        :param bulk_capacity: The capacity (in m3) in the vessel's bulk tanks.
        :param is_spot_vessel: True if the vessel is a spot vessel.
        """
        self.index = index
        self.name = name
        self.return_day = return_day
        self.deck_capacity = deck_capacity
        self.bulk_capacity = bulk_capacity
        self.is_spot_vessel = is_spot_vessel

    def is_spot_vessel(self):
        return self.is_spot_vessel()

    def get_hourly_return_time(self):
        return self.return_day*24

    def get_index(self):
        return self.index

    def __str__(self):
        return self.name
