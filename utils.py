import pandas as pd
import networkx as nx
import json
from custom_nx import *
from itertools import chain
from collections import Counter


def cal(node, link, port=None, centrality='betweenness'):
    G = nx.DiGraph()
    n = node.copy()
    e = link.copy()
    nodes = n['ENCODED_ID']
    attributes = e[['ENCODED_DISTANCE']].to_json(orient='records')
    attributes = json.loads(attributes)
    edges = [(from_node, to_node, attr) for from_node, to_node, attr in zip(e['ENCODED_FROM_NODE'], e['ENCODED_TO_NODE'], attributes)]
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    
    if centrality != 'layout':
        if port is not None:
            p = port.copy()
            ports_count = p.groupby('ENCODED_ID')['ENCODED_PORT'].count().to_dict()
            ports = {}
            for node in nodes:
                if node not in ports_count:
                    ports[node] = 0
                else:
                    ports[node] = ports_count[node]
                    
            node_centrality, edge_centrality = parallel_all_centrality(G, weight = 'ENCODED_DISTANCE', factor = ports, centrality = centrality)
            nx.set_node_attributes(G, node_centrality, f'{centrality}')
            nx.set_edge_attributes(G, edge_centrality, f'{centrality}')
                    
        else:
            node_centrality, edge_centrality = parallel_all_centrality(G, weight = 'ENCODED_DISTANCE', centrality = centrality)
            nx.set_node_attributes(G, node_centrality, f'{centrality}')
            nx.set_edge_attributes(G, edge_centrality, f'{centrality}')

    data = nx.node_link_data(G)
    
    return data

def find_path(G, seq, weight = 'ENCODED_DISTANCE'):
    path = []
    if len(seq) == 1:
        return seq
    for i in range(len(seq)-1):
        try:
            p = nx.shortest_path(G, seq[i], seq[i+1], weight)
            path.extend(p)
        except:
            pass
    
    return path


def cal_flow(node, link, flow):
    f = flow.copy()

    G = nx.DiGraph()
    n = node.copy()
    e = link.copy()
    nodes = n['ENCODED_ID']
    attributes = e[['ENCODED_DISTANCE']].to_json(orient='records')
    attributes = json.loads(attributes)
    edges = [(from_node, to_node, attr) for from_node, to_node, attr in zip(e['ENCODED_FROM_NODE'], e['ENCODED_TO_NODE'], attributes)]
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    
    f = f.applymap(lambda x : list(map(int, x.split(','))))
    
    f = f.applymap(lambda x : find_path(G, x))
    
    f['loading_edges'] = f['loading'].apply(lambda x : [(x[i], x[i+1]) for i in range(len(x)-1)])
    f['destination_edges'] = f['destination'].apply(lambda x : [(x[i], x[i+1]) for i in range(len(x)-1)])
    f['pickup_edges']=f.apply(lambda row : [(row['loading'][-1], row['destination'][0])], axis=1)
    
    f = f[['loading_edges', 'destination_edges', 'pickup_edges']]
    
    loading_edges, destination_edges, pickup_edges = f.apply(lambda x : list(chain(*x)), axis=0)
    
    load_dict = dict(Counter(loading_edges))
    dest_dict = dict(Counter(destination_edges))
    pick_dict = dict(Counter(pickup_edges))
    tot_dict = dict(Counter(loading_edges) + Counter(destination_edges) + Counter(pickup_edges))
    
    load_dict = {edge: attr for edge, attr in load_dict.items() if edge in G.edges}
    dest_dict = {edge: attr for edge, attr in dest_dict.items() if edge in G.edges}
    pick_dict = {edge: attr for edge, attr in pick_dict.items() if edge in G.edges}
    tot_dict = {edge: attr for edge, attr in tot_dict.items() if edge in G.edges}

    nx.set_edge_attributes(G, load_dict, 'load_flow')
    nx.set_edge_attributes(G, dest_dict, 'dest_flow')
    nx.set_edge_attributes(G, pick_dict, 'pick_flow')
    nx.set_edge_attributes(G, tot_dict, 'flow')


    data = nx.node_link_data(G)

    return data
