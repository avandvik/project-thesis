import data
from arc_flow.preprocessing import helpers as hlp
from collections import defaultdict as dd


class ArcGenerator:

    def __init__(self, preparation_end_time, verbose):
        # nodes[vessel][node][time] -> True/False
        self.nodes = dd(lambda: dd(lambda: dd(lambda: False)))

        # arc_costs[vessel][start_node][start_time][end_node][end_time] -> arc_costs
        self.arc_costs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))

        # sep_arc_costs[vessel][start_node][start_time][end_node][end_time] -> (fuel_cost, charter_cost)
        self.sep_arc_costs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))

        # arc_arrival_times[vessel][start_node][start_time][end_node][end_time] -> arrival_time
        self.arc_arrival_times = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: 0)))))

        # node_time_points[vessel][node] -> time
        self.node_time_points = [[[] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # start_nodes[vessel][end_node][end_time] -> start_node
        self.start_nodes = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # end_nodes[vessel][start_node][start_time] -> end_node
        self.end_nodes = [[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # start_times[vessel][start_node][end_node] -> start_time
        self.start_times = [[[[] for _ in data.ALL_NODES] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # end_times[vessel][start_node][end_node] -> end_time
        self.end_times = [[[[] for _ in data.ALL_NODES] for _ in data.ALL_NODES] for _ in data.VESSELS]

        # specific_start_times[vessel][start_node][end_node][end_times] -> start_time
        self.specific_start_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES]
                                      for _ in data.ALL_NODES] for _ in data.VESSELS]

        # specific_end_times[vessel][start_node][end_node][start_time] -> end_time
        self.specific_end_times = [[[[[] for _ in data.TIME_POINTS_DISC] for _ in data.ALL_NODES]
                                    for _ in data.ALL_NODES] for _ in data.VESSELS]

        self.preparation_end_time = preparation_end_time
        self.verbose = verbose
        self.number_of_arcs = 0

    def generate_arcs(self):
        for vessel in data.VESSELS:
            self.nodes[vessel.get_index()][0][self.preparation_end_time] = True
            self.node_time_points[vessel.get_index()][0].append(self.preparation_end_time)
            for start_node in data.ALL_NODES[:-1]:
                for end_node in data.ALL_NODES[1:]:
                    if hlp.is_illegal_arc(start_node, end_node):
                        continue

                    discretized_return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR

                    for start_time in range(self.preparation_end_time, discretized_return_time):
                        if self.is_valid_start_node(vessel, start_node, start_time, end_node):
                            self.generate_arcs_from_node(vessel, start_node, start_time, end_node)
        if self.verbose:
            print(f'Arc generation done!\nTotal number of arcs: {self.number_of_arcs}\n'
                  f'Arcs per vessel: {int(self.number_of_arcs / len(data.VESSELS))}')

    def generate_arcs_from_node(self, vessel, start_node, start_time, end_node):
        distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
        early_arrival, late_arrival = hlp.get_arrival_time_span(distance, start_time)
        service_duration = hlp.calculate_service_time(end_node)

        # Checkpoints are in the form of (arrival time, idling end time/service start time, service end time)
        checkpoints, idling = hlp.get_checkpoints(early_arrival, late_arrival, service_duration, end_node)

        hlp.print_arc_info(start_node, end_node, distance, start_time, early_arrival,
                           late_arrival, service_duration, checkpoints, self.verbose)

        return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR - 1
        checkpoints = [ckp for ckp in checkpoints if ckp[-1] <= return_time]

        arc_costs, arc_end_times, arc_arr_times = hlp.calculate_arc_data(start_time, checkpoints, distance, vessel)

        if end_node.is_end_depot():
            self.add_end_depot_node_and_arc(start_node, end_node, arc_costs, start_time, arc_end_times, vessel,
                                            arc_arr_times)
        elif idling:
            self.add_best_idling_arc(start_node, end_node, arc_costs, start_time, arc_end_times, vessel, arc_arr_times)
        else:
            self.add_nodes_and_arcs(start_node, end_node, arc_costs, start_time, arc_end_times, vessel, arc_arr_times)

        if self.verbose:
            print()

    def is_valid_start_node(self, vessel, start_node, start_time, end_node):
        if start_time != self.preparation_end_time and start_node.is_start_depot():
            return False
        if not self.nodes[vessel.get_index()][start_node.get_index()][start_time]:
            return False

        for time in range(self.preparation_end_time, start_time):
            if start_node.get_index() in self.end_nodes[vessel.get_index()][end_node.get_index()][time]:
                return False

        return True

    def add_end_depot_node_and_arc(self, start_node, end_node, arc_costs, start_time, arc_end_times, vessel,
                                   arc_arr_times):
        return_time = vessel.get_hourly_return_time() * data.TIME_UNITS_PER_HOUR
        feasible_return_arcs = [(ac[-1], ac[:-1], aet, aat) for ac, aet, aat in
                                zip(arc_costs, arc_end_times, arc_arr_times) if aet <= return_time]

        if feasible_return_arcs:
            best_return_arc = min(feasible_return_arcs)
            arc_cost, sep_arc_cost, arc_end_time, arc_arr_time = best_return_arc
            self.update_sets(start_node, end_node, arc_cost, sep_arc_cost, start_time, arc_end_time, vessel,
                             arc_arr_time)

    def add_best_idling_arc(self, start_node, end_node, arc_costs, start_time, end_times, vessel, arc_arr_times):
        arcs = [(ac[-1], ac[:-1], aet, aat) for ac, aet, aat in zip(arc_costs, end_times, arc_arr_times)
                if hlp.is_return_possible(end_node, aet, vessel)]
        if arcs:
            best_arc = min(arcs)
            arc_cost, sep_arc_cost, arc_end_time, arc_arr_time = best_arc
            self.update_sets(start_node, end_node, arc_cost, sep_arc_cost, start_time, arc_end_time, vessel,
                             arc_arr_time)

    def add_nodes_and_arcs(self, start_node, end_node, arc_costs, start_time, end_times, vessel, arc_arr_times):
        for arc_cost, arc_end_time, arc_arr_time in zip(arc_costs, end_times, arc_arr_times):
            if hlp.is_return_possible(end_node, arc_end_time, vessel):
                self.update_sets(start_node, end_node, arc_cost[-1], arc_cost[:-1], start_time, arc_end_time, vessel,
                                 arc_arr_time)

    def update_sets(self, sn, en, ac, sac, ast, aet, v, aat):
        if self.verbose:
            distance = sn.get_installation().get_distance_to_installation(en.get_installation())
            if aat - ast > 0:
                speed = distance / hlp.disc_to_exact_hours(aat - ast)
            else:
                speed = 0
            print(f'\tAdding arc: {ast} -> {aet} ({ac}) {speed}')

        self.number_of_arcs += 1

        self.nodes[v.get_index()][en.get_index()][aet] = True
        self.arc_costs[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = ac
        self.sep_arc_costs[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = sac
        self.arc_arrival_times[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = aat

        if aet not in self.node_time_points[v.get_index()][en.get_index()]:
            self.node_time_points[v.get_index()][en.get_index()].append(aet)
        if sn.get_index() not in self.start_nodes[v.get_index()][en.get_index()][aet]:
            self.start_nodes[v.get_index()][en.get_index()][aet].append(sn.get_index())
        if en.get_index() not in self.end_nodes[v.get_index()][sn.get_index()][ast]:
            self.end_nodes[v.get_index()][sn.get_index()][ast].append(en.get_index())
        if ast not in self.start_times[v.get_index()][sn.get_index()][en.get_index()]:
            self.start_times[v.get_index()][sn.get_index()][en.get_index()].append(ast)
        if aet not in self.end_times[v.get_index()][sn.get_index()][en.get_index()]:
            self.end_times[v.get_index()][sn.get_index()][en.get_index()].append(aet)
        if ast not in self.specific_start_times[v.get_index()][sn.get_index()][en.get_index()][aet]:
            self.specific_start_times[v.get_index()][sn.get_index()][en.get_index()][aet].append(ast)
        if aet not in self.specific_end_times[v.get_index()][sn.get_index()][en.get_index()][ast]:
            self.specific_end_times[v.get_index()][sn.get_index()][en.get_index()][ast].append(aet)

    def get_nodes(self):
        return self.nodes

    def get_arc_costs(self):
        return self.arc_costs

    def get_sep_arc_costs(self):
        return self.sep_arc_costs

    def get_arc_arrival_times(self):
        return self.arc_arrival_times

    def get_node_time_points(self):
        return self.node_time_points

    def get_start_nodes(self):
        return self.start_nodes

    def get_end_nodes(self):
        return self.end_nodes

    def get_start_times(self):
        return self.start_times

    def get_end_times(self):
        return self.end_times

    def get_specific_start_times(self):
        return self.specific_start_times

    def get_specific_end_times(self):
        return self.specific_end_times


# ag = ArcGenerator(16 * data.TIME_UNITS_PER_HOUR - 1, True)
# ag.generate_arcs()
