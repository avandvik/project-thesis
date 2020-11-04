import gurobipy as gp
import data


def add_flow_conservation_constrs(model, x, from_nodes, to_nodes, specific_departure_times, specific_arrival_times,
                                  node_times):
    model.addConstrs((gp.quicksum(x[v, j, t2, i, t1]
                                  for j in from_nodes[v][i][t1]
                                  for t2 in specific_departure_times[v][j][i][t1])

                      - gp.quicksum(x[v, i, t1, j, t2]
                                    for j in to_nodes[v][i][t1]
                                    for t2 in specific_arrival_times[v][i][j][t1])

                      ==

                      0

                      for v in range(len(data.VESSELS))
                      for i in data.ALL_NODE_INDICES[1:-1]
                      for t1 in node_times[v][i])

                     , name=f'flow-conservation')


def add_start_and_end_flow_constrs(model, x, departure_times, specific_arrival_times):
    model.addConstrs((gp.quicksum(x[v, 0, t1, j, t2]
                                  for j in data.ALL_NODE_INDICES[1:]
                                  for t1 in departure_times[v][0][j]
                                  for t2 in specific_arrival_times[v][0][j][t1])

                      ==

                      1

                      for v in range(len(data.VESSELS)))

                     , name='start-flow')

    model.addConstrs((gp.quicksum(x[v, i, t1, data.ALL_NODE_INDICES[-1], t2]
                                  for i in data.ALL_NODE_INDICES[:-1]
                                  for t1 in departure_times[v][i][data.ALL_NODE_INDICES[-1]]
                                  for t2 in specific_arrival_times[v][i][data.ALL_NODE_INDICES[-1]][t1])

                      ==

                      1

                      for v in range(len(data.VESSELS)))

                     , name='end-flow')


def add_visit_limit_constrs(model, x, u, departure_times, specific_arrival_times):
    model.addConstrs((gp.quicksum(x[v, i, t1, j, t2]
                                  for i in data.ALL_NODE_INDICES[:-1] if i != j  # TODO: Find out if i != j is needed
                                  for t1 in departure_times[v][i][j]
                                  for t2 in specific_arrival_times[v][i][j][t1])

                      ==

                      u[v, j]

                      for j in data.ALL_NODE_INDICES[1:-1]
                      for v in range(len(data.VESSELS)))

                     , name=f'visit-limit')

    model.addConstrs((gp.quicksum(u[v, i]
                                  for v in range(len(data.VESSELS)))

                      ==

                      1

                      for i in data.MANDATORY_NODE_INDICES)

                     , name=f'visit-all-mand')

    # model.addConstr((u[0, 0] == 1), name='init-u')
    # model.addConstr((u[1, 0] == 1), name='init-u-2')


def add_initial_delivery_load_constrs(model, l_D, u):
    model.addConstrs((l_D[v, 0]

                      ==

                      gp.quicksum(data.ALL_NODES[i].get_order().get_size() * u[v, i]
                                  for i in data.DELIVERY_NODE_INDICES)

                      for v in range(len(data.VESSELS)))

                     , name=f'initial-delivery-load')


def add_load_capacity_constrs(model, l_D, l_P, u):
    model.addConstrs((l_D[v.get_index(), i] + l_P[v.get_index(), i]

                      <=

                      v.get_capacity() * u[v.get_index(), i]

                      for i in data.ALL_NODE_INDICES
                      for v in data.VESSELS)

                     , name=f'load-capacity-upper')


def add_load_continuity_constrs_1(model, x, l_D, l_P, u, departure_times, specific_arrival_times):
    model.addConstrs((l_D[v, j]

                      <=

                      l_D[v, i]
                      - data.ALL_NODES[j].get_order().get_size() * u[v, j]
                      + data.VESSELS[v].get_capacity() * (1 - gp.quicksum(x[v, i, t1, j, t2]
                                                                          for t1 in departure_times[v][i][j]
                                                                          for t2 in
                                                                          specific_arrival_times[v][i][j][t1]))

                      for i in data.ALL_NODE_INDICES[:-1]
                      for j in data.DELIVERY_NODE_INDICES if j != i
                      for v in range(len(data.VESSELS)))

                     , name=f'load-continuity-delivery-1')

    model.addConstrs((l_P[v, j]

                      >=

                      l_P[v, i]
                      + data.ALL_NODES[j].get_order().get_size() * u[v, j]
                      - data.VESSELS[v].get_capacity() * (1 - gp.quicksum(x[v, i, t1, j, t2]
                                                                          for t1 in departure_times[v][i][j]
                                                                          for t2 in
                                                                          specific_arrival_times[v][i][j][t1]))

                      for i in data.ALL_NODE_INDICES
                      for j in data.PICKUP_NODE_INDICES
                      for v in range(len(data.VESSELS)))

                     , name=f'load-continuity-pickup-1')


def add_load_continuity_constrs_2(model, x, l_D, l_P, departure_times, specific_arrival_times):
    model.addConstrs((l_D[v, j]

                      <=

                      l_D[v, i]
                      + data.VESSELS[v].get_capacity() * (1 - gp.quicksum(x[v, i, t1, j, t2]
                                                                          for t1 in departure_times[v][i][j]
                                                                          for t2 in
                                                                          specific_arrival_times[v][i][j][t1]))

                      for i in data.ALL_NODE_INDICES[:-1]
                      for j in data.PICKUP_NODE_INDICES if j != i
                      for v in range(len(data.VESSELS)))

                     , name=f'load-continuity-delivery-2')

    model.addConstrs((l_P[v, j]

                      >=

                      l_P[v, i]
                      - data.VESSELS[v].get_capacity() * (1 - gp.quicksum(x[v, i, t1, j, t2]
                                                                          for t1 in departure_times[v][i][j]
                                                                          for t2 in
                                                                          specific_arrival_times[v][i][j][t1]))

                      for i in data.ALL_NODE_INDICES
                      for j in data.DELIVERY_NODE_INDICES
                      for v in range(len(data.VESSELS)))

                     , name=f'load-continuity-pickup-2')


def add_final_pickup_load_constrs(model, l_P, u):
    model.addConstrs((l_P[v, data.ALL_NODE_INDICES[-1]]

                      ==

                      gp.quicksum(data.ALL_NODES[i].get_size() * u[v, i]
                                  for i in data.PICKUP_NODE_INDICES)

                      for v in range(len(data.VESSELS))),

                     name=f'final-pickup-load')
