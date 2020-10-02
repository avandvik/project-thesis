class Vessel:

    def __init__(self, identifier, name, return_day, deck_capacity, bulk_capacity, is_spot_vessel):
        """
        :param identifier: Unique identifier for the vessel (starting at 0).
        :param name: Shortened name of the vessel.
        :param return_day: The day in the planning period the vessel must be back at the depot.
        :param deck_capacity: The capacity (in m2) on the vessel's deck.
        :param bulk_capacity: The capacity (in m3) in the vessel's bulk tanks.
        :param is_spot_vessel: True if the vessel is a spot vessel.
        """
        self.identifier = identifier
        self.name = name
        self.return_day = return_day
        self.deck_capacity = deck_capacity
        self.bulk_capacity = bulk_capacity
        self.is_spot_vessel = is_spot_vessel
