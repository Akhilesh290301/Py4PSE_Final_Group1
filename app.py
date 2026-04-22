import tempfile
import networkx as nx
import pandas as pd
import streamlit as st

from core.parsers.aml_parser import parse_aml
from core.crud.crud import add_node, update_node, delete_node, add_edge, delete_edge
from core.exporter import export_to_aml
from core.utils.validator import validate_ppr_model
from core.visualization.visualizer import visualize_graphviz, show_yfiles
from core.views.views import (
    build_view_dataframe,
    build_full_node_dataframe,
    filter_graph_by_view,
)

st.set_page_config(page_title="Group 1: PPR Modeling Tool", layout="wide")

if "G" not in st.session_state:
    st.session_state.G = nx.DiGraph()

st.title("🛠️ Group 1: PPR Modeling Workbench")

with st.expander("How to use this app", expanded=False):
    st.markdown("""
### Workflow
1. Upload your AML model from the sidebar.
2. Click **Confirm Import** to load the model.
3. Select a **View**:
   - Normal PPR View
   - Basic Engineering View
   - Quality View
4. Select a **Visualization Type**:
   - Graphviz
   - yFiles 
5. Use **Nodes** and **Edges** tabs for CRUD operations.
6. Use **Views** to inspect the filtered model perspective.
7. Use **Visualization** to explore the graph.
8. Use **Analysis** for validation, reachability, and critical nodes.
9. Use **Export** to download the final AML file.

### Supported Input Format
- AML 

### Notes
- Graphviz is the required static visualization.
- yFiles is the interactive alternative.
- Basic Engineering View shows engineering-related attributes.
- Quality View shows quality-related attributes.
""")
# SIDEBAR CONTROLS:
st.sidebar.header("📂 Data Management")
uploaded_file = st.sidebar.file_uploader("Import AML File", type=["aml"])

if uploaded_file is not None:
    if st.sidebar.button("Confirm Import"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".aml") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        data = parse_aml(tmp_path)
        st.session_state.G = nx.DiGraph()

        for index, n in enumerate(data["nodes"]):
            attrs = dict(n["attributes"])
            attrs["display_order"] = index

            st.session_state.G.add_node(
                n["id"],
                name=n["name"],
                type=n["type"],
                **attrs
            )

        for e in data["edges"]:
            st.session_state.G.add_edge(
                e["source"],
                e["target"],
                relation=e["relation"]
            )

        st.sidebar.success("Model imported successfully.")
        st.rerun()

if st.sidebar.button("🗑️ Reset Model"):
    st.session_state.G = nx.DiGraph()
    st.rerun()

selected_view = st.selectbox(
    "Select View",
    ["Normal PPR View", "Basic Engineering View", "Quality View"]
)

visualization_mode = st.selectbox(
    "Select Visualization Type",
    ["Graphviz", "yFiles Graph"]
)
# TABS
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📥 Import & Summary",
    "🏗️ Nodes",
    "🔗 Edges",
    "👁️ Views",
    "📊 Visualization",
    "⚙️ Analysis",
    "💾 Export"
])
# TAB 1: IMPORT & SUMMARY,
with tab1:
    st.header("Import & Model Summary")

    graph = st.session_state.G

    if graph.number_of_nodes() == 0:
        st.info("No model loaded yet.")
    else:
        products = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "Product")
        processes = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "Process")
        resources = sum(1 for _, d in graph.nodes(data=True) if d.get("type") == "Resource")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Nodes", graph.number_of_nodes())
        c2.metric("Total Edges", graph.number_of_edges())
        c3.metric("Products", products)
        c4.metric("Processes", processes)
        c5.metric("Resources", resources)

        st.divider()

        c6, c7 = st.columns(2)
        c6.info(f"**Selected View:** {selected_view}")
        c7.info(f"**Visualization Mode:** {visualization_mode}")

        st.subheader("Node Type Distribution")
        type_counts = pd.Series(
            [d.get("type", "Unknown") for _, d in graph.nodes(data=True)]
        ).value_counts()

        st.dataframe(
            type_counts.rename_axis("Type").reset_index(name="Count"),
            use_container_width=True
        )
