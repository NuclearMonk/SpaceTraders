

from pathfinding.pathfinding import calculate_route


route  = calculate_route("X1-ZN25-A1", "X1-ZN25-J55", 400, 400)

for wp in route:
    print(*wp)
