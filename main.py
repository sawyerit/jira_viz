import jira
from pyvis.network import Network
import networkx as nx

color_dict = {
    "PRO": "blue",
    "JOBS": "green",
    "JS": "purple",
    "PDA": "orange",
    "DATA": "brown",
    "MOFO": "pink",
    "BRAND": "yellow",
    "IDT": "gold",
    "DCOM": "red"
}

# Connect to Jira using the Jira Python API
jira_instance = jira.JIRA(server="https://dhi-jira.atlassian.net", basic_auth=("username", "key"))


def set_color(issue):
    if issue.fields.status.name in ["Done", "Closed", "Resolved", "Released"]:
        return "lightgray"
    else:
        proj_id = issue.key.split("-")[0]
        return None if proj_id not in color_dict.keys() else color_dict[issue.key.split("-")[0]]

def set_shape(issue):
    type = issue.fields.issuetype.name 
    match type:
        case "Initiative":
            return "diamond"
        case "Epic":
            return "square"
        case _:
            return "dot"

def build_graph(issues, parent_key):
    dashes = False
    color = "purple"
    weight = 1
    for issue in issues:
        if "DHISD" in issue.key or (issue.fields.resolution and issue.fields.resolution.name == "Won't Do"):
            continue
        #add the nodes and edge to the parent
        matching_node = [obj for obj in net.nodes if obj['id'] == issue.key]
        color = set_color(issue)
        if not matching_node:
            net.add_node(issue.key, label=f'{issue.key} - {issue.fields.summary}', shape=set_shape(issue), color=color)
        net.add_edge(parent_key, issue.key, weight=1, color=color)

        for link in issue.fields.issuelinks:
            # color = "purple"
            weight = 1
            if link.type.name not in ["Change Request", "Cloners","Relates","Related"]: # skip clones and change requests
                # dashes = link.type.name in ["Relates","Related"]
                if link.type.name in ["Blocks"]:
                    color = "red"
                    weight = 3
                # if "Dependency" in link.type.name:
                #     color = "purple" # dependency is gray, blocks are red, related are dashes
                #     weight = 3
                if hasattr(link, "outwardIssue") and "DHISD" not in link.outwardIssue.key:
                    net.add_node(link.outwardIssue.key, label=f'{link.outwardIssue.key} - {link.outwardIssue.fields.summary}', shape=set_shape(link.outwardIssue), color=set_color(link.outwardIssue))
                    net.add_edge(issue.key, link.outwardIssue.key, dashes=True, color=color, weight=weight)
                # elif hasattr(link, "inwardIssue") and "DHISD" not in link.inwardIssue.key:
                #     net.add_node(link.inwardIssue.key, label=f'{link.inwardIssue.key} - {link.inwardIssue.fields.summary}', shape=set_shape(link.inwardIssue), color=set_color(link.inwardIssue))
                #     net.add_edge(issue.key, link.inwardIssue.key, color=color, weight=weight)
        
        #get children to create edges/nodes
        #TODO: not working? Removes all data epics??
        # if issue.fields.issuetype.name == "Epic" and issue.fields.status.name == "Done":
        #     continue;
        if not issue.fields.issuetype.name in ["Bug", "Story", "Spike / Task", "Change Request"] and not (issue.fields.issuetype.name == "Epic" and issue.fields.status.name == "Done"):
            child_issues = jira_instance.search_issues('"Parent Link" = ' + issue.key, maxResults=75)
            if len(child_issues) > 0:
                build_graph(child_issues, issue.key)


G = nx.Graph()
base_ticket = "PROG-2"
issues = jira_instance.search_issues(f'"Parent Link" = {base_ticket}', maxResults=20) # Fetch all the issues in Jira
net = Network(notebook=False, directed=True, height="800px", select_menu=True) # Initialize the network
net.add_node(base_ticket, label=base_ticket, shape="star", size=40)

build_graph(issues, base_ticket)


# Show the network
# net.show_buttons(filter_=['nodes'])
net.set_options("""
const options = {
  "interaction": {
    "hover": true
  }
}
""")

# even tho notebook is false on the net definition, it needs to be set again here
net.write_html("jira_issues.html",notebook=False)

## Todo: explore D3 rather than pyvis, its much more customizable