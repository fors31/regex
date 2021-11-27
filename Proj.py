from RPQ import loadgraph, runquery, bfs, compile
from parse import NFA, State
import re


def get_outgoing_nodes(filename):
    '''
    Get all outgoing node from the server/file
    :param filename: Using txt filename in the format |start_node:node_# end_node:_node# transition|
    :return: a set of nodes
    '''
    g = loadgraph(filename)
    domain_name = list(g.keys())[0].split(":")[0]  # use the first node in the file to get the domain
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


def get_data_responses(origin_er, graph, list_out_nodes):
    '''
    Returns a tuple with a data structure with responses to all the requests sent to the servers
    and a set of not filtered nodes
    :param origin_er: original regular expression used to filter non end nodes
    :param graph: graph (dict) used for the guery (use loadgraph to convert)
    :param list_out_nodes: set of all outgoing nodes
    :return: a dict of {rule: [(origin_node, {response nodes})]}
    '''
    data_graph = dict()
    er_list, start_state, end_state = expand_re(origin_er)
    not_filtered = set()
    for node in graph:
        if node not in list_out_nodes:
            continue

        # Run a query for each rule of the expanded_re and inserts the responses in a
        # dict format -> {rule : [(start_node, {set of end nodes})]}
        for er in er_list:
            data_graph.setdefault(er, [])
            sol, visited, edgelist, bc = runquery(graph, node, er_list[er][2])
            res_nodes = set()
            for res_node in sol:
                if res_node in list_out_nodes or er_list[er][1].is_end is True:
                    res_nodes.add(res_node)
                    if er_list[er][1].is_end is True:
                        not_filtered.add(res_node)
            if len(res_nodes) != 0:
                data_graph[er].append((node, res_nodes))
    return data_graph, not_filtered


def get_data_graph(graph_list, origin_er, outnodes):
    '''
    Get all the responses data structure from all the servers and merge then into a single graph
    :param graph_list: a list of all the graph where requests are sent
    :param origin_er: regular expression to use to find the endpoints
    :param outnodes: set of all outgoing nodes in all the servers
    :return: a dict of all the data in a graph format
    '''

    # Merge all the data_responses together
    full_result, not_filtered_nodes = get_data_responses(origin_er, graph_list[0], outnodes)
    for graph in graph_list[1::]:
        partial_result, partial_not_filtered_nodes = get_data_responses(origin_er, graph, outnodes)
        for not_filtered_node in partial_not_filtered_nodes:
            not_filtered_nodes.add(not_filtered_node)
        for key in partial_result:
            if len(partial_result[key]) > 0:
                for result in partial_result[key]:
                    full_result[key].append(result)
    # Format the data_responses merged into a graph using the loadgraph format
    new_graph = dict()

    for key in full_result:
        for node in full_result[key]:
            new_graph.setdefault(node[0], list())
            for destination in node[1]:
                new_graph[node[0]].append((destination, key))
    for not_filtered_node in not_filtered_nodes: #add not filtered nodes to respect the format
        new_graph.setdefault(not_filtered_node, [])
    return new_graph

def get_all_out_nodes(list_of_graph):
    '''
    Use a list of filenames (graphs) to get all the outgoing nodes
    Returns a set of all outgoing nodes
    '''
    all_out_nodes = set()
    for graph in list_of_graph:
        nodes = get_outgoing_nodes(graph)
        all_out_nodes.update(list(nodes))
    return all_out_nodes


