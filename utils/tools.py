from typing import Dict, Iterable, Mapping, Optional, Tuple, Union

def estimate_capacity(
    dau: int, 
    reads_per_user: int, 
    writes_per_user: int, 
    payload_kb: float, 
    retention_years: int = 5
):
    """
    Purpose: When you propose a system (like a URL shortener or distributed rate limiter), the agent calls this Python function to compute exact QPS (Queries Per Second), peak QPS ($2\times$ to $3\times$ average), and 5-year(default) storage requirements, then uses those numbers to grill you on database bottlenecks.
    """
    read_qps = round(dau * reads_per_user / 86400)
    write_qps = round(dau * writes_per_user / 86400)
    peak_read_qps = read_qps * 3
    peak_write_qps = write_qps * 3
    read_bandwidth = round(read_qps * payload_kb / 1024)
    write_bandwidth = round(write_qps * payload_kb / 1024)
    daily_storage = round(write_bandwidth * 86400 / 1024)
    total_storage = round(daily_storage * 365 * retention_years / 1024)
    
    result = {
        "read_qps": read_qps, 
        "write_qps": write_qps, 
        "peak_read_qps": peak_read_qps,
        "peak_write_qps": peak_write_qps,
        "read_bandwidth_mbps": read_bandwidth, 
        "total_storage_tb": total_storage,
    }
    
    if read_qps / write_qps >= 10:
        result.update(["read_heavy", True])  
    if total_storage > 10:
        result.update(["requires_sharding_or_partitioning", True])

    return result

def _format_node(node_id: str, label: str) -> str:
    lower = label.lower()
    safe = label.replace('"', "'")

    if any(k in lower for k in ("db", "database", "postgres", "mysql", "mongo", "dynamo", "s3", "storage")):
        return f'{node_id}[("{safe}")]'   # Cylinder
    if any(k in lower for k in ("queue", "kafka", "rabbitmq", "sqs", "event", "stream")):
        return f'{node_id}{{{{"{safe}"}}}}'  # Hexagon
    if any(k in lower for k in ("cache", "redis", "memcached")):
        return f'{node_id}(["{safe}"])'   # Stadium/pill
    return f'{node_id}["{safe}"]'          # Box

Edge = Union[Tuple[str, str], Tuple[str, str, str]]

def render_architecture(
    connections: Iterable[Edge],
    direction: str = "LR",
    groups: Optional[Mapping[str, Iterable[str]]] = None,
    output_file: Optional[str] = None,
) -> str:
    """
    Generates a Markdown-ready Mermaid diagram string, saves in the provided filename as well as returns it, with zero external dependencies.

    Args:
        connections: Iterable of (source, target) or (source, target, label) tuples.
        direction: 'LR' (left-to-right) or 'TB' (top-to-bottom).
        groups: Optional dict mapping boundary/group titles to lists of node names.
        output_file: Optional '.md' path to write the output directly.

    Returns:
        A fenced Markdown string ready to paste or save.
    """
    edge_list = list(connections)
    groups = groups or {}

    node_ids: Dict[str, str] = {}
    for edge in edge_list:
        for name in (edge[0], edge[1]):
            if name not in node_ids:
                node_ids[name] = f"N{len(node_ids)}"
    for members in groups.values():
        for name in members:
            if name not in node_ids:
                node_ids[name] = f"N{len(node_ids)}"

    lines = ["```mermaid", f"flowchart {direction}"]
    grouped = set()

    for idx, (group_name, members) in enumerate(groups.items()):
        safe_group = group_name.replace('"', "'")
        lines.append(f'    subgraph G{idx}["{safe_group}"]')
        for name in members:
            lines.append(f"        {_format_node(node_ids[name], name)}")
            grouped.add(name)
        lines.append("    end")

    for name, nid in node_ids.items():
        if name not in grouped:
            lines.append(f"    {_format_node(nid, name)}")

    for edge in edge_list:
        src, dst = node_ids[edge[0]], node_ids[edge[1]]
        if len(edge) >= 3 and edge[2]:
            label = edge[2].replace('"', "'")
            lines.append(f'    {src} -->|"{label}"| {dst}')
        else:
            lines.append(f"    {src} --> {dst}")

    lines.append("```")
    markdown = "\n".join(lines)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown + "\n")

    return markdown

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "estimate_capacity",
            "description": """
                - WHEN TO CALL: Whenever the candidate provides or updates DAU, read/write counts, or payload sizes.
                - HARD RULE: Never perform QPS, bandwidth, or storage arithmetic yourself. Always delegate calculations to this tool.
                """,
            "parameters": {
                "type": "object",
                "properties":{
                    "dau": {
                        "type": "integer",
                        "description": "Daily active users count"
                    },
                    "reads_per_user": {
                        "type": "integer",
                        "description": "Max Read requests a user will do in a day"
                    },
                    "writes_per_user": {
                        "type": "integer",
                        "description": "Max Write requests a user will do in a day"
                    },
                    "payload_kb": {
                        "type": "float",
                        "description": "Max Payload size in KB a user will read/write"
                    },
                    "retention_years": {
                        "type": "integer",
                        "description": "Retention Time in years to remove the data after this specific age"
                    },
                    
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "render_architecture",
            "description": """
                - WHEN TO CALL: Every time the candidate adds, removes, or connects infrastructure components.
                - HARD RULE: Always pass the COMPLETE list of current components and connections accumulated across the entire conversation so far—never pass only the newest delta.
                """,
            "parameters": {
                "type": "object",
                "properties":{
                    "connections": {
                        "type": "array",
                        "description": "Edges connecting components in the architecture.",
                        "items": {
                            "oneOf": [
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "minItems": 2,
                                    "maxItems": 2
                                },
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "minItems": 3,
                                    "maxItems": 3
                                }
                            ]
                        }
                    },
                    "direction": {
                        "type": "string",
                        "description": "Diagram layout direction.",
                        "enum": ["LR", "RL", "TB", "BT"],
                        "default": "LR"
                    },
                    "groups": {
                        "type": ["object", "null"],
                        "description": "Optional grouping of nodes",
                        "additionalProperties": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "output_file": {
                        "type": ["string", "null"],
                        "description": "Optional Path where the Diagram should be saved."
                    }            
                },
                "required": ["connections"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

FUNCTION_NAME_TO_FUNCTION_MAP = {
    "estimate_capacity": estimate_capacity,
    "render_architectre": render_architecture
}


if __name__ == "__main__":
    edges = [
         ["Client", "API Gateway", "HTTPS"],
         ["API Gateway", "Auth Service"],
         ["API Gateway", "Order Service"],
         ["Order Service", "Postgres DB", "SQL"],
         ["Order Service", "Kafka Queue", "Publish"],
    ]
    render_architecture(edges, output_file="architecture.md")