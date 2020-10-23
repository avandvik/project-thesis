import gurobipy as gp
import data


def add_flow_conservation_constrs(model, x, to_orders, specific_departure_times, specific_arrival_times, node_times):
    model.addConstrs((gp.quicksum(x[v, j, t2, i, t1]
                                  for j in to_orders[v, i, t1]
                                  for t2 in specific_departure_times[v, j, i, t1])

                      - gp.quicksum(x[v, i, t1, j, t2]
                                    for j in to_orders[v, i, t1]
                                    for t2 in specific_arrival_times[v, i, t1, j])
                      == 0
                      for v in range(len(data.VESSELS))
                      for i in range(len(data.ORDERS[1:-1]))
                      for t1 in node_times[v, i])

                     , name=f'flow-conservation-vessel-{v}_order_{i}_time_{t1}')


def add_visit_limit_constrs(model, x, u, departure_times, specific_arrival_times):
    model.addConstrs((gp.quicksum(x[v, i, t1, j, t2]
                                  for i in range(len(data.ORDERS)) if i != j  # TODO: Find out if i != j is needed
                                  for t1 in departure_times[v, i, j]
                                  for t2 in specific_arrival_times[v, i, t1, j])
                      <= u[j]

                      for j in range(len(data.ORDERS[1:-1]))
                      for v in range(len(data.VESSELS)))

                     , name=f'visit-limit-vessel_{v}_order_{j}')

    model.addConstrs((u[i] == 1 for i in range(len(data.MAND_ORDERS))), name=f'visit_all_mand-order_{i}')

    # TODO: Add constraints for init and final node


def add_initial_delivery_load_constrs(model, l_D):
    model.addConstrs((gp.quicksum(l_D[0, ])))

