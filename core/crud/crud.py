import networkx as nx
VALID_TYPES = {"Product", "Process", "Resource"}
def _next_display_order(graph: nx.DiGraph) -> int:
    if graph.number_of_nodes() == 0:
        return 0

    existing_orders = []
    for _, data in graph.nodes(data=True):
        value = data.get("display_order")
        if isinstance(value, int):
            existing_orders.append(value)
        else:
            try:
                existing_orders.append(int(value))
            except (TypeError, ValueError):
                pass

    return max(existing_orders, default=-1) + 1
def add_node(graph: nx.DiGraph, node_id: str, name: str, node_type: str, **attrs):
    if not node_id.strip():
        raise ValueError("Node ID is required.")
    if not name.strip():
        raise ValueError("Node name is required.")
    if node_type not in VALID_TYPES:
        raise ValueError("Invalid node type.")
    if node_id in graph:
        raise ValueError("Node already exists.")

    cleaned_attrs = {k: v for k, v in attrs.items() if str(v).strip() != ""}
    cleaned_attrs["display_order"] = _next_display_order(graph)

    graph.add_node(node_id.strip(), name=name.strip(), type=node_type, **cleaned_attrs)
def update_node(graph: nx.DiGraph, node_id: str, name: str, node_type: str, **attrs):
    if node_id not in graph:
        raise ValueError("Node does not exist.")
    if not name.strip():
        raise ValueError("Node name is required.")
    if node_type not in VALID_TYPES:
        raise ValueError("Invalid node type.")


    original_display_order = graph.nodes[node_id].get("display_order")

    graph.nodes[node_id]["name"] = name.strip()
    graph.nodes[node_id]["type"] = node_type

    for key, value in attrs.items():
        if str(value).strip() != "":
            graph.nodes[node_id][key] = value
        elif key in graph.nodes[node_id]:
            del graph.nodes[node_id][key]

    graph.nodes[node_id]["display_order"] = original_display_order
def delete_node(graph: nx.DiGraph, node_id: str):
    if node_id in graph:
        graph.remove_node(node_id)
def add_edge(graph: nx.DiGraph, source: str, target: str, relation: str):
    if source == target:
        raise ValueError("Source and target must be different.")
    if source not in graph or target not in graph:
        raise ValueError("Both nodes must exist.")
    if not relation.strip():
        raise ValueError("Relation is required.")

    graph.add_edge(source, target, relation=relation.strip())
def delete_edge(graph: nx.DiGraph, source: str, target: str):
    if graph.has_edge(source, target):
        graph.remove_edge(source, target)