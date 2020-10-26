class Order:

    def __init__(self, index, transport_type, cargo_type, mandatory, size, deadline):
        """
        :param index: Unique identifier for the order also servicing as index in the list of orders.
        :param transport_type: Type of transport (delivery or pickup).
        :param cargo_type: Type of cargo (either deck or bulk).
        :param size: Size of the order (m2 for deck, m3 for bulk).
        :param mandatory: True if order is categorized as mandatory, False if optional.
        :param deadline: Deadline for the order.
        """
        self.index = index
        self.transport_type = transport_type
        self.cargo_type = cargo_type
        self.mandatory = mandatory
        self.size = size
        self.deadline = deadline

    def is_mandatory(self):
        return self.mandatory

    def is_optional(self):
        return not self.mandatory

    def is_delivery(self):
        return self.transport_type == 'delivery'

    def is_pickup(self):
        return self.transport_type == 'pickup'

    def is_mandatory_delivery(self):
        return self.mandatory and self.transport_type == 'delivery'

    def is_optional_delivery(self):
        return not self.mandatory and self.transport_type == 'delivery'

    def is_optional_pickup(self):
        return not self.mandatory and self.transport_type == 'pickup'

    def get_index(self):
        return self.index

    def get_size(self):
        return self.size

    def get_deadline(self):
        return self.deadline
