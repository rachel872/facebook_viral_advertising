import networkx as nx
import numpy as np
from tqdm import tqdm
from operator import itemgetter
import time

def get_strength():
    return np.random.exponential(2)

def check_all_seen(G, items):
    complete = 0
    # For each node in the network
    for node in G.nodes():
        # If it has not seen every post
        if G.node[node]['seen'] != {k + 1:True for k in range(items)}:
            # return false and exit loop
            return False, round(complete/len(G.nodes()),0)
        # If it has seen every post, move onto next node
        complete += 1
        continue
    # If all nodes have seen all posts, return true
    return True, 100

def find_next_post(G, newsfeed, previously_posted):
    # For each post in the newsfeed
    for post in newsfeed:
        # If its post number is 0, skip it
        if G.node[post]['current_post'] == 0:
            continue

        # If its post number isn't 0, and it hasn't already been posted
        if G.node[post]['current_post'] not in previously_posted:
            # Repost that item
            return G.node[post]['current_post']

    # If nothing has been posted
    if len(previously_posted) == 0:
        # Continue to post nothing
        return 0
    # Otherwise
    else:
        # Post a random item that has previously been posted
        return np.random.choice(previously_posted)

F = nx.Graph()

edges = [['A', 'B'], ['A', 'C'], ['A', 'E'], ['A', 'F'], ['A', 'H'],
           ['B', 'D'], ['B', 'E'], ['C', 'E'], ['C', 'F'],
           ['C', 'G'], ['C', 'H'], ['E', 'H'],['F', 'G']]
for i in edges:
    F.add_edge(i[0], i[1], strength=0)

n = 1
items = 4
newsfeed_composition = [3,2,1]

# Add 'strength of connection' as weight to each edge
for i in F.nodes():
    for k in F.neighbors(i):
        F[i][k]['strength'] = get_strength()

for i in tqdm(range(n)):
    # Create empty graph
    G = nx.Graph()

    # Create newsfeed for each node in F
    for node in tqdm(F.nodes()):
        w_edges = []
        # Get edge strength for each edge between the current node and its
        # neighbors
        for j in F.neighbors(node):
            w_edges.append([j, F.get_edge_data(node, j)['strength']])

        # Filter w_edges for the strongest 1/3rd of edges
        strong_nodes = [i for i in w_edges if i[1] > 1.4]
        # Sort strong nodes descending for strength
        strong_nodes = sorted(strong_nodes, key=itemgetter(1), reverse=True)
        # FIlter w_edges for remaining 2/3rd of edges
        weak_nodes = [i for i in w_edges if i[1] <= 1.4]
        # Sort weak nodes descending for strength
        weak_nodes = sorted(weak_nodes, key=itemgetter(1), reverse=True)
        # Set all other non-neighbor nodes as random
        random_nodes = [i for i in F.nodes() if i not in F.neighbors(node)]

        # Calculate probabilities for each strong and weak node based on
        # relative strength
        strong_tot = sum([i[1] for i in strong_nodes])
        weak_tot = sum([i[1] for i in weak_nodes])
        strong_proba = []
        for j in strong_nodes:
            strong_proba.append(j[1]/strong_tot)
        weak_proba = []
        for j in weak_nodes:
            weak_proba.append(j[1] / weak_tot)

        # Construct news feed
        newsfeed = []

        # If there aren't enough strong nodes to fill the quota
        if len(strong_nodes) < newsfeed_composition[0]:
            newsfeed.extend([i[0] for i in strong_nodes])
        else:
            # Add a random selection of strong nodes, weighted according to
            # strength
            newsfeed.extend(np.random.choice([i[0] for i in strong_nodes],
                                             size=newsfeed_composition[0],
                                             replace=False, p=strong_proba))

        # If there aren't enough weak nodes to fill the quota
        if len(weak_nodes) < newsfeed_composition[1]:
            # Add all available weak nodes
            newsfeed.extend([i[0] for i in weak_nodes])
        else:
            # Add a random selection of weak nodes, weighted according to
            # strength
            newsfeed.extend(np.random.choice([i[0] for i in weak_nodes],
                            size=newsfeed_composition[1],
                            replace=False, p=weak_proba))

        # For remaining spots in the newsfeed, populate with random
        for j in range(sum(newsfeed_composition) - len(newsfeed)):
            newsfeed.append(np.random.choice(random_nodes))

        # Add the newsfeed edges to the new graph
        for j in newsfeed:
            G.add_edge(node, j)
        G.node[node]['newsfeed'] = newsfeed
        G.node[node]['seen'] = {k + 1:False for k in range(items)}
        G.node[node]['current_post'] = 0
        G.node[node]['previously_posted'] = []

    # Generate random posts at nodes
    generators = np.random.choice(G.nodes(), size=items, replace=False)

    for post, node in enumerate(generators):
        G.node[node]['seen'][post + 1] = True
        G.node[node]['current_post'] = post + 1
        G.node[node]['previously_posted'] = [post + 1]

    """
    for node in G.nodes():
        print(node, G.node[node]['seen'], G.node[node]['current_post'],
              G.node[node]['newsfeed'])
    """

    all_seen_all = False
    i = 0
    t0 = time.time()
    while not all_seen_all:

        # For every node
        for node in G.nodes():
            # Check each post that it can see on its newsfeed
            newsfeed = G.node[node]['newsfeed']
            for post in newsfeed:
                # If that post number is 0, ignore it
                if G.node[post]['current_post'] == 0:
                    continue
                # Otherwise
                else:
                    # Update the 'seen' dictionary to reflect that the post
                    # has been seen
                    G.node[node]['seen'][G.node[post]['current_post']] = True

            # When all posts have been scanned, find which one of them to
            # repost
            G.node[node]['current_post'] = find_next_post(G, newsfeed,
                                                G.node[node]['previously_posted'])

            # Add the posted item to the 'previously_posted' list
            G.node[node]['previously_posted'].append(G.node[node]['current_post'])
            #print(node, G.node[node]['seen'], G.node[node]['current_post'],
            #      G.node[node]['newsfeed'])

        # Check stopping criteria
        all_seen_all, perc_complete = check_all_seen(G, items)
        t1 = time.time()
        print("Iteration", i, " complete. Time: " + str(round(t1 - t0,
                0)) + "s.\n")
        print("Percentage complete: " + str(perc_complete) + "%")
        i += 1
        #all_seen_all = True