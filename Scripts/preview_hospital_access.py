"""Render the corrected street, forecourt, and actual entrance corridor."""
import runpy
runpy.run_path(r"F:\Carnival\Scripts\capture_industrial_hospital_connected.py", init_globals={
    "CAPTURE_OUTPUT": "Saved/IndustrialHospital/Previews/CorrectedAccess",
})
