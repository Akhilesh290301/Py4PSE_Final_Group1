import xml.etree.ElementTree as ET
import networkx as nx


def export_to_aml(graph: nx.DiGraph):
    root = ET.Element("CAEXFile", {"SchemaVersion": "3.0"})
    instance_hierarchy = ET.SubElement(root, "InstanceHierarchy", {"Name": "PPR_Export"})

    for node_id, data in graph.nodes(data=True):
        elem = ET.SubElement(
            instance_hierarchy,
            "InternalElement",
            {"ID": str(node_id), "Name": str(data.get("name", node_id))}
        )

        ET.SubElement(
            elem,
            "RoleRequirements",
            {"RefBaseRoleClassPath": f"PPR_Lib/{data.get('type', 'Unknown')}"}
        )

        for key, val in data.items():
            if key not in ["name", "type"]:
                attr = ET.SubElement(elem, "Attribute", {"Name": str(key)})
                ET.SubElement(attr, "Value").text = str(val)

    for u, v, data in graph.edges(data=True):
        ET.SubElement(instance_hierarchy, "InternalLink", {
            "Name": str(data.get("relation", "related_to")),
            "RefPartnerSideA": str(u),
            "RefPartnerSideB": str(v)
        })

    return ET.tostring(root, encoding="utf-8", method="xml")