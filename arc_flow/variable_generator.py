import data
import gurobipy as gp


def generate_arc_variables(model, departure_times, specific_arrival_times):
    x = {}

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            for j in range(len(data.ORDERS)):
                if i == j:
                    continue
                for t1 in departure_times[v][i][j]:
                    for t2 in specific_arrival_times[v][i][j][t1]:
                        x[v][i][t1][j][t2] = model.addVar(vtype=gp.GRB.BINARY, name=f'x_{i}_{t1}_{j}_{t2}_{v}')


def generate_order_served_variables(model):
    u = {}

    for i in range(len(data.ORDERS)):
        u[i] = model.addVar(vtype=gp.GRB.BINARY, name=f'u_{i}')


def generate_delivery_load_variables(model):
    l_D = {}

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            l_D[v][i] = model.addVar(vtype=gp.GRB.BINARY, name=f'l_D_{i}_{v}')


def generate_pickup_load_variables(model):
    l_P = {}

    for v in range(len(data.VESSELS)):
        for i in range(len(data.ORDERS)):
            l_P[v][i] = model.addVar(vtype=gp.GRB.BINARY, name=f'l_D_{i}_{v}')