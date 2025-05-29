import random
import json
from collections import defaultdict

num_reqs = 120
req_ids = [f"REQ-{str(i).zfill(3)}" for i in range(1, num_reqs + 1)]

nodes = [{"cell_text": req_id, "background_color": "#EBF5FB"} for req_id in req_ids]
id_to_node = {node["cell_text"]: node for node in nodes}
tree = defaultdict(list)

root = "REQ-001"
depth_map = {root: 1}
available_parents = [root]

for req_id in req_ids[1:]:
    while True:
        parent = random.choice(available_parents)
        depth = depth_map[parent]
        if depth < 15:
            break

    id_to_node[req_id]["parent_id"] = parent
    tree[parent].append(req_id)
    depth_map[req_id] = depth + 1

    if random.random() < 0.75:
        available_parents.append(req_id)

nodes_with_parents = list(id_to_node.values())

with open("tree_structure.json", "w", encoding="utf-8") as f:
    json.dump(nodes_with_parents, f, indent=4, ensure_ascii=False)
