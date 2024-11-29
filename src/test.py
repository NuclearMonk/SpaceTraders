# from schemas.navigation import WaypointTraitSymbol
# from st_requests.market import get_market
# from st_requests.waypoint import get_system

# system = get_system('X1-Y3')
# for wp in system.waypoints:
#     if wp.has_trait(WaypointTraitSymbol.MARKETPLACE):
#         print(wp.symbol)
#         get_market(wp.symbol)


from state_machine.state_machine import StateMachine, State, Transition
from state_machine.states.waiting import StateWaiting

sm = StateMachine('Miner', [StateMachine('Extract SM',
                  [StateWaiting('Awaiting Cooldown'),
                   StateWaiting('Awaiting Pickup'),
                   State('Extract'),
                   State('Jettison')],
                  [Transition('Awaiting Cooldown', 'Extract', lambda: True, "Cooldown = 0"),
                   Transition('Extract', 'Jettison',
                              lambda: True, "Cargo Full"),
                   Transition('Extract', 'Awaiting Cooldown',
                              lambda: True, "Cargo Not Full"),
                   Transition('Jettison', 'Awaiting Pickup',
                              lambda: True, "Cargo Full"),
                   Transition('Jettison', 'Awaiting Cooldown',
                              lambda: True, "Cargo Not Full"),
                   Transition('Awaiting Pickup', 'Awaiting Cooldown',
                              lambda: True, "Cargo Not Full")

                   ],
                   'Awaiting Cooldown'),
                   StateMachine('Travel SM',
                                [State('Calculate Route'),
                                 StateWaiting('In Transit'),
                                 State('Match Status'),
                                 State('Done'),
                                 State('Refuel'),
                                 State('Orbit'),
                                 State('Match Speed'),
                                 State('Navigate')],
                                 [
                                    Transition('Calculate Route','In Transit', lambda: True, "Is in Transit"),
                                    Transition('Calculate Route','Match Status', lambda: True, "Is at Destination"),
                                    Transition('In Transit','Match Status', lambda: True, "Is Not in Transit"),
                                    Transition('Match Status', 'Done', lambda: True, "Is Final Destination"),
                                    Transition('Match Status', 'Refuel', lambda: True, "Needs Fuel"),
                                    Transition('Match Status', 'Match Speed', lambda: True, "Does NOT Need Fuel"),
                                    Transition('Refuel', 'Orbit', lambda: True, "Does NOT Need Fuel and Not in Orbit"),
                                    Transition('Orbit', 'Match Speed', lambda: True, "Is In Orbit"),
                                    Transition('Match Speed', 'Navigate', lambda: True, "In Orbit At Correct Speed"),
                                    Transition('Navigate', 'In Transit', lambda: True, "Is In Transit"),
                                  ], 'Calculate Route')],
                                [Transition('Extract SM', 'Travel SM', lambda: True, "Not At Assigned WP"),
                                 Transition('Travel SM', 'Extract SM',
                                            lambda: True, "At Assigned WP")
                                 ],
                                'Travel SM')

print(sm.viz().source)
