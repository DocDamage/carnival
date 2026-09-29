"""Focused real-vehicle regression; does not claim full route acceptance."""
import runpy
runpy.run_path(r"F:\Carnival\Scripts\playtest_industrial_hospital_route.py", init_globals={
    "ROUTE_START_INDEX": 985,
    "START_MODE": "motorcycle",
    "REPORT_PREFIX": "Forecourt_Playtest",
})
