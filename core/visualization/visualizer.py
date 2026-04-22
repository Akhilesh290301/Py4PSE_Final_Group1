from graphviz import Digraph
import networkx as nx

from core.views.views import get_view_attributes, filter_graph_by_view

from yfiles_graphs_for_streamlit import (
    StreamlitGraphWidget,
    Layout,
    LabelStyle,
    EdgeStyle,
    FontWeight,
)


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pretty_attr_name(attr: str) -> str:
    pretty_names = {
        "eng_cost": "Engineering Cost",
        "eng_oee": "Engineering OEE",
        "engineering_kpi": "Engineering KPI",
        "target_value": "Target Value",
        "technical_parameter": "Technical Parameter",
        "qual_threshold": "Quality Threshold",
        "process_parameter": "Process Parameter",
        "ok_nok": "OK / NOK",
    }
    return pretty_names.get(attr, attr.replace("_", " ").title())


def _build_node_label(node_id: str, data: dict, selected_view: str) -> str:
    name = data.get("name", node_id)
    node_type = data.get("type", "Unknown")

    label_lines = [name, f"({node_type})"]

    visible_attrs = get_view_attributes(selected_view)
    for attr in visible_attrs:
        value = data.get(attr, "")
        if value not in ["", None, "None"]:
            label_lines.append(f"{_pretty_attr_name(attr)}: {value}")

    return "\n".join(label_lines)


def _get_base_style(node_type: str):
    styles = {
        "Product": {"fillcolor": "lightblue", "shape": "box", "fontcolor": "black"},
        "Process": {"fillcolor": "lightgreen", "shape": "ellipse", "fontcolor": "black"},
        "Resource": {"fillcolor": "orange", "shape": "diamond", "fontcolor": "black"},
        "Unknown": {"fillcolor": "lightgray", "shape": "oval", "fontcolor": "black"},
    }
    return styles.get(node_type, styles["Unknown"]).copy()


def _is_engineering_problem(data: dict) -> bool:
    oee = _safe_float(data.get("eng_oee"))
    kpi = _safe_float(data.get("engineering_kpi"))
    low_oee = oee is not None and oee < 0.7
    low_kpi = kpi is not None and kpi < 70
    return low_oee or low_kpi


def _is_quality_problem(data: dict) -> bool:
    return str(data.get("ok_nok", "")).strip().upper() == "NOK"


def _apply_view_highlight(style: dict, data: dict, selected_view: str):
    if selected_view == "Basic Engineering View" and _is_engineering_problem(data):
        style["fillcolor"] = "red"
        style["fontcolor"] = "white"

    elif selected_view == "Quality View" and _is_quality_problem(data):
        style["fillcolor"] = "red"
        style["fontcolor"] = "white"


def visualize_graphviz(graph: nx.DiGraph, selected_view: str) -> Digraph:
    filtered_graph = filter_graph_by_view(graph, selected_view)

    dot = Digraph()
    dot.attr(rankdir="LR")
    dot.attr("node", style="filled")

    for node_id, data in filtered_graph.nodes(data=True):
        node_type = data.get("type", "Unknown")
        style = _get_base_style(node_type)
        _apply_view_highlight(style, data, selected_view)

        dot.node(
            str(node_id),
            label=_build_node_label(str(node_id), data, selected_view),
            fillcolor=style["fillcolor"],
            fontcolor=style["fontcolor"],
            shape=style["shape"],
        )

    for u, v, data in filtered_graph.edges(data=True):
        dot.edge(str(u), str(v), label=data.get("relation", ""))

    return dot


def visualize_yfiles(graph: nx.DiGraph, selected_view: str) -> StreamlitGraphWidget:
    filtered_graph = filter_graph_by_view(graph, selected_view)

    def node_color_mapping(node: dict):
        props = node.get("properties", {})
        node_type = props.get("type", "Unknown")
        style = _get_base_style(node_type)
        _apply_view_highlight(style, props, selected_view)
        return style["fillcolor"]

    def node_size_mapping(node: dict):
        props = node.get("properties", {})
        if selected_view == "Basic Engineering View" and _is_engineering_problem(props):
            return (85, 85)
        if selected_view == "Quality View" and _is_quality_problem(props):
            return (85, 85)
        return (60, 60)

    def node_label_mapping(node: dict):
        props = node.get("properties", {})
        text = props.get("name", node.get("id", ""))

        is_problem = (
            selected_view == "Basic Engineering View" and _is_engineering_problem(props)
        ) or (
            selected_view == "Quality View" and _is_quality_problem(props)
        )

        return LabelStyle(
            text=text,
            font_weight=FontWeight.BOLD if is_problem else FontWeight.NORMAL,
            font_size=16 if is_problem else 12,
        )

    def edge_label_mapping(edge: dict):
        props = edge.get("properties", {})
        return props.get("relation", "")

    def edge_styles_mapping(edge: dict):
        return EdgeStyle(
            color="#888888",
            thickness=2,
        )

    widget = StreamlitGraphWidget.from_graph(
        graph=filtered_graph,
        node_color_mapping=node_color_mapping,
        node_size_mapping=node_size_mapping,
        node_label_mapping=node_label_mapping,
        edge_label_mapping=edge_label_mapping,
        edge_styles_mapping=edge_styles_mapping,
    )

    return widget


def show_yfiles(graph: nx.DiGraph, selected_view: str):
    widget = visualize_yfiles(graph, selected_view)
    widget.show(
        directed=True,
        graph_layout=Layout.HIERARCHIC,
        overview=True,
        sidebar={"enabled": True, "start_with": "Neighborhood"},
        key=f"yfiles_{selected_view}",
    )