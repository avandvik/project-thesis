class Order:

    def __init__(self, index, transport_type, cargo_type, mandatory, size, deadline, departure_day, installation):
        """
        :param index: Unique identifier for the order also servicing as index in the list of orders.
        :param transport_type:
        :param cargo_type: Type of cargo (either deck or bulk).
        :param size: Size of the order (m2 for deck, m3 for bulk).
        :param mandatory: True if order is categorized as mandatory, False if optional.
        :param deadline: Deadline for the order.
        :param departure_day: WHY DOES AN ORDER HAVE A FIXED DEPARTURE DAY?
        :param installation: The installation that placed the order.
        """
        self.index = index
        self.transport_type = transport_type
        self.cargo_type = cargo_type
        self.mandatory = mandatory
        self.size = size
        self.deadline = deadline
        self.departure_day = departure_day
        self.installation = installation

    def get_size(self):
        return self.size
