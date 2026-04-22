import xml.etree.ElementTree as ET
def parse_aml(file_path: str):
    tree = ET.parse(file_path)
    root = tree.getroot()
    namespace = {"ns": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}

    def q(tag: str) -> str:
        return f"ns:{tag}" if namespace else tag

    nodes, edges = [], []

    for elem in root.findall(f".//{q('InternalElement')}", namespace):
        node_id = elem.get("ID")
        name = elem.get("Name")
        if not node_id or not name:
            continue

        role_elem = elem.find(q("RoleRequirements"), namespace)
        node_type = (
            role_elem.get("RefBaseRoleClassPath", "").split("/")[-1]
            if role_elem is not None else "Unknown"
        )

        attributes = {}
        for attr in elem.findall(q("Attribute"), namespace):
            attr_name = attr.get("Name")
            value_elem = attr.find(q("Value"), namespace)
            attr_value = value_elem.text if value_elem is not None else None
            if attr_name:
                attributes[attr_name] = attr_value

        nodes.append({
            "id": node_id,
            "name": name,
            "type": node_type,
            "attributes": attributes
        })

    for link in root.findall(f".//{q('InternalLink')}", namespace):
        source = link.get("RefPartnerSideA")
        target = link.get("RefPartnerSideB")
        if source and target:
            edges.append({
                "source": source,
                "target": target,
                "relation": link.get("Name") or "related_to"
            })

    return {"nodes": nodes, "edges": edges}