# TAB 2: NODE CRUD
with tab2:
    st.header("Node Management")
    graph = st.session_state.G

    existing_nodes = list(graph.nodes)
    mode = st.radio("Choose Action", ["Add Node", "Update Existing Node"], horizontal=True)

    selected_node_id = None
    existing_data = {}

    if mode == "Update Existing Node":
        if existing_nodes:
            selected_node_id = st.selectbox("Select Node to Update", existing_nodes)
            existing_data = graph.nodes[selected_node_id]
        else:
            st.info("No existing nodes available to update.")

    with st.form("node_form"):
        if mode == "Add Node":
            default_id = ""
            default_name = ""
            default_type = "Product"
        else:
            default_id = selected_node_id
            default_name = existing_data.get("name", "")
            default_type = existing_data.get("type", "Product")

        c1, c2, c3 = st.columns(3)

        nid = c1.text_input("Node ID", value=default_id, disabled=(mode == "Update Existing Node"))
        nname = c2.text_input("Node Name", value=default_name)

        type_options = ["Product", "Process", "Resource"]
        default_type_index = type_options.index(default_type) if default_type in type_options else 0
        ntype = c3.selectbox("Node Type", type_options, index=default_type_index)

        attrs = {}

        if selected_view == "Basic Engineering View":
            st.subheader("Basic Engineering Attributes")

            c4, c5 = st.columns(2)
            attrs["eng_cost"] = c4.text_input(
                "Engineering Cost",
                value="" if mode == "Add Node" else str(existing_data.get("eng_cost", ""))
            )
            attrs["target_value"] = c5.text_input(
                "Target Value",
                value="" if mode == "Add Node" else str(existing_data.get("target_value", ""))
            )

            c6, c7 = st.columns(2)
            attrs["engineering_kpi"] = c6.text_input(
                "Engineering KPI",
                value="" if mode == "Add Node" else str(existing_data.get("engineering_kpi", ""))
            )
            attrs["eng_oee"] = c7.text_input(
                "Engineering OEE",
                value="" if mode == "Add Node" else str(existing_data.get("eng_oee", ""))
            )

        elif selected_view == "Quality View":
            st.subheader("Quality Attributes")

            c4, c5 = st.columns(2)
            attrs["technical_parameter"] = c4.text_input(
                "Technical Parameter",
                value="" if mode == "Add Node" else str(existing_data.get("technical_parameter", ""))
            )
            attrs["qual_threshold"] = c5.text_input(
                "Quality Threshold",
                value="" if mode == "Add Node" else str(existing_data.get("qual_threshold", ""))
            )

            c6, c7 = st.columns(2)
            attrs["process_parameter"] = c6.text_input(
                "Process Parameter",
                value="" if mode == "Add Node" else str(existing_data.get("process_parameter", ""))
            )

            ok_nok_options = ["", "OK", "NOK"]
            current_ok_nok = "" if mode == "Add Node" else str(existing_data.get("ok_nok", ""))
            ok_nok_index = ok_nok_options.index(current_ok_nok) if current_ok_nok in ok_nok_options else 0

            attrs["ok_nok"] = c7.selectbox(
                "OK / NOK",
                ok_nok_options,
                index=ok_nok_index
            )

        submitted = st.form_submit_button("Save Node")

        if submitted:
            try:
                if mode == "Add Node":
                    add_node(graph, nid, nname, ntype, **attrs)
                    st.success(f"Node '{nid}' added.")
                else:
                    update_node(graph, nid, nname, ntype, **attrs)
                    st.success(f"Node '{nid}' updated.")

                st.rerun()

            except Exception as e:
                st.error(str(e))

    if graph.number_of_nodes() > 0:
        st.subheader("Current Nodes")
        st.dataframe(
            build_full_node_dataframe(graph),
            use_container_width=True
        )

        delete_id = st.selectbox("Select Node to Delete", list(graph.nodes), key="delete_node_key")
        if st.button("Delete Node"):
            delete_node(graph, delete_id)
            st.rerun()
    else:
        st.info("No nodes in the model yet.")
# TAB 3: EDGE CRUD
with tab3:
    st.header("Relationship Management")
    graph = st.session_state.G

    c1, c2 = st.columns(2)
    c1.metric("Total Edges", graph.number_of_edges())
    c2.metric("Total Nodes", graph.number_of_nodes())

    if graph.number_of_nodes() > 1:
        with st.form("add_edge_form"):
            source = st.selectbox("Source Node", list(graph.nodes), key="source_key")
            target = st.selectbox("Target Node", list(graph.nodes), key="target_key")
            relation = st.text_input("Relation")

            if st.form_submit_button("Add Edge"):
                try:
                    add_edge(graph, source, target, relation)
                    st.success(f"Added edge: {source} → {target}")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    if graph.number_of_edges() > 0:
        st.subheader("Current Edges")
        edge_rows = []
        for u, v, data in graph.edges(data=True):
            edge_rows.append({
                "Source": u,
                "Target": v,
                "Relation": data.get("relation", "")
            })
        st.dataframe(pd.DataFrame(edge_rows), use_container_width=True)

        edge_options = [f"{u} -> {v}" for u, v in graph.edges()]
        edge_to_del = st.selectbox("Select Edge to Delete", edge_options, key="edge_delete_key")
        if st.button("Delete Edge"):
            src, tgt = edge_to_del.split(" -> ")
            delete_edge(graph, src, tgt)
            st.rerun()
    else:
        st.info("No edges found.")
# TAB 4: VIEWS
with tab4:
    st.header("PPR Views")

    if st.session_state.G.number_of_nodes() > 0:
        filtered_graph = filter_graph_by_view(st.session_state.G, selected_view)
        view_df = build_view_dataframe(filtered_graph, selected_view)

        if selected_view == "Normal PPR View":
            st.info("Showing the complete PPR model.")
        elif selected_view == "Basic Engineering View":
            st.info("Showing only nodes relevant to Basic Engineering View.")
        elif selected_view == "Quality View":
            st.info("Showing only nodes relevant to Quality View.")

        c1, c2 = st.columns(2)
        c1.metric("Visible Nodes", filtered_graph.number_of_nodes())
        c2.metric("Visible Edges", filtered_graph.number_of_edges())

        st.dataframe(view_df, use_container_width=True)
    else:
        st.info("No model loaded.")
