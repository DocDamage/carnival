"""Reproduce the tyre-contact stall on a bounded road stretch, not full-route acceptance."""
import runpy
runpy.run_path(r'F:\Carnival\Scripts\playtest_industrial_hospital_route.py',init_globals={
    'START_MODE':'motorcycle','REPORT_PREFIX':'Motorcycle_Tyre_Stall_Probe',
    'ROUTE_START_INDEX':40,'ROUTE_END_INDEX':90})
