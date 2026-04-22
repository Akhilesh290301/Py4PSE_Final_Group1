import networkx as nx
def validate_ppr_model(graph: nx.DiGraph):
    errors = []
    valid_types = {"Product", "Process", "Resource"}

    for n, data in graph.nodes(data=True):
        if data.get("type") not in valid_types:
            errors.append(f"Node {n} has invalid PPR type: {data.get('type')}")

    allowed_edges = {
        ("Resource", "Process"),
        ("Process", "Product"),
        ("Product", "Product"),
        ("Process", "Process"),
        ("Resource", "Resource"),
    }

    for u, v in graph.edges():
        u_type = graph.nodes[u].get("type")
        v_type = graph.nodes[v].get("type")
        if (u_type, v_type) not in allowed_edges:
            errors.append(f"Invalid Relation: {u} ({u_type}) → {v} ({v_type})")

    return errors