def expand_re(regex):
    '''
    TODO: automate the process
    Uses a regular expression in a format like <a><b>*<c> and decomposes it
    Us
    :param re: regular expression to decompose
    :return: a dict of rule : (start state, end state, regular expression),
             the NFA's start state and a set of all the end states
    '''
    compiled_regex = compile(regex)

    # Get a list of all the states of the original regex from the NFA
    states = []
    visited, queue = set(), [compiled_regex.start]

    while queue:
        vertex = queue.pop(0)
        if vertex not in visited:
            visited.add(vertex)
            transitions = set()
            for k in vertex.transitions.keys():
                trans = vertex.transitions[k]
                states.append(trans)
                if trans not in visited:
                    transitions.add(trans)

            transitions.update(vertex.epsilon)
            queue.extend([s for s in transitions if s not in visited])

    # Manual decomposition of the regex using states from the original regex NFA
    re_expanded = {"r1": (states[0], states[1], "<a><b>*"),
                   "r2": (states[0], states[2], "<a><b>*<c>"),
                   "r3": (states[0], states[3], "<a><b>*<c><d>"),
                   "r4": (states[1], states[1], "<b>+"),
                   "r5": (states[1], states[2], "<b>*<c>"),
                   "r6": (states[1], states[3], "<b>*<c><d>"),
                   "r7": (states[2], states[3], "<d>")}

    start_state = compiled_regex.start

    # Find all the end states in the NFA
    end_states = set()
    for state in states:
        if state.is_end is True:
            end_states.add(state)

    return re_expanded, start_state, end_states


def get_NFA(expanded_re):
    '''
    Builds an NFA using the State and NFA classes from parse.py
    :param expanded_re: Takes a dict after being passed into the expand_re method
    :return: an NFA object
    '''
    list_of_states = []
    transitions = dict()
    rules = expanded_re[0]
    end_state = None

    # Creates a list of all the states from the expanded_re rules
    for rule in rules:
        for state in rules[rule][:2]:
            if state not in list_of_states:
                list_of_states.append(state)

    # Get all the transitions for each State
    for rule in rules:
        transitions.setdefault(rules[rule][0], set())
        transitions[rules[rule][0]].add((rules[rule][1], rule))

    # Transform into a set of transition in dict and add them to the actual state
    for state in transitions:
        actual_transitions = {}
        for transition in transitions[state]:
            actual_transitions.setdefault(transition[1], transition[0])
        state.transitions = actual_transitions

    # Get first state
    start_state = list_of_states[0]
    list_of_states.remove(start_state)

    # Get last state
    for state in list_of_states:
        if state.is_end:
            end_state = state
            list_of_states.remove(state)

    # Set start and end states
    result_NFA = NFA(start_state, end_state)

    # Add all the states in between
    for inter_state in list_of_states:
        result_NFA.addstate(inter_state, set())

    return result_NFA


er = "<a><b>*<c><d>"

graph_filenames = ["graph_blue_2.txt", "graph_green_2.txt", "graph_red_2.txt"]

g = loadgraph("graph_complet2.txt")
gblue = loadgraph("graph_blue_2.txt")
ggreen = loadgraph("graph_green_2.txt")
gred = loadgraph("graph_red_2.txt")
outnodes = get_all_out_nodes(graph_filenames)
outnodes.add("blue:1")
graph_list = [gblue, ggreen, gred]

resultat = get_data_graph(graph_list, er, outnodes)

State0 = State("0")
State1 = State("1")
State2 = State("2")
State3 = State("3")
State0.transitions = {"r1": State1, "r2": State2, "r3": State3}
State1.transitions = {"r4": State1, "r5": State2, "r6": State3}
State2.transitions = {"r7": State3}
State3.is_end = True
NFA1 = NFA(State0, State3)
NFA1.addstate(State1, set())
NFA1.addstate(State2, set())

er_for_NFA, start, end = expand_re("<a><b>*<c><d>")


get_NFA(expand_re("<a><b>*<c><d>"))


test_graph = loadgraph("testing.txt")
#print(test_graph)
#print(resultat)
# for key in test_graph:
#     if key not in resultat:
#         print(key)

#print(resultat)
results = bfs(resultat, NFA1, "blue:1")
print(results[0])

#re_expanded.pretty_print()
#print(re_expanded.start.transitions['a'].name)

expand_re("<a><b>*<c><d>")