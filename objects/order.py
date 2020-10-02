class Order:

    def __init__(self, identifier, transport_type, cargo_type, mandatory, size, deadline, departure_day, installation):
        """
        :param identifier: Unique identifier for the order.
        :param transport_type:
        :param cargo_type: Type of cargo (either deck or bulk).
        :param size: Size of the order (m2 for deck, m3 for bulk).
        :param mandatory: True if order is categorized as mandatory, False if optional.
        :param deadline: Deadline for the order.
        :param departure_day: WHY DOES AN ORDER HAVE A FIXED DEPARTURE DAY?
        :param installation: The installation that placed the order.
        """
        self.identifier = identifier
        self.transport_type = transport_type
        self.cargo_type = cargo_type
        self.mandatory = mandatory
        self.size = size
        self.deadline = deadline
        self.departure_day = departure_day
        self.installation = installation
