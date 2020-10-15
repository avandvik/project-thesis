import data
from arc_generation_v2 import ArcGenerator

ag = ArcGenerator()
ag.generate_arcs(16 * data.TIME_UNITS_PER_HOUR)
