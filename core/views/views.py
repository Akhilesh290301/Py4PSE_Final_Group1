import pandas as pd
import networkx as nx
BASE_COLUMNS = [
    "ID", "name", "type"
]
GENERAL_COLUMNS = [
    "Role",
    "Color",
    "Type",
    "WheelRequirement",
    "Material",
    "Position",
    "Amount",
    "Sequence",
    "WorksOn",
    "Uses",
    "Category",
]
ENGINEERING_COLUMNS = [
    "eng_cost",
    "target_value",
    "engineering_kpi",
    "eng_oee",
]
QUALITY_COLUMNS = [
    "technical_parameter",
    "qual_threshold",
    "process_parameter",
    "ok_nok",
]
def get_view_attributes(view_name: str):
    if view_name == "Normal PPR View":
        return GENERAL_COLUMNS

    if view_name == "Basic Engineering View":
        return GENERAL_COLUMNS + ENGINEERING_COLUMNS

    if view_name == "Quality View":
        return GENERAL_COLUMNS + QUALITY_COLUMNS

    return GENERAL_COLUMNS
def get_all_ordered_columns():
    return BASE_COLUMNS + GENERAL_COLUMNS + ENGINEERING_COLUMNS + QUALITY_COLUMNS
def _sort_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "display_order" in df.columns:
        df["display_order_numeric"] = pd.to_numeric(df["display_order"], errors="coerce")
        df = df.sort_values(by=["display_order_numeric", "ID"], kind="stable")
        df = df.drop(columns=["display_order_numeric"])
    else:
        df = df.sort_values(by=["ID"], kind="stable")

    return df.reset_index(drop=True)
def build_view_dataframe(graph: nx.DiGraph, selected_view: str) -> pd.DataFrame:
    visible_attrs = get_view_attributes(selected_view)
    ordered_columns = BASE_COLUMNS + visible_attrs

    rows = []

    for node_id, data in graph.nodes(data=True):
        row = {
            "ID": node_id,
            "name": data.get("name", ""),
            "type": data.get("type", ""),
            "display_order": data.get("display_order", ""),
        }

        for attr in visible_attrs:
            row[attr] = data.get(attr, "")

        rows.append(row)

    df = pd.DataFrame(rows)

    for col in ordered_columns:
        if col not in df.columns:
            df[col] = ""

    df = _sort_dataframe(df)
    df = df[["ID", "name", "type"] + visible_attrs]
    return df
def build_full_node_dataframe(graph: nx.DiGraph) -> pd.DataFrame:
    ordered_columns = get_all_ordered_columns()
    rows = []

    for node_id, data in graph.nodes(data=True):
        row = {
            "ID": node_id,
            "name": data.get("name", ""),
            "type": data.get("type", ""),
            "display_order": data.get("display_order", ""),
        }

        for attr in GENERAL_COLUMNS + ENGINEERING_COLUMNS + QUALITY_COLUMNS:
            row[attr] = data.get(attr, "")

        rows.append(row)

    df = pd.DataFrame(rows)

    for col in ordered_columns:
        if col not in df.columns:
            df[col] = ""

    df = _sort_dataframe(df)
    df = df[ordered_columns]
    return df
def filter_graph_by_view(graph: nx.DiGraph, selected_view: str) -> nx.DiGraph:
    if selected_view == "Normal PPR View":
        return graph.copy()

    if selected_view == "Basic Engineering View":
        relevant_attrs = ENGINEERING_COLUMNS
    elif selected_view == "Quality View":
        relevant_attrs = QUALITY_COLUMNS
    else:
        relevant_attrs = []

    filtered_graph = nx.DiGraph()

    for node_id, data in graph.nodes(data=True):
        include_node = False

        for attr in relevant_attrs:
            value = data.get(attr, "")
            if value not in ["", None, "None"]:
                include_node = True
                break

        if include_node:
            filtered_graph.add_node(node_id, **data)

    for source, target, edge_data in graph.edges(data=True):
        if source in filtered_graph.nodes and target in filtered_graph.nodes:
            filtered_graph.add_edge(source, target, **edge_data)

    return filtered_graph