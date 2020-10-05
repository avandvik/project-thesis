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
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)

    def has_orders(self):
        return True if self.orders else False

    def is_closed(self, hour):
        return self.opening_hour <= hour <= self.closing_hour

    def get_standard_order_size(self):
        return self.standard_order_size

    def get_distance_to_installation(self, installation_index):
        return self.distances[installation_index]

    def get_orders(self):
        return self.orders