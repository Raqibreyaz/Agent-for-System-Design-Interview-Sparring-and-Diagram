# System Design Mock Interviewer (AI Agent)

A lightweight, framework-free CLI AI agent that conducts a realistic 20-minute System Design mock interview in the persona of a Staff Backend Engineer. Built directly on top of the OpenAI Chat Completions API (and any OpenAI-compatible endpoint) with custom function calling.

## Features

- **Structured Interview Flow**: Guides candidates through four phases defined in the system prompt ([`conversation.json`](conversation.json)):
  1. **Problem Kickoff** – Clarifies functional requirements, DAU, read/write ratios, and payload sizes.
  2. **Back-of-the-Envelope Estimation** – Delegates capacity math to a deterministic Python tool instead of LLM arithmetic.
  3. **High-Level Design & Evolution** – Tracks infrastructure components and connections as the design evolves.
  4. **Deep-Dive & Trade-Offs** – Probes CAP theorem decisions, bottlenecks, and single points of failure anchored to calculated numbers.
- **Multi-Step Tool-Calling Loop**: Executes up to 5 tool-call iterations per user turn inside [`app.py`](app.py).
- **Deterministic Capacity Estimation (`estimate_capacity`)**: Calculates average and 3x peak read/write QPS, read bandwidth (Mbps), and multi-year storage requirements (TB) from DAU, per-user request counts, payload size, and retention period.
- **Mermaid Architecture Diagramming (`render_architecture`)**: Generates fenced Mermaid `flowchart` diagrams with zero external dependencies, automatically mapping component names to distinct shapes:
  - **Databases / Storage** (`db`, `postgres`, `mysql`, `mongo`, `dynamo`, `s3`, etc.) → Cylinders
  - **Queues / Streams** (`queue`, `kafka`, `rabbitmq`, `sqs`, `event`, `stream`) → Hexagons
  - **Caches** (`cache`, `redis`, `memcached`) → Stadium/pill nodes
  - **Services / Gateways / Clients** → Standard boxes
  - Supports custom layout directions (`LR`, `RL`, `TB`, `BT`), labeled edges, `subgraph` groupings, and optional export to a `.md` file (see [`architecture.md`](architecture.md) for sample output).

## Project Structure

```text
.
├── app.py               # Main CLI chat loop and tool-call dispatcher
├── utils/
│   └── tools.py         # Tool implementations (estimate_capacity, render_architecture) & JSON schemas
├── conversation.json    # System prompt and persisted conversation history
└── architecture.md      # Sample generated Mermaid architecture diagram
```

## Setup & Usage

### 1. Prerequisites

- Python 3.12+
- An OpenAI API key or OpenAI-compatible provider endpoint

### 2. Install Dependencies

Create and activate a virtual environment, then install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install openai python-dotenv
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
BASE_URL=https://api.openai.com/v1
API_KEY=your_api_key_here
MODEL=gpt-4o-mini
```

### 4. Run the Interview Agent

```bash
python app.py
```

Type your responses at the `You: ` prompt. Enter `bye`, `exit`, or `goodbye` to end the session.

### Generating a Standalone Sample Diagram

You can also run [`utils/tools.py`](utils/tools.py) directly to generate a sample Mermaid diagram in [`architecture.md`](architecture.md):

```bash
python -m utils.tools
```
