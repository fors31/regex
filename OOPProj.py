from RPQ import loadgraph, runquery, bfs
from parse import NFA, State
from jinja2 import Environment, FileSystemLoader
import re

class Serveur:
    def __init__(self, name, domain, graph):
        self.name = name
        self.domain = domain
        self.graph = graph # File containing datagraph
        self.data = {}

    def get_last_state(self, er_expanded):
        '''
        Gets the end state from the dict of rules
        :param er_expanded: dict of rules
        :return: the end state of the automata
        '''
        end = set()
        for key in er_expanded:
            end.add(er_expanded[key][1])
        #return max(end)
        return 3

    def get_outgoing_nodes(self):
        '''
        Get all outgoing node from the server/file
        :return: a set of nodes
        '''
        g = loadgraph(self.graph)
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

class Client:
    def __init__(self, name):
        self.name = name
        self.knownServers = { "serveur1": ("blue", {"outnodes": set()}, {"innodes" : set()}),
                              "serveur2": ("green", {"outnodes": set()}, {"innodes": set()}),
                              "serveur3": ("red", {"outnodes": set()}, {"innodes": set()}),
                              }

    def expand_re(self, er):
        '''
        TODO: automate the process
        Uses a regular expression in a format like <a><b>*<c> and decomposes it
        :param re: regular expression to decompose
        :return: a dict of rule : (start state, end state, regular expression)
        '''
        er_expanded = {"r1": (0, 1, "<a><b>*"),
                       "r2": (0, 2, "<a><b>*<c>"),
                       "r3": (0, 3, "<a><b>*<c><d>"),
                       "r4": (1, 1, "<b>+"),
                       "r5": (1, 2, "<b>*<c>"),
                       "r6": (1, 3, "<b>*<c><d>"),
                       "r7": (2, 3, "<d>")}
        return er_expanded

    def get_data_graph(self, serveur, graph_list, origin_er, outnodes):
        '''
        Get all the responses data structure from all the servers and merge then into a single graph
        :param graph_list: a list of all the graph where requests are sent
        :param origin_er: regular expression to use to find the endpoints
        :param outnodes: set of all outgoing nodes in all the servers
        :return: a dict of all the data in a graph format
        '''

        # Merge all the data_responses together
        full_result, not_filtered_nodes = serveur.get_data_responses(origin_er, graph_list[0], outnodes)
        for graph in graph_list[1::]:
            partial_result, partial_not_filtered_nodes = serveur.get_data_responses(origin_er, graph, outnodes)
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


    def get_server_out_nodes(self, server):
        '''
        Returns the outgoing nodes of a specified server, if said server exists in the knownServers list
        Otherwise, adds this server to the list of knownServers
        :param server: a single server for which you want the outgoing nodes
        '''
        outnodes = server.get_outgoing_nodes()
        if server.name not in self.knownServers:
            self.knownServers.update({server.name : (server.domain, {"outnodes": (outnodes)}, {"innodes" : ()})})
        else:
            self.knownServers[server.name][1]["outnodes"] = outnodes


    def get_innodes(self, server, outnodes_list):
        '''
        Gets all incoming nodes for a given server.
        :param server: The server for which you want to find the incoming nodes
        :param outnodes_list: Outnodes list for outside servers of the one you inquire about
        :return: Updates this client's knownServers innodes for the server inquired about
        '''
        all_nodes = set()
        for node in outnodes_list: # Check all outgoing nodes in the given list
            if server.domain in node: # If inquired server's domain appears in the outgoing nodes list iteration
                all_nodes.add(node)
        self.knownServers[server.name][2]['innodes'] = (all_nodes) # Update known incoming nodes list for specified server


    def get_all_out_nodes(self, list_of_servers):
        '''
        Use a list of filenames (graphs) to get all the outgoing nodes
        Returns a set of all outgoing nodes
        '''
        all_out_nodes = set()
        for server in list_of_servers:
            nodes = server.get_outgoing_nodes()
            all_out_nodes.update(list(nodes))
        return all_out_nodes

    def get_data_responses(self, server, origin_er, list_out_nodes):
        '''
        Returns a tuple with a data structure with responses to all the requests sent to the servers
        and a set of not filtered nodes
        :param origin_er: original regular expression used to filter non end nodes
        :param graph: graph (dict) used for the guery (use loadgraph to convert)
        :param list_out_nodes: set of all outgoing nodes
        :return: a dict of {rule: [(origin_node, {response nodes})]}
        '''
        graph = server.graph
        data_graph = dict()
        er_list = self.expand_re(origin_er)
        end_state = server.get_last_state(er_list)
        not_filtered = set()
        for node in graph:
            if node not in list_out_nodes:
                continue
            for er in er_list:
                data_graph.setdefault(er, [])
                sol, visited, edgelist, bc = runquery(graph, node, er_list[er][2])
                res_nodes = set()
                for res_node in sol:
                    if res_node in list_out_nodes or end_state == er_list[er][1]:
                        res_nodes.add(res_node)
                        if end_state == er_list[er][1]:
                            not_filtered.add(res_node)
                if len(res_nodes) != 0:
                    data_graph[er].append((node, res_nodes))
        return data_graph, not_filtered

    def get_NFA(self, expanded_er, server):
        '''
        Builds an NFA using the State and NFA classes from parse.py
        :param expanded_er: Takes a dict after being passed into the expand_re method
        :return: an NFA object
        '''
        states = server.get_last_state(expanded_er) + 1
        list_of_states = []
        transitions = dict()

        # Creates a list of all the states
        for state in range(states):
            list_of_states.append(State(str(state)))

        # Get all the transitions for each state in textual form
        for er in expanded_er:
            transitions.setdefault(expanded_er[er][0], set())
            transitions[expanded_er[er][0]].add((expanded_er[er][1], er))

        # Transform into a set of transition in dict and add them to the actual state
        for trans_state in transitions:
            actual_transition = {}
            for transition in transitions[trans_state]:
                actual_transition.setdefault(transition[1], list_of_states[transition[0]])
            list_of_states[trans_state].transitions = actual_transition

        # Set start and end states
        result_NFA = NFA(list_of_states[0], list_of_states[len(list_of_states) - 1])

        # Add all the states in between
        for inter_state in list_of_states[1:-1]:
            result_NFA.addstate(inter_state, set())

        return result_NFA


c1 = Client("clientnom")
s1 = Serveur("serveur1", "blue", "graph_blue_2.txt")
s2 = Serveur("serveur2", "green", "graph_green_2.txt")
s3 = Serveur("serveur3", "red", "graph_red_2.txt")

er = "<a><b>*<c><d>"

graph_filenames = [s1, s2, s3]

g = loadgraph("graph_complet2.txt")
gblue = loadgraph("graph_blue_2.txt")
ggreen = loadgraph("graph_green_2.txt")
gred = loadgraph("graph_red_2.txt")
outnodes = c1.get_all_out_nodes(graph_filenames)
outnodes.add("blue:1")
graph_list = [gblue, ggreen, gred]


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

er_for_NFA = c1.expand_re("<a><b>*<c><d>")

file_loader = FileSystemLoader('SPARQL-Templates')
env = Environment(loader=file_loader)
template = env.get_template('test1.py')
output = template.render()
print(output)




