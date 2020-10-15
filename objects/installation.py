class Installation:

    def __init__(self, index, name, opening_hour, closing_hour, distances):
        """
        :param index: Unique identifier for the installation (starting at 0 for depot).
        :param name: Shortened name of the installation.
        :param opening_hour: Hour (0-24) that installation opens for service.
        :param closing_hour: Hour (0-24) that installation closes.
        :param distances: Distances to all other installations.
        """
        self.index = index
        self.name = name
        self.opening_hour = opening_hour
        self.closing_hour = closing_hour
        self.distances = distances
        self.orders = []

    def add_order(self, order):
        self.orders.append(order)

    def has_orders(self):
        return True if self.orders else False

    def has_mandatory_order(self):
        for order in self.orders:
            if order.is_mandatory():
                return True
        return False

    def has_optional_delivery_order(self):
        for order in self.orders:
            if not order.is_mandatory() and order.is_delivery():
                return True
        return False

    def is_open(self, time_of_day):
        return self.opening_hour <= time_of_day <= self.closing_hour

    def get_opening_hours_as_list(self):
        return list(range(self.opening_hour, self.closing_hour + 1))

    def get_distance_to_installation(self, destination_installation):
        return self.distances[destination_installation.get_index()]

    def get_orders(self):
        return self.orders

    def get_mandatory_order(self):
        for order in self.orders:
            if order.is_mandatory():
                return order
        return None

    def get_optional_delivery_order(self):
        for order in self.orders:
            if not order.is_mandatory() and order.is_delivery():
                return order
        return None

    def get_index(self):
        return self.index

    def __repr__(self):
        return f'Installation {self.name} with {len(self.orders)} orders'

    def __str__(self):
        return f'Installation {self.name} with {len(self.orders)} orders'
