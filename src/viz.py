from itertools import pairwise, product
from crud.system import get_system_db
from crud.waypoint import get_waypoints
import drawsvg as draw
from jinja2 import Environment, FileSystemLoader

from pathfinding.pathfinding import calculate_route
wps = get_waypoints('X1-Y3')
system = get_system_db('X1-Y3')
positions = {}
for wp in wps:
    if x := positions.get((wp.x, wp.y)):
        x.append(wp)
        continue
    positions[(wp.x, wp.y)] = [wp]

d = draw.Drawing(2000, 2000, origin='center',
                 id="svg_overlay", style="font-family: Departure;")

d.append(draw.Rectangle(-1000, -1000, 0, 0, fill="#ff00ff"))
d.append(draw.Circle(0, 0, 1, fill='blue'))

for position, wpss in positions.items():
    # print(position, *(wp.symbol.split('-')[2] for wp in wpss))
    d.append(draw.Circle(position[0], position[1], 1, fill='white'))
    d.append(draw.Text(" ".join(wp.symbol.split(
        '-')[2] for wp in wpss), 2, x=position[0]+1.5, y=position[1]+1.5, fill='white'))

start_wp = wps[0]
for end_wp in wps:
    route = calculate_route(start_wp.symbol, end_wp.symbol, 400, 400)
    if not route:
        continue
    for s_wp, e_wp in pairwise(route):
        print(s_wp[0].symbol, e_wp[0].symbol, s_wp[1], e_wp[1])
        d.append(draw.Line(s_wp[0].x, s_wp[0].y, e_wp[0].x,
                 e_wp[0].y, stroke_width=1, stroke='green'))
env = Environment(loader=FileSystemLoader("templates/"))
template = env.get_template("template.html")
html = template.render(svg_background=d.as_svg())
with open("output.html", "w") as output:
    output.write(html)
