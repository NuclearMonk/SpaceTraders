import argparse
import math
from login import API_KEY
from utils import print_json
from requests import get
from dataclasses import dataclass

SYSTEM_BASE_URL = "https://api.spacetraders.io/v2/systems/"


@dataclass
class WaypointSymbol:
    sector: str
    system: str
    waypoint: str = None

    @classmethod
    def split_symbol(cls, symbol_code: str):
        return symbol_code.split("-")

    @property
    def system_string(self):
        return f"{self.sector}-{self.system}"

    @property
    def waypoint_string(self):
        if self.waypoint:
            return f"{self.sector}-{self.system}-{self.waypoint}"
        return None

    def get_info(self):
        headers = {"Authorization": f"Bearer {API_KEY}"}
        print(f"GETTING INFO ON {self}")
        if self.waypoint:
            response = get(SYSTEM_BASE_URL + self.system_string +
                           "/waypoints/"+self.waypoint_string, headers=headers)
        else:
            response = get(SYSTEM_BASE_URL +
                           self.system_string, headers=headers)
        if response.ok:
            return response.json()
        else:
            return None

    def get_filtered_waypoints(self, query, limit=20):
        headers = {"Authorization": f"Bearer {API_KEY}"}
        wps = []
        current = 0
        m = float("inf")
        page=1
        while current < m:
            response = get(SYSTEM_BASE_URL + self.system_string +
                           f"/waypoints?{query}&page={page}", headers=headers)
            if response.ok:
                js = response.json()
                m = js["meta"]["total"]
                current += len(js["data"])
                page+=1
                wps.extend(js["data"])
        return wps

    def __str__(self) -> str:
        if self.waypoint:
            return self.waypoint_string
        else:
            return self.system_string


def distance_betweenWaypoints(A, B):
    return math.sqrt((A["x"]-B["x"])**2 + (A["y"]-B["y"])**2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("-s", "--search")
    args = parser.parse_args()
    if args.symbol:
        nav_point = WaypointSymbol(*WaypointSymbol.split_symbol(args.symbol))
    if args.search:
        if wps := nav_point.get_filtered_waypoints(args.search):
            start_data = nav_point.get_info()
            wps.sort(key=lambda x: distance_betweenWaypoints(
                start_data["data"], x))
            for d in wps:
                print(d["symbol"], d["x"], d["y"],
                      distance_betweenWaypoints(start_data["data"], d))
        else:
            "ERROR GETTING SYSTEM DATA"
    else:
        if wps := nav_point.get_info():
            print_json(wps)
        else:
            "ERROR GETTING SYSTEM DATA"
