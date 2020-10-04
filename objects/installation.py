class Installation:

    def __init__(self, identifier, name, opening_hour, closing_hour, standard_order_size, distances):
        """
        :param identifier: Unique identifier for the installation (starting at 0 for depot).
        :param name: Shortened name of the installation.
        :param opening_hour: Hour (0-24) that installation opens for service.
        :param closing_hour: Hour (0-24) that installation closes.
        :param standard_order_size: Standard order size of the installation. Will vary in different scenarios.
        :param distances: Distances to all other installations.
        """
        self.identifier = identifier
        self.name = name
        self.opening_hour = opening_hour
        self.closing_hour = closing_hour
        self.standard_order_size = standard_order_size
        self.distances = distances

    def is_closed(self, order):
        pass

    def get_standard_order_size(self):
        return self.standard_order_size
