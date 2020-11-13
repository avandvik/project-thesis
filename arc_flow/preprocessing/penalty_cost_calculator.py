import data


def calculate_penalty_costs(arc_costs, preparation_end_time):

    penalty_costs = []

    for j in data.ALL_NODE_INDICES:
        if j not in data.OPTIONAL_NODE_INDICES:
            penalty_costs.append(0)
        else:
            costs_from_depot = []
            for t in data.TIME_POINTS_DISC:
                if arc_costs[0][0][preparation_end_time][j][t] != 0:
                    costs_from_depot.append(arc_costs[0][0][preparation_end_time][j][t])

            # best_cost = min(costs_from_depot)
            # avg_cost = sum(costs_from_depot) / len(costs_from_depot)
            worst_cost = max(costs_from_depot)
            penalty_costs.append(worst_cost)

    return penalty_costs
