import data
import arc_flow.preprocessing.helpers as hlp
from collections import defaultdict as dd


class ArcGeneratorX:

    def __init__(self):
        # arcs[vessel][start_node][start_time][end_node][end_time] -> True/False
        self.arcs = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(lambda: False)))))
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
        self.number_of_arcs = 0
        self.verbose = True

    def generate_arcs(self):
        visit_list = hlp.generate_visit_list()

        for vessel in data.VESSELS:
            start_node = data.ALL_NODES[0]
            for not_visited_node in visit_list:
                new_visit_list = visit_list.copy()
                new_visit_list.remove(not_visited_node)
                start_time = data.PREPARATION_END_TIME
                self.visit_nodes(start_node, not_visited_node, new_visit_list, start_time, vessel)

    def visit_nodes(self, start_node, end_node, visit_list, start_time, vessel):
        if hlp.is_illegal_arc(start_node, end_node):
            return
        if not visit_list:
            return

        inbound_et = self.inbound_arc_calc(start_node, end_node, start_time, vessel)

        if end_node.is_end_depot():
            return

        internal_nodes = hlp.get_internal_nodes(end_node)
        if len(internal_nodes) == 3:
            self.generate_outbound_arcs(internal_nodes[0], visit_list, inbound_et, vessel)
            internal_et = self.internal_arc_calc(internal_nodes[:2], inbound_et, vessel)
            self.generate_outbound_arcs(internal_nodes[1], visit_list, internal_et, vessel)
            internal_et = self.internal_arc_calc([internal_nodes[0], internal_nodes[2]], inbound_et, vessel)
            self.generate_outbound_arcs(internal_nodes[2], visit_list, internal_et, vessel)
            internal_et = self.internal_arc_calc(internal_nodes, inbound_et, vessel)
            self.generate_outbound_arcs(internal_nodes[2], visit_list, internal_et, vessel)
        elif len(internal_nodes) == 2:
            self.generate_outbound_arcs(internal_nodes[0], visit_list, inbound_et, vessel)
            internal_et = self.internal_arc_calc(internal_nodes, inbound_et, vessel)
            self.generate_outbound_arcs(internal_nodes[1], visit_list, internal_et, vessel)
        else:
            node = internal_nodes[0]
            self.generate_outbound_arcs(node, visit_list, inbound_et, vessel)

    def generate_outbound_arcs(self, start_node, visit_list, start_times, vessel):
        for start_time in start_times:
            if len(visit_list) == 1 and visit_list[0].is_end_depot():
                # print(f'\tCurrent node: {start_node} ({start_time}) | Next node: {visit_list[0]} | Visit list: {visit_list} | Start time: {start_time}')
                self.visit_nodes(start_node, visit_list[0], visit_list, start_time, vessel)
            else:
                for not_visited_node in visit_list:
                    new_visit_list = visit_list.copy()
                    new_visit_list.remove(not_visited_node)
                    # print(f'\tCurrent node: {start_node} ({start_time}) | Next node: {not_visited_node} | Visit list: {new_visit_list} | Start time: {start_time}')
                    self.visit_nodes(start_node, not_visited_node, new_visit_list, start_time, vessel)

    def inbound_arc_calc(self, start_node, end_node, start_time, vessel):
        distance = start_node.get_installation().get_distance_to_installation(end_node.get_installation())
        early_arrival, late_arrival = hlp.get_arrival_time_span(distance, start_time)
        service_duration = hlp.calculate_service_time(end_node)
        checkpoints, idling = hlp.get_checkpoints(early_arrival, late_arrival, service_duration, end_node, vessel)
        arc_costs, arc_end_times, arc_arr_times = hlp.calculate_arc_data(start_time, checkpoints, distance, vessel)
        if end_node.is_end_depot():
            self.add_end_depot_node_and_arc(start_node, end_node, arc_costs, start_time, arc_end_times, vessel,
                                            arc_arr_times)
        elif idling:
            self.add_best_idling_arc(start_node, end_node, arc_costs, start_time, arc_end_times, vessel, arc_arr_times)
        else:
            self.add_nodes_and_arcs(start_node, end_node, arc_costs, start_time, arc_end_times, vessel, arc_arr_times)

        return list(dict.fromkeys(arc_end_times))

    def internal_arc_calc(self, internal_nodes, start_times, vessel):
        end_times = []
        for start_time in start_times:
            service_durations = []
            for internal_node in internal_nodes[1:]:
                service_durations.append(hlp.calculate_service_time(internal_node))

            total_service_duration = sum(service_durations)
            end_node, end_time = internal_nodes[-1], start_time + total_service_duration
            end_times.append(end_time)

            checkpoints = []
            service_start_time = start_time
            for service_duration in service_durations:
                checkpoints.append((service_start_time, service_start_time, service_start_time + service_duration))
                service_start_time = service_start_time + service_duration

            if hlp.is_return_possible(end_node, end_time, vessel) \
                    and hlp.is_servicing_possible(start_time, total_service_duration, end_node):

                arc_costs, arc_end_times, arc_arr_times = hlp.calculate_arc_data(start_time, checkpoints, 0, vessel)

                if len(internal_nodes) == 3:
                    self.add_nodes_and_arcs(internal_nodes[0], internal_nodes[1], arc_costs, start_time,
                                            [arc_end_times[0]], vessel, arc_arr_times)
                    self.add_nodes_and_arcs(internal_nodes[1], internal_nodes[2], arc_costs, start_time,
                                            [arc_end_times[1]], vessel, arc_arr_times)
                else:
                    self.add_nodes_and_arcs(internal_nodes[0], internal_nodes[1], arc_costs, start_time, arc_end_times,
                                            vessel, arc_arr_times)

        return end_times

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
            print(f'Adding arc: {sn} ({ast}) -> {en} ({aet}) ({ac}) {speed}')

        self.number_of_arcs += 1
        self.arcs[v.get_index()][sn.get_index()][ast][en.get_index()][aet] = True
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

    def print_arcs(self):
        for start_node in data.ALL_NODES[:-1]:
            for end_node in data.ALL_NODES[1:]:
                for start_time in range(data.PREPARATION_END_TIME, data.PERIOD_DISC):
                    for end_time in range(data.PREPARATION_END_TIME, data.PERIOD_DISC):
                        if self.arcs[0][start_node.get_index()][start_time][end_node.get_index()][end_time]:
                            print(f'{start_node} ({start_time}) -> {end_node} ({end_time})')


ag = ArcGeneratorX()
ag.generate_arcs()
print(ag.number_of_arcs)
ag.print_arcs()