# TAB 5: VISUALIZATION
with tab5:
    st.header("System Visualization")

    if selected_view == "Normal PPR View":
        st.info("Showing the complete PPR graph.")
    elif selected_view == "Basic Engineering View":
        st.info("Showing only Basic Engineering nodes. Red nodes indicate low OEE (< 0.7) or low Engineering KPI (< 70).")
    elif selected_view == "Quality View":
        st.info("Showing only Quality nodes. Red nodes indicate NOK status.")

    if st.session_state.G.number_of_nodes() > 0:
        filtered_graph = filter_graph_by_view(st.session_state.G, selected_view)

        if filtered_graph.number_of_nodes() > 0:
            if visualization_mode == "Graphviz":
                st.graphviz_chart(visualize_graphviz(st.session_state.G, selected_view))
            else:
                show_yfiles(st.session_state.G, selected_view)
        else:
            st.warning("No nodes available for the selected view.")
    else:
        st.info("Graph is empty.")
# TAB 6: ANALYSIS
with tab6:
    st.header("PPR Validation & Analysis")
    graph = st.session_state.G

    st.subheader("Model Integrity Check")
    validation_errors = validate_ppr_model(graph)

    if not validation_errors and graph.number_of_nodes() > 0:
        st.success("✅ STATUS: PPR VALID")
    elif graph.number_of_nodes() == 0:
        st.info("No data to validate.")
    else:
        st.error("❌ STATUS: PPR INVALID")
        for err in validation_errors:
            st.write(f"- {err}")

    st.divider()
    st.subheader("Reachability Analysis")

    if graph.number_of_nodes() > 0:
        reach_source = st.selectbox("Select Source Node", list(graph.nodes), key="reachability_source")

        if st.button("Show Reachable Nodes"):
            reachable = nx.descendants(graph, reach_source)
            reachable_list = sorted(list(reachable))

            st.write(f"**Reachable Node Count:** {len(reachable_list)}")

            if reachable_list:
                reach_rows = []
                for node_id in reachable_list:
                    reach_rows.append({
                        "ID": node_id,
                        "name": graph.nodes[node_id].get("name", ""),
                        "type": graph.nodes[node_id].get("type", "")
                    })
                st.dataframe(pd.DataFrame(reach_rows), use_container_width=True)
            else:
                st.info("No reachable nodes found from the selected source.")
    else:
        st.info("No graph available for reachability analysis.")

    st.divider()
    st.subheader("Structural Analysis")

    if graph.number_of_nodes() > 0:
        comps = [graph.subgraph(c).copy() for c in nx.weakly_connected_components(graph)]
        large = [c for c in comps if len(c.nodes) >= 5]

        c1, c2 = st.columns(2)
        c1.metric("Disconnected Segments", len(comps))
        c2.metric("Subgraphs with ≥ 5 Nodes", len(large))

        if large:
            st.success(f"Found {len(large)} subgraph(s) with at least 5 nodes.")
        else:
            st.info("No subgraphs with at least 5 nodes found.")
    else:
        st.info("No graph available for structural analysis.")

    st.divider()
    st.subheader("Critical Nodes (Based on Selected View)")

    problem_nodes = []

    if selected_view == "Basic Engineering View":
        for n, data in graph.nodes(data=True):
            try:
                oee = float(data.get("eng_oee", 1))
                kpi = float(data.get("engineering_kpi", 100))
            except Exception:
                continue

            if oee < 0.7 or kpi < 70:
                problem_nodes.append({
                    "ID": n,
                    "name": data.get("name"),
                    "Engineering OEE": data.get("eng_oee"),
                    "Engineering KPI": data.get("engineering_kpi")
                })

    elif selected_view == "Quality View":
        for n, data in graph.nodes(data=True):
            if str(data.get("ok_nok", "")).upper() == "NOK":
                problem_nodes.append({
                    "ID": n,
                    "name": data.get("name"),
                    "Status": "NOK"
                })

    if selected_view in ["Basic Engineering View", "Quality View"]:
        if problem_nodes:
            st.error(f"{len(problem_nodes)} critical node(s) found")
            st.dataframe(pd.DataFrame(problem_nodes), use_container_width=True)
        else:
            st.success("No critical nodes detected")
    else:
        st.info("Select Basic Engineering View or Quality View to see view-specific critical nodes.")
# TAB 7: EXPORT
with tab7:
    st.header("Final Export")

    if st.session_state.G.number_of_nodes() > 0:
        st.download_button(
            "📥 Download AML for Submission",
            data=export_to_aml(st.session_state.G),
            file_name="final_ppr_model.aml",
            mime="application/xml"
        )
    else:
        st.info("No model available for export.")