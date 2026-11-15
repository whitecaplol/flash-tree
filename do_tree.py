import mermaidx
import mermaid.flowchart as fl
from bs4 import BeautifulSoup
from pathlib import Path

def main(node: Path, root_directory: Path, nodes: set[str], connections: list[tuple[str, str]]):
    node_from = str(node.relative_to(root_directory)).removeprefix("classes/").replace("/", "::")
    if (node_from in nodes): return
    nodes.add(node_from)

    with open(node / "content.html", "r") as f:
        soup = BeautifulSoup(f, "lxml")

        inherited_from = soup.find("span", class_="class-decl").find_all("a", class_="entity type")
        for inherited in inherited_from:
            link = str(inherited.get("href"))[1:]
            derived_path = root_directory / link
            main(derived_path, root_directory, nodes, connections)

        derived_classes = soup.find_all("details", class_="section")[-1].find_all("div", class_="entity class")

        for derived_class in derived_classes:
            link = str(derived_class.find("a").get("href"))[1:]
            derived_path = root_directory / link
            node_to = str(derived_path.relative_to(root_directory)).removeprefix("classes/").replace("/", "::")
            derivation = (node_from, node_to)

            if derivation not in connections:
                connections.append(derivation)
                main(derived_path, root_directory, nodes, connections)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root_input", help="The file in which you want to build the tree from.", type=Path)
    parser.add_argument("root_folder", help="The directory that the flash-generated documentation is contained in.", type=Path)
    parser.add_argument("root_output", help="Where to emit the mermaid output", type=Path)

    args = parser.parse_args()

    nodes: set[str] = set()
    connections: list[tuple[str, str]] = []

    main(args.root_input, args.root_folder, nodes, connections)

    print(f"Statistics: {len(nodes)} classes, {len(connections)} derived class counts (edges)")

    node_map = {node_str: fl.Node(node_str) for node_str in nodes}
    parsed_links = [fl.Link(node_map[a], node_map[b]) for a, b in connections]
    parsed_nodes = list(node_map.values())

    result = fl.FlowChart("", parsed_nodes, parsed_links).script
    mermaidx.render(
        result,
        config={
            "maxEdges": 100000,
            "maxTextSize": 10000000,
            "flowchart": {
                "wrappingWidth": 300,
                "padding": 20
            },
            "htmlLabels": False,
        },
        backend="js:pele",
    ).save(args.root_output)
