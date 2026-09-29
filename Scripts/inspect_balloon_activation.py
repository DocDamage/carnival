"""Read-only inspection of the hot-air-balloon Blueprint activation path."""

import json
from pathlib import Path

import unreal


ASSETS = (
    "/Game/Carnival/Rides/BP_HotAirBalloon_Carnival",
    "/Game/Creepwood_Carnival_Meshingun/Environment/Blueprint/Ride/BP_HotairBalloon_Ride_01a",
)
REPORT = Path(r"F:\Carnival\Saved\Packages\BalloonActivationInspection.json")


def safe_property(obj, name):
    try:
        value = obj.get_editor_property(name)
        return str(value)
    except Exception as error:
        return "<%s>" % error


def inspect_blueprint(path):
    bp = unreal.load_asset(path)
    if bp is None:
        return {"asset": path, "error": "asset not found"}

    item = {"asset": path, "class": bp.get_class().get_name(), "graphs": []}
    item["editor_api"] = {}
    for type_name in ("BlueprintEditorLibrary", "KismetEditorUtilities", "GraphEditorLibrary", "EdGraph", "EdGraphNode"):
        type_obj = getattr(unreal, type_name, None)
        if type_obj:
            item["editor_api"][type_name] = [name for name in dir(type_obj) if "graph" in name.lower() or "node" in name.lower()]
    generated = None
    try:
        item["generated_class"] = bp.generated_class().get_path_name()
    except Exception as error:
        item["class_error"] = str(error)

    editor_lib = unreal.BlueprintEditorLibrary
    item["graph_api"] = [name for name in dir(editor_lib) if "graph" in name.lower()]
    graph_method = None
    for candidate in ("list_graphs", "get_all_graphs", "get_graphs", "get_blueprint_graphs"):
        if hasattr(editor_lib, candidate):
            graph_method = getattr(editor_lib, candidate)
            item["graph_method"] = candidate
            break
    try:
        graphs = graph_method(bp) if graph_method else []
    except Exception as error:
        item["graphs_error"] = str(error)
        graphs = []
    for graph in graphs:
        graph_data = {"name": graph.get_name(), "nodes": []}
        graph_data["graph_methods"] = [name for name in dir(graph) if "graph" in name.lower() or "node" in name.lower()]
        try:
            nodes = graph.get_editor_property("nodes")
        except Exception as error:
            graph_data["node_error"] = str(error)
            nodes = []
        for node in nodes:
            node_data = {"name": node.get_name(), "class": node.get_class().get_name()}
            for prop in ("function_reference", "member_name", "function_name", "node_title"):
                value = safe_property(node, prop)
                if value != "<Property not found>":
                    node_data[prop] = value
            node_data["text"] = node.get_class().get_name() + " " + node.get_name()
            graph_data["nodes"].append(node_data)
        item["graphs"].append(graph_data)

    try:
        item["component_templates"] = []
        subobjects = unreal.SubobjectDataBlueprintFunctionLibrary
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        item["subobject_api"] = [name for name in dir(subsystem) if "blueprint" in name.lower() or "gather" in name.lower()]
        for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
            data = subobjects.get_data(handle)
            template = subobjects.get_associated_object(data)
            if template is None or not isinstance(template, unreal.ActorComponent):
                continue
            component = {"name": template.get_name(), "class": template.get_class().get_name()}
            for prop in ("auto_activate", "auto_activate_for_player", "auto_destroy", "auto_manage_attachment"):
                try:
                    component[prop] = str(template.get_editor_property(prop))
                except Exception:
                    pass
            item["component_templates"].append(component)
    except Exception as error:
        item["component_templates_error"] = str(error)
    return item


report = {
    "blueprints": [inspect_blueprint(path) for path in ASSETS],
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("BALLOON_ACTIVATION_INSPECTION " + str(REPORT))
unreal.SystemLibrary.quit_editor()
