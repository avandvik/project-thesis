import gurobipy as gp
import data


def add_flow_conservation_constrs(model, x, from_nodes, to_nodes, specific_departure_times, specific_arrival_times, node_times):
    model.addConstrs((gp.quicksum(x[v, j, t2, i, t1]
                                  for j in from_nodes[v][i][t1]
                                  for t2 in specific_departure_times[v][j][i][t1])

                      - gp.quicksum(x[v, i, t1, j, t2]
                                    for j in to_nodes[v][i][t1]
                                    for t2 in specific_arrival_times[v][j][i][t1])

                      ==

                      0

                      for v in range(len(data.VESSELS))
                      for i in range(len(data.ALL_NODES[1:-1]))
                      for t1 in node_times[v][i])

                     , name=f'flow-conservation')


def add_start_and_end_flow_constrs(model, x, departure_times, specific_arrival_times):
    model.addConstrs((gp.quicksum(x[v, 0, t1, j, t2]
                                  for j in range(len(data.ALL_NODES[1:]))
                                  for t1 in departure_times[v][0][j]
                                  for t2 in specific_arrival_times[v][0][j][t1])

                      ==

                      1

                      for v in range(len(data.VESSELS))

                      )

                     , name='start-flow')

    model.addConstrs((gp.quicksum(x[v, i, t1, len(data.ALL_NODES)-1, t2]
                                  for i in range(len(data.ALL_NODES[:-1]))
                                  for t1 in departure_times[v][i][len(data.ALL_NODES)-1]
                                  for t2 in specific_arrival_times[v][i][len(data.ALL_NODES)-1][t1])

                      ==

                      1

                      for v in range(len(data.VESSELS))

                      )

                     , name='end-flow')


def add_visit_limit_constrs(model, x, u, departure_times, specific_arrival_times):
    model.addConstrs((gp.quicksum(x[v, i, t1, j, t2]
                                  for i in range(len(data.ALL_NODES)) if i != j  # TODO: Find out if i != j is needed
                                  for t1 in departure_times[v][i][j]
                                  for t2 in specific_arrival_times[v][j][i][t1])
                      <=

                      u[j]

                      for j in range(len(data.ALL_NODES[1:-1]))
                      for v in range(len(data.VESSELS)))

                     , name=f'visit-limit')

    model.addConstrs((u[i]

                      ==

                      1

                      for i in data.MANDATORY_NODE_INDICES)

                     , name=f'visit_all_mand')

    # TODO: Add constraints for init and final node


def add_initial_delivery_load_constrs(model, l_D, u):
    model.addConstrs((l_D[v, 0]

                      == gp.quicksum(data.ALL_NODES[i].get_order().get_size() * u[i]
                                     for i in data.DELIVERY_NODE_INDICES)

                      for v in range(len(data.VESSELS)))

                     , name=f'initial-delivery-load')


def add_load_capacity_constrs(model, l_D, l_P):
    model.addConstrs((l_D[v.get_index(), i] + l_P[v.get_index(), i]

                      <=

                      v.get_total_capacity()

                      for i in range(len(data.ALL_NODES))
                      for v in data.VESSELS)

                     , name=f'load-capacity-upper')

    model.addConstrs((l_D[v.get_index(), i] + l_P[v.get_index(), i]

                      >=

                      0

                      for i in range(len(data.ALL_NODES))
                      for v in data.VESSELS)

                     , name=f'load-capacity-lower')


def add_load_continuity_constrs_1(model, x, l, u, to_nodes, departure_times, specific_arrival_times):
    model.addConstrs((l[v, j]

                      >=

                      l[v, i]
                      - data.ALL_NODES[j].get_order().get_size() * u[j]
                      - data.VESSELS[v].get_total_capacity() * (1 - gp.quicksum(x[v, i, t1, j, t2]
                                                                                for t1 in departure_times[v][i][j]
                                                                                for t2 in
                                                                                specific_arrival_times[v][j][i][t1]))

                      for i in range(len(data.ALL_NODES))
                      for j in to_nodes
                      for v in range(len(data.VESSELS)))

                     , name=f'load-continuity-1')


def add_load_continuity_constrs_2(model, x, l, to_nodes, departure_times, specific_arrival_times):
    model.addConstrs((l[v, j]

                      >=

                      l[v, i]
                      - data.VESSELS[v].get_total_capacity() * (1 - gp.quicksum(x[v, i, t1, j, t2]
                                                                                for t1 in departure_times[v][i][j]
                                                                                for t2 in
                                                                                specific_arrival_times[v][j][i][t1]))

                      for i in range(len(data.ALL_NODES))
                      for j in to_nodes
                      for v in range(len(data.VESSELS))
                      )

                     , name=f'load-continuity-2')


def add_final_pickup_load_constrs(model, l_P, u):
    model.addConstrs((l_P[v, len(data.ALL_NODES)-1]

                      ==

                      gp.quicksum(data.ALL_NODES[i].get_size() * u[i]
                                  for i in data.PICKUP_NODE_INDICES)

                      for v in range(len(data.VESSELS))),

                     name=f'final-pickup-load')
