class Node:

    def __init__(self, index, is_order, order, installation, is_start_depot=False):
        self.index = index
        self._is_order = is_order
        self._is_depot = not is_order
        self._is_start_depot = is_start_depot
        self._is_end_depot = not is_start_depot and self._is_depot
        self.order = order if is_order else None
        self.installation = installation

    def is_order(self):
        return self._is_order

    def is_depot(self):
        return self._is_depot

    def is_start_depot(self):
        return self._is_depot and self._is_start_depot

    def is_end_depot(self):
        return self._is_depot and self._is_end_depot

    def get_order(self):  # TODO: Raise a modified error if the node is depot
        return self.order

    def get_installation(self):
        return self.installation

    def get_index(self):
        return self.index

    def generate_representation(self):
        if self.is_start_depot():
            return 'START_DEP'
        elif self.is_end_depot():
            return 'END_DEP'
        else:
            if self.order.is_mandatory_delivery():
                out_str = 'MD'
            elif self.order.is_optional_delivery():
                out_str = 'OD'
            elif self.order.is_optional_pickup():
                out_str = 'OP'
            else:
                out_str = 'UNKNOWN_NODE'
            return f'{out_str}_I{self.installation.get_index()}'

    def __str__(self):
        return self.generate_representation()

    def __repr__(self):
        return self.generate_representation()
