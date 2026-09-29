"""Validate the complete hospital road in both directions by motorcycle."""
import runpy
runpy.run_path(r"F:\Carnival\Scripts\playtest_industrial_hospital_route.py", init_globals={
    "START_MODE": "motorcycle",
    "REPORT_PREFIX": "Motorcycle_Route_Playtest",
})
