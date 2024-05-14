import networkx as nx
from networkx.utils import py_random_state
from networkx.algorithms.centrality.betweenness import _single_source_shortest_path_basic, _single_source_dijkstra_path_basic, _accumulate_endpoints,\
    _accumulate_basic, _rescale_e, _rescale, _accumulate_edges
import multiprocessing
import numpy as np

# ---------------------- node/edge return at once -----------------

def node_edge_betweenness(G, normalized=True, weight=None, seed=None, factor=None, nodes = None):
   
    betweenness = dict.fromkeys(G, 0.0)
    betweenness.update(dict.fromkeys(G.edges(), 0.0))     

    if nodes is None:
        nodes = G
    
    for s in nodes:
        if weight is None:
            S, P, sigma, D = _single_source_shortest_path_basic(G, s)
        else: 
            S, P, sigma, D = _single_source_dijkstra_path_basic(G, s, weight)
        

        if factor is not None:
            betweenness = _custom_accumulate(betweenness, S, P, sigma, s, factor)
        else:
            betweenness = _accumulate_edges(betweenness, S, P, sigma, s)

    node_betweenness = {}
            
    for n in G.nodes:
        node_betweenness[n] = betweenness.pop(n)
    
    edge_betweenness = betweenness

    if normalized:
        num = sum(list(factor.values())) if factor is not None else len(G)

        node_betweenness = _rescale(
            node_betweenness,
            num,
            normalized=normalized,
            directed=G.is_directed(),
            endpoints=False,
        )

        edge_betweenness = _rescale_e(
                    edge_betweenness, num, normalized=normalized, directed=G.is_directed()
                    )

    
    return node_betweenness, edge_betweenness

def node_edge_stress(G, normalized=True, weight=None, seed=None, factor=None, nodes = None):
   
    stress = dict.fromkeys(G, 0.0)
    stress.update(dict.fromkeys(G.edges(), 0.0))

    if nodes is None:
        nodes = G
                
    for s in nodes:
        if weight is None:
            S, P, sigma, D = _single_source_shortest_path_basic(G, s)
        else:
            S, P, sigma, D = _single_source_dijkstra_path_basic(G, s, weight)
        
        stress = _stress_accumulate(stress, S, P, sigma, s, factor)

    node_stress = {}
            
    for n in G.nodes:
        node_stress[n] = stress.pop(n)
    
    edge_stress = stress
    
    return node_stress, edge_stress

def _custom_accumulate(betweenness, S, P, sigma, s, factor):
    delta = dict.fromkeys(S, 0)
    factors = [factor[v] for v in S if v !=  s]
    betweenness[s] += factor[s] * sum(factors)
    
    while S:
        w = S.pop()
        coeff = (factor[s] * factor[w] + delta[w]) / sigma[w]
        for v in P[w]:
            c = sigma[v] * coeff
            if (v, w) not in betweenness:
                betweenness[(w, v)] += c
            else:
              betweenness[(v, w)] += c
            delta[v] += c
        if w != s:
            betweenness[w] += delta[w] + factor[s] * factor[w]
    return betweenness

def _stress_accumulate(stress, S, P, sigma, s, factor):
    delta = dict.fromkeys(S, 0)

    if factor is None:
        while S:
            w = S.pop()
            for v in P[w]:
                c = sigma[v]*(1+delta[w]/sigma[w])
                if (v, w) not in stress:
                    stress[(w, v)] += c
                else:
                    stress[(v, w)] += c
                delta[v] += c
            if w != s:
                stress[w] += delta[w]
        return stress
    
    else:
        factors = [factor[v]*sigma[v] for v in S if v !=  s]
        stress[s] += factor[s] * sum(factors)
        while S:
            w = S.pop()
            for v in P[w]:
                c = sigma[v] * (factor[s] * factor[w] + delta[w]/sigma[w])
                if (v, w) not in stress:
                    stress[(w, v)] += c
                else:
                    stress[(v, w)] += c
                delta[v] += c
            if w != s:
                stress[w] += delta[w] + factor[s] * factor[w] * sigma[w]
        return stress


#  ---------------- parallelization --------------------

def compute_all(args):
    G, chunk, weight, factor, centrality = args

    process_name = multiprocessing.current_process().name
    print(f"Process {process_name} starting computation for chunk {chunk}")
    
    if centrality == 'betweenness':
        result = node_edge_betweenness(G, weight=weight, nodes=chunk, factor = factor)
    elif centrality == 'stress':
        result = node_edge_stress(G, weight=weight, nodes=chunk, factor = factor)
    
    print(f"Process {process_name} completed computation for chunk {chunk}")

    return result

def parallel_all_centrality(G, process_count=100, weight = None, factor = None, centrality = 'betweenness'):
    
    process_count = min(multiprocessing.cpu_count(), process_count)

    chunks = np.array_split(G.nodes(), process_count)

    args = [(G, chunk, weight, factor, centrality) for chunk in chunks]
    
    with multiprocessing.Pool(processes=process_count) as pool:
        results = pool.map(compute_all, args)

    combined_centrality = dict.fromkeys(G, 0.0)
    combined_edge_centrality = dict.fromkeys(G.edges(), 0.0)

    for node_betweenness, edge_betweenness in results:
        for node, centrality in node_betweenness.items():
            combined_centrality[node] += centrality
        for edge, centrality in edge_betweenness.items():
            combined_edge_centrality[edge] += centrality

    return combined_centrality, combined_edge_centrality