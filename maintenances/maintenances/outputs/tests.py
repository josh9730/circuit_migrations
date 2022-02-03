import json
from pprint import pprint
import functools

with open("bgp.json", "r") as f:
    bgp = json.load(f)

with open("comb_dict.json", "r") as f:
    comb_dict = json.load(f)

# with open("isis.json", "r") as f:
#     isis = json.load(f)

# with open("int.json", "r") as f:
#     iface = json.load(f)

bgp_peers = bgp["global"]["peers"]

for i in bgp_peers:
    # get(i) vs i
    # print(bgp_peers.get(i))


"""
- check agains both iBGP and eBGP
- attach to the appropriate interface


- else, put in new dict? 
"""