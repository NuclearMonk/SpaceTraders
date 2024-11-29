from datetime import timedelta
from itertools import pairwise
from crud.system import get_system_db
from crud.waypoint import get_waypoints
import drawsvg as draw
from jinja2 import Environment, FileSystemLoader

from pathfinding.pathfinding import calculate_route, create_edges, create_nodes, djikstras
from schemas.navigation import WaypointTraitSymbol
from schemas.ship import ShipNavFlightMode
wps = get_waypoints('X1-Y3')
system = get_system_db('X1-Y3')
positions = {}
for wp in wps:
    if x := positions.get((wp.x, wp.y)):
        x.append(wp)
        continue
    positions[(wp.x, wp.y)] = [wp]

d = draw.Drawing(2000, 2000, origin='center',
                 id="svg_overlay", style="font-family: Departure;background-color:#000000")

d.append(draw.Rectangle(-1000, -1000, 0, 0, fill="#ff00ff"))
d.append(draw.Circle(0, 0, 1, fill='blue'))
for position, wpss in positions.items():
    # print(position, *(wp.symbol.split('-')[2] for wp in wpss))
    for wp in wpss:
        if wp.has_trait(WaypointTraitSymbol.MARKETPLACE):
            d.append(draw.Circle(position[0], position[1], 3, fill='red'))
            break
    else:
        d.append(draw.Circle(position[0], position[1], 3, fill='white'))
    d.append(draw.Text(" ".join((f"{wp.symbol.split(
        '-')[2]}") for wp in wpss), 4, x=position[0]+2.5, y=position[1]+2.5, fill='white'))


route=  calculate_route('X1-Y3-J74', 'X1-Y3-AZ5B', 400, 30, 400)
for step in route.steps:
        
        d.append(draw.Line(step.start.x, step.start.y, step.end.x,
                           step.end.y, stroke_width=1, stroke='green' if step.flight_mode== ShipNavFlightMode.CRUISE else 'yellow'))
        d.append(draw.Text(f"{timedelta(seconds=step.time)}", 2, x=(step.start.x+step.end.x)/2, y=(step.start.y+step.end.y)/2, fill='white'))
# nodes = create_nodes(wps)
# wp_edges = create_edges(nodes.values(), 400, 30)
# for wp, edges in wp_edges.items():
#     for edge in edges:
#         if edge.refuel:
#             d.append(draw.Line(edge.start.x, edge.start.y, edge.end.x,
#                     edge.end.y, stroke_width=0.1, stroke='green'))
#             d.append(draw.Text(str(edge.cost_fuel), 2, x=(edge.start.x+edge.end.x)/2, y=(edge.start.y+edge.end.y)/2, fill='white'))
# print("----------------------")
# print(*(wp.symbol for wp  in wps), sep='\n')

# start_wp = wps[0]
# for end_wp in wps:
#     route = calculate_route(start_wp.symbol, end_wp.symbol, 400, 400)
#     if not route:
#         continue
#     for s_wp, e_wp in pairwise(route):
#         print(s_wp[0].symbol, e_wp[0].symbol, s_wp[1], e_wp[1])
#         d.append(draw.Text(str(s_wp[0].distance_to(e_wp[0])), 2, x=(s_wp[0].x+e_wp[0].x)/2, y=(s_wp[0].y+e_wp[0].y)/2, fill='white'))
#         d.append(draw.Line(s_wp[0].x, s_wp[0].y, e_wp[0].x,
#                  e_wp[0].y, stroke_width=1, stroke='green'))
env = Environment(loader=FileSystemLoader("templates/"))
template = env.get_template("template.html")
html = template.render(svg_background=d.as_svg())
with open("output.html", "w") as output:
    output.write(html)
