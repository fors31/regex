from RPQ import loadgraph, runquery


def get_outgoing_nodes(domain_name, filename):
    g = loadgraph(filename)
    nodes_out = set()
    node_in = domain_name.lower()
    for key in g.keys():
        if key.split(":")[0].lower() != node_in:
            continue
        else:
            for value in g[key]:
                if value[0].split(":")[0].lower() != node_in:
                    nodes_out.add(value[0])
    return nodes_out


result = get_outgoing_nodes("green", "Graph Green.txt")
print(result)
