IncidentLens
> AI-powered, evidence-based incident investigation for production-like
> environments.
IncidentLens is an AI-native DevOps project built for the WemakeDevs /
AWS Hackathon -- Build It track.
The goal is simple: when a service starts failing, an engineer should
not have to manually search through disconnected logs, metrics, and
events and then guess the root cause. IncidentLens creates a simulated
production environment, generates telemetry from that environment,
stores the telemetry in OpenSearch, and uses a Strands-based
investigation agent to collect and correlate evidence before producing
an incident analysis.
The core principle of the project is:
Do not ask the LLM to guess what happened. Make the agent investigate
the evidence first.
---
Table of Contents
Project Overview
Problem We Are Solving
What IncidentLens Does
Core Design Principle
Architecture
End-to-End Data Flow
Technology Stack
Project Structure
Component Responsibilities
Simulated Production
Telemetry and OpenSearch
Evidence Collection
Evidence Correlation
Strands Investigation Agent
Local Model
Streamlit UI
Run Isolation and `run\\\_id`
AWS Open-Source Stack Usage
Development Environment
Git and GitHub
Problems We Encountered
Important Lessons From the
Problems
How the Major Problems Were
Addressed
How to Run the Project
Development Workflow
Project Resources
What Makes IncidentLens
Different
Current Scope and Limitations
Future Improvements
Hackathon Context
---
Project Overview
IncidentLens is designed as a small production-like observability and
incident-response system.
Instead of creating a chatbot where a user types:
> "Why is my payment service down?"
and the LLM simply generates a plausible answer, IncidentLens creates an
environment in which the service can actually fail.
The system then:
Simulates a production service.
Generates logs, metrics, and events.
Stores telemetry in OpenSearch.
Gives an investigation agent tools for retrieving telemetry.
Lets the agent investigate the incident.
Correlates the retrieved evidence.
Produces an evidence-backed explanation.
Displays the investigation in a Streamlit UI.
This makes the project an AI investigation workflow, rather than an
LLM wrapper.
---
Problem We Are Solving
Incident investigation is often difficult because operational evidence
is distributed across different sources.
When a service fails, an engineer may need to answer questions such as:
Which service failed?
When did the degradation begin?
Was the service healthy before the incident?
Did latency increase before errors appeared?
Which events happened immediately before the failure?
Are multiple signals pointing to the same cause?
Which services were affected?
What evidence supports the suspected root cause?
Traditional troubleshooting requires manually connecting these signals.
IncidentLens attempts to automate this first layer of investigation.
---
What IncidentLens Does
The current simulated environment focuses on a `payment-api` service.
The simulator can transition the service through states such as:
``` text
HEALTHY
   ↓
DEGRADED
   ↓
FAILING
```
During these transitions it generates production-like telemetry.
Examples include:
log records
metric records
event records
latency measurements
failure signals
recovery/state-transition information
The telemetry is written to:
``` text
incidentlens-telemetry
```
in OpenSearch.
The investigation agent can then retrieve evidence associated with an
incident and reason over it.
---
Core Design Principle
The most important architectural decision in IncidentLens is the
separation between:
Evidence collection and AI reasoning.
The agent does not need to hallucinate operational facts because
operational facts already exist in the telemetry store.
The intended reasoning loop is:
``` text
Question
   ↓
Investigation Agent
   ↓
Evidence Collection Tools
   ↓
OpenSearch
   ↓
Telemetry
   ↓
Evidence Correlation
   ↓
Agent Reasoning
   ↓
Incident Analysis
```
This is fundamentally different from:
``` text
User Question
   ↓
LLM
   ↓
Generated Guess
```
---
Architecture
High-Level Architecture
``` text
┌──────────────────────────────────────────────┐
│              Simulated Production            │
│                                              │
│              payment-api                     │
│                                              │
│       HEALTHY → DEGRADED → FAILING          │
└──────────────────────┬───────────────────────┘
                       │
                       │ logs / metrics / events
                       ▼
┌──────────────────────────────────────────────┐
│               OpenSearch                     │
│                                              │
│          incidentlens-telemetry              │
│                                              │
│      Searchable operational evidence         │
└──────────────────────┬───────────────────────┘
                       │
                       │ evidence queries
                       ▼
┌──────────────────────────────────────────────┐
│          Evidence Collection Layer            │
│                                              │
│             evidence/collector.py            │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          Evidence Correlation Layer           │
│                                              │
│             evidence/correlator.py            │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│             Strands Agent                    │
│                                              │
│             agent/investigator.py            │
│                                              │
│   investigates → gathers → correlates        │
│                 → reasons                    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                Streamlit UI                  │
│                                              │
│        Investigation + Evidence + Result     │
└──────────────────────────────────────────────┘
```
---
End-to-End Data Flow
A typical incident flows through the system like this:
1. Production simulation
The simulator creates a production-like service:
``` text
payment-api
```
The service starts healthy and can transition into degraded and failing
states.
2. Telemetry generation
The simulator produces operational signals such as:
``` text
logs
metrics
events
latency
failures
state transitions
```
3. OpenSearch ingestion
The telemetry is indexed into:
``` text
incidentlens-telemetry
```
4. Incident investigation
The user asks IncidentLens to investigate an incident.
5. Evidence retrieval
The investigation layer searches OpenSearch for relevant records.
6. Evidence correlation
The retrieved records are grouped and interpreted as an incident
timeline.
7. Agent reasoning
The Strands investigation agent uses the collected evidence to determine
what happened.
8. UI presentation
The investigation result is presented together with supporting evidence
rather than only showing a final LLM response.
---
Technology Stack
---
Technology                          Purpose
---
Strands Agents                  Investigation agent and tool-based
agent workflow
Amazon OpenSearch / OpenSearch  Telemetry and evidence
storage/search
Ollama                          Local LLM runtime
Qwen3 4B                        Local model used during development
Streamlit                       User interface
Python                          Main application language
Docker / Docker Compose         Local OpenSearch environment
WSL2 Ubuntu                     Development environment on Windows
Git                             Version control
GitHub                          Remote repository and project
history
AWS open-source stack           Core Build It track technologies
---
Project Structure
The current core project structure is:
``` text
incidentlens/
│
├── agent/
│   └── investigator.py
│
├── evidence/
│   ├── collector.py
│   └── correlator.py
│
├── simulator/
│   └── production.py
│
├── .venv/
│
└── README.md
```
Additional UI/configuration files may exist in the working project
depending on the latest local revision.
The important architectural modules are intentionally separated by
responsibility.
---
Component Responsibilities
`simulator/production.py`
This module represents the simulated production environment.
Its purpose is to create realistic operational conditions without
requiring a real production infrastructure.
It models the `payment-api` service and produces telemetry as the
service changes state.
Conceptually:
``` text
Production Simulator
        │
        ├── logs
        ├── metrics
        ├── events
        └── state transitions
```
The simulator is important because it gives IncidentLens actual evidence
to investigate.
Without it, the project would effectively be a static chatbot
demonstration.
---
`evidence/collector.py`
The collector is responsible for retrieving evidence from OpenSearch.
Its job is not to decide the final root cause.
It focuses on questions such as:
What telemetry exists?
Which records belong to the incident?
What failures occurred?
What was the recent timeline?
What operational signals changed?
This separation makes the system easier to reason about and allows the
agent to use structured evidence.
---
`evidence/correlator.py`
The correlator takes collected signals and organizes them into a
meaningful incident view.
The purpose is to connect individual telemetry records.
For example:
``` text
Latency increases
       ↓
Service becomes degraded
       ↓
Errors increase
       ↓
Payment requests fail
       ↓
Service enters failing state
```
Instead of treating each record independently, the correlation layer
helps turn telemetry into an incident story.
---
`agent/investigator.py`
This is the core AI investigation layer.
The Strands agent is responsible for performing an investigation rather
than simply generating an answer.
The agent can use tools to access evidence and then reason over the
returned information.
Conceptually:
``` text
User request
     ↓
Investigator
     ↓
Call evidence tools
     ↓
Retrieve telemetry
     ↓
Correlate evidence
     ↓
Reason about incident
     ↓
Generate investigation
```
---
Simulated Production
One of the most important parts of IncidentLens is that the project does
not depend on a static dataset.
The simulated environment produces dynamic telemetry.
The current simulated service is:
``` text
payment-api
```
Its state progression is approximately:
``` text
healthy
   ↓
degraded
   ↓
failing
```
The generated telemetry includes operational information such as latency
and failure signals.
For example, during a failure run, latency can rise substantially before
or around the time failures appear.
This provides the investigation agent with temporal evidence rather than
a single pre-written incident description.
---
Telemetry and OpenSearch
OpenSearch is the operational evidence layer.
The primary telemetry index is:
``` text
incidentlens-telemetry
```
The OpenSearch instance used during development runs locally through
Docker.
The project previously used a Compose configuration with:
``` text
OpenSearch image:
opensearchproject/opensearch:3.8.0

Container:
incidentlens-opensearch

Port:
9200

Additional OpenSearch performance/monitoring port:
9600
```
The OpenSearch cluster was verified during development and reported
version:
``` text
3.8.0
```
The basic relationship is:
``` text
Simulator
    ↓
Telemetry records
    ↓
OpenSearch
    ↓
Search
    ↓
Evidence
```
OpenSearch is therefore not being used as a decorative AWS technology.
It is part of the actual investigation workflow.
---
Evidence Collection
The collector provides the bridge between raw telemetry and the
investigation agent.
Instead of exposing the entire database to the model, the system can
provide focused evidence retrieval.
This creates a more controlled architecture:
``` text
Agent
  ↓
Tool
  ↓
Collector
  ↓
OpenSearch query
  ↓
Relevant evidence
```
This is important for both performance and reliability.
---
Evidence Correlation
Raw telemetry is not automatically an explanation.
For example:
``` text
Record A:
latency = high

Record B:
service = degraded

Record C:
error = payment request failure

Record D:
service = failing
```
Individually these are just records.
Correlation turns them into:
``` text
High latency appeared
        ↓
Service degraded
        ↓
Payment failures increased
        ↓
Service entered failing state
```
That timeline gives the AI useful context for reasoning.
---
Strands Investigation Agent
Strands Agents is the main AWS open-source AI framework used by
IncidentLens.
The agent is designed around tool usage.
Instead of:
``` text
Prompt → LLM → Answer
```
the intended flow is:
``` text
Prompt
  ↓
Strands Agent
  ↓
Choose investigation tool
  ↓
Retrieve evidence
  ↓
Inspect result
  ↓
Call additional tools if required
  ↓
Correlate evidence
  ↓
Final investigation
```
This is one of the key reasons Strands was selected for the project.
It allows the AI component to participate in an actual operational
workflow.
---
Local Model
During development, IncidentLens was tested with Ollama and the
local:
``` text
qwen3:4b
```
model.
An earlier experiment used:
``` text
qwen3:8b
```
but the 8B model was slower and placed more load on the development
machine.
The 4B model was selected for the local development workflow because it
provided a better speed/resource tradeoff for the available machine.
This allowed the project to develop and test the agent workflow without
making the entire development process dependent on a remote model API.
---
Streamlit UI
Streamlit provides the application interface.
The UI is designed around the investigation workflow rather than around
a generic chat interface.
The intended user journey is:
``` text
Open IncidentLens
      ↓
View production/incident context
      ↓
Ask for investigation
      ↓
Agent investigates
      ↓
Evidence is displayed
      ↓
Investigation result is displayed
```
The UI is particularly important because the project is intended to
demonstrate that the agent is actually using evidence.
The result should therefore communicate both:
what the agent concluded
why it reached that conclusion
---
Run Isolation and `run\\\_id`
One of the most important engineering issues discovered during
development was historical telemetry mixing.
Because the same OpenSearch index was reused across simulator
executions, a new investigation could accidentally retrieve records from
earlier runs.
For example:
``` text
Run A
  └── old failure telemetry

Run B
  └── new failure telemetry

        ↓

Same OpenSearch index
        ↓

Collector query
        ↓

Potentially mixed evidence
```
This is dangerous for an incident investigation system because an AI
agent could produce a technically plausible explanation based on the
wrong incident.
The solution is to associate telemetry with a unique execution
identifier:
``` text
run\\\_id
```
Conceptually:
``` text
Run 001
  ├── telemetry
  ├── telemetry
  └── telemetry

Run 002
  ├── telemetry
  ├── telemetry
  └── telemetry
```
The collector can then isolate the relevant execution instead of
searching all historical telemetry indiscriminately.
This is a major reliability improvement because correct evidence
selection is more important than sophisticated LLM reasoning.
---
AWS Open-Source Stack Usage
The project was built for the AWS Build It track.
The main AWS open-source technologies used are:
Strands Agents
Used for:
AI investigation
tool calling
evidence retrieval workflow
reasoning over collected telemetry
OpenSearch
Used for:
telemetry storage
operational evidence search
incident timeline retrieval
querying logs, metrics, and events
The project intentionally makes these technologies part of the core
application architecture rather than merely mentioning them in the
documentation.
---
Development Environment
The project was developed on:
``` text
Windows 11
    ↓
WSL2
    ↓
Ubuntu
```
Docker Desktop was used to provide the Docker environment.
The project uses Python virtual environments:
``` text
.venv
```
The project repository is:
``` text
\\\~/incidentlens
```
OpenSearch development configuration was maintained separately during
setup in:
``` text
\\\~/opensearch-test
```
This separation was useful during the initial infrastructure testing
phase.
---
Local OpenSearch Resource
The local OpenSearch development environment was built using Docker
Compose.
The important resource was:
``` text
\\\~/opensearch-test/compose.yaml
```
The resulting Docker container was:
``` text
incidentlens-opensearch
```
OpenSearch was exposed locally on:
``` text
localhost:9200
```
This allowed the Python application to communicate with OpenSearch
during development.
---
Git and GitHub
Git was used throughout development to maintain the project history.
The repository was initialized locally and the primary branch was
changed to:
``` text
main
```
The project was connected to GitHub and the local branch was
synchronized with the remote repository.
The `.venv` directory was explicitly kept out of version control.
This is important because virtual environments contain machine-specific
dependencies and should not be committed to the repository.
The general workflow followed was:
``` text
Make a project change
      ↓
Test it
      ↓
Review git diff/status
      ↓
Commit
      ↓
Push to GitHub
```
Regular commits were intentionally part of the project workflow.
---
Problems We Encountered
Building IncidentLens in a short hackathon window exposed several real
engineering problems.
These problems were valuable because they were not just syntax errors;
they affected the architecture and reliability of the system.
---
1. Historical Telemetry Mixing
Problem
The simulator repeatedly wrote telemetry to the same OpenSearch index.
When the collector queried the index, it could return evidence from
multiple simulator executions.
This produced results containing:
older failures
older high-latency records
timeline entries from previous runs
current incident records
Why It Was Serious
An incident investigation system must investigate the correct incident.
If historical records are mixed with the current incident, the AI can
form a convincing but incorrect explanation.
Lesson
Observability systems need explicit identity and scope.
A record should not only answer:
``` text
What happened?
```
It should also answer:
``` text
Which execution/incident did this belong to?
```
That led to the use of:
``` text
run\\\_id
```
for run-level isolation.
---
2. Connecting AI Reasoning to Real Data
Problem
It is relatively easy to build:
``` text
User prompt
    ↓
LLM
    ↓
Answer
```
But that does not create a meaningful incident investigation system.
The harder problem was making the agent actually interact with
operational data.
Why It Was Difficult
The system needed to coordinate:
``` text
Simulator
    ↓
OpenSearch
    ↓
Collector
    ↓
Agent tools
    ↓
Strands
    ↓
Investigation
```
Every layer had to agree on the data being produced and consumed.
Lesson
The quality of an AI operations system depends heavily on the quality
and accessibility of its tools and evidence.
---
3. Designing Evidence Instead of Just Returning Raw Logs
Problem
Returning hundreds of raw telemetry records to an LLM is not useful.
The agent needs meaningful evidence.
Solution Direction
The project separated:
``` text
collection
```
from:
``` text
correlation
```
The collector retrieves records.
The correlator organizes them into an incident-oriented view.
The agent then reasons over that evidence.
Lesson
Good agent architecture is not just about choosing a model.
It is about designing the tools and intermediate representations that
the model uses.
---
4. Local Model Performance
Problem
The initial local model experiment used:
``` text
qwen3:8b
```
It was slower and caused noticeably higher system load during
development.
Solution
A smaller:
``` text
qwen3:4b
```
model was tested and used for the local development workflow.
Lesson
For an agentic application, model size is only one consideration.
Tool latency, reasoning quality, hardware constraints, and iteration
speed all matter.
During a hackathon, fast feedback can be more valuable than using the
largest available model.
---
5. Docker / WSL Environment Issues
The development environment depended on the interaction between:
``` text
Windows
WSL2
Ubuntu
Docker Desktop
Docker daemon
```
This created environment-level troubleshooting during development.
Docker and WSL connectivity had to be verified before OpenSearch could
reliably run.
At one point, the WSL/Docker environment required recovery after a
disk-sharing-related issue.
Lesson
For local AI/DevOps projects, the development environment itself becomes
part of the engineering problem.
A service such as OpenSearch can be perfectly configured while still
being unavailable because the underlying container runtime is not
healthy.
---
6. OpenSearch Availability
OpenSearch had to be running before the application could query:
``` text
localhost:9200
```
When the container was stopped, requests naturally failed.
The fix was to start the Compose environment again and verify the
cluster before running the application.
Lesson
Application-level debugging should always distinguish:
``` text
Application problem
```
from:
``` text
Dependency unavailable
```
This saved time during troubleshooting.
---
7. Understanding the AWS Stack While Building
Another challenge was learning multiple technologies simultaneously:
Strands Agents
OpenSearch
agent tool calling
local models
Docker
Streamlit
Python
simulated production
Git/GitHub
The project was therefore intentionally built incrementally.
Each layer was tested before being connected to the next.
The resulting progression was approximately:
``` text
Python
  ↓
Ollama + local model
  ↓
Strands agent
  ↓
OpenSearch
  ↓
Telemetry simulator
  ↓
Evidence collector
  ↓
Evidence correlator
  ↓
Agent investigation
  ↓
Streamlit UI
```
---
Important Lessons From the Problems
The biggest lessons from IncidentLens were architectural rather than
syntactic.
1. Evidence comes before reasoning
An AI agent is only as reliable as the evidence it receives.
2. Data isolation matters
Historical data must not accidentally become current incident evidence.
3. Tool design matters
Giving an agent a useful search/investigation tool is more valuable than
simply giving it access to a huge raw dataset.
4. Simulation is useful
A simulated production environment makes it possible to test an
incident-response system repeatedly without needing a real production
outage.
5. Local development exposes real engineering problems
Docker, networking, OpenSearch availability, model performance, and data
lifecycle all became practical engineering concerns.
6. AI does not replace system design
The LLM is only one component.
The overall system is:
``` text
Production simulation
+
Telemetry
+
Search
+
Evidence collection
+
Correlation
+
Agent reasoning
+
UI
```
---
How the Major Problems Were Addressed
---
Problem                             Approach
---
Historical telemetry mixing         Introduced per-run `run\\\_id`
isolation
Raw telemetry difficult to reason   Added evidence collection and
over                                correlation layers
LLM could otherwise guess           Agent retrieves actual OpenSearch
evidence
Large local model too slow          Moved development workflow to Qwen3
4B
OpenSearch unavailable              Verified Docker container and
cluster health before investigation
Complex multi-service setup         Built and tested components
incrementally
Virtual environment pollution       Kept `.venv` out of Git
Agent/application integration       Separated simulator, evidence, and
complexity                          agent responsibilities
---
How to Run the Project
The exact commands can evolve as the project changes, but the
development environment follows this general order.
1. Enter the repository
``` bash
cd \\\~/incidentlens
```
2. Activate the Python environment
``` bash
source .venv/bin/activate
```
3. Make sure Docker is available
``` bash
docker ps
```
4. Start OpenSearch
From the OpenSearch development directory:
``` bash
cd \\\~/opensearch-test
docker compose up -d
```
Verify that OpenSearch is reachable:
``` bash
curl http://localhost:9200
```
Then return to the project:
``` bash
cd \\\~/incidentlens
```
5. Start the application components
Run the simulator, investigation workflow, and Streamlit interface
according to the current application entry points in the repository.
The important dependency order is:
``` text
Docker / OpenSearch
        ↓
Telemetry
        ↓
Evidence
        ↓
Investigation Agent
        ↓
Streamlit UI
```
---
Development Workflow
The project was developed incrementally rather than attempting to build
everything simultaneously.
A simplified development progression was:
Phase 1 --- Environment
``` text
WSL2
Docker
Python
Git
```
Phase 2 --- Local AI
``` text
Ollama
Qwen3
```
Phase 3 --- Agent
``` text
Strands Agents
Tool calling
```
Phase 4 --- Search and Evidence
``` text
OpenSearch
Telemetry index
Queries
```
Phase 5 --- Production Simulation
``` text
payment-api
Telemetry generation
Failure states
```
Phase 6 --- Investigation
``` text
Collector
Correlator
Investigator
```
Phase 7 --- UI
``` text
Streamlit
Evidence display
Investigation results
```
Phase 8 --- Reliability
``` text
run\\\_id
Historical-data isolation
Testing
```
Phase 9 --- Submission
``` text
README
Demo
GitHub
Hackathon submission
```
---
Project Resources
This section maps the major resources used by IncidentLens to their
roles.
---
Resource                Location / Identifier              Purpose
---
IncidentLens repository `\\\~/incidentlens`                   Main application
Git repository          `\\\~/incidentlens/.git`              Version history
Python environment      `\\\~/incidentlens/.venv`             Isolated dependencies
Investigator            `agent/investigator.py`            Strands investigation logic
Evidence collector      `evidence/collector.py`            Retrieves operational evidence
Evidence correlator     `evidence/correlator.py`           Correlates telemetry
Production simulator    `simulator/production.py`          Generates simulated production
telemetry
OpenSearch setup        `\\\~/opensearch-test`                Local OpenSearch environment
Docker Compose          `\\\~/opensearch-test/compose.yaml`   Defines local OpenSearch
OpenSearch container    `incidentlens-opensearch`          Running search backend
OpenSearch endpoint     `localhost:9200`                   Local API endpoint
OpenSearch version      `3.8.0`                            Development version
Telemetry index         `incidentlens-telemetry`           Stores operational telemetry
Local model runtime     Ollama                             Local LLM serving
Local model             `qwen3:4b`                         Development model
UI                      Streamlit                          Incident investigation interface
OS environment          WSL2 Ubuntu                        Main development environment
Container runtime       Docker Desktop                     Runs OpenSearch
Version control         Git                                Source control
Remote repository       GitHub                             Collaboration/storage/submission
---
Resource Relationships
The resources can be understood as one dependency graph:
``` text
Windows 11
   │
   └── WSL2 Ubuntu
          │
          ├── Git
          │     └── GitHub
          │
          ├── Python / .venv
          │     │
          │     ├── Strands
          │     ├── OpenSearch client
          │     └── Streamlit
          │
          ├── Ollama
          │     └── Qwen3 4B
          │
          └── Docker
                │
                └── OpenSearch
                      │
                      └── incidentlens-telemetry
```
The application sits above these infrastructure components:
``` text
                  IncidentLens
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Simulator      Evidence       Agent
        │              │              │
        │         Collector +     Strands
        │         Correlator         │
        │              │              │
        └──────────────┴──────┬───────┘
                              │
                         OpenSearch
                              │
                   incidentlens-telemetry
                              │
                           Docker
```
---
What Makes IncidentLens Different
IncidentLens is not intended to be:
``` text
ChatGPT for DevOps
```
It is also not simply:
``` text
LLM + textbox
```
The distinguishing workflow is:
``` text
Simulated production
       ↓
Dynamic telemetry
       ↓
Searchable evidence
       ↓
Agent investigation
       ↓
Evidence correlation
       ↓
Root-cause analysis
```
The agent is expected to investigate the environment before explaining
the incident.
That makes the project closer to an AI-assisted incident-response
workflow than a conventional conversational application.
---
Current Scope and Limitations
IncidentLens is a hackathon-scale prototype.
The current system uses a simulated production environment rather than
connecting to a real organization's production infrastructure.
The primary simulated service is:
``` text
payment-api
```
The current telemetry and investigation workflow is designed to
demonstrate the architecture and core concept rather than provide a
complete enterprise observability platform.
The local development model is also selected primarily for practical
development speed and resource constraints.
---
Future Improvements
Potential next steps include:
Support for multiple simulated services.
Dependency-aware service graphs.
More sophisticated incident correlation.
More telemetry types.
Stronger temporal reasoning.
Persistent incident records.
Automated incident severity classification.
Suggested remediation actions.
Human approval before remediation.
Production observability integrations.
Better visualization of incident timelines.
More robust evaluation datasets.
More comprehensive automated tests.
Deployment of the complete workflow to AWS infrastructure.
---
Hackathon Context
IncidentLens was built for the WemakeDevs / AWS Hackathon with the
Build It track as the primary target.
The project focuses on the AWS open-source stack and specifically
demonstrates the use of:
Strands Agents
OpenSearch
The project was designed around a real DevOps problem:
> How can an AI agent help an engineer investigate a production incident
> using actual operational evidence?
The answer implemented by IncidentLens is:
``` text
Generate production-like telemetry
            ↓
Store it in OpenSearch
            ↓
Give the agent investigation tools
            ↓
Retrieve relevant evidence
            ↓
Correlate the evidence
            ↓
Reason over the evidence
            ↓
Explain the incident
```
---
Final Architecture Summary
At its core, IncidentLens follows this architecture:
``` text
                     ┌─────────────────────┐
                     │  Simulated          │
                     │  Production         │
                     │                     │
                     │  payment-api        │
                     └──────────┬──────────┘
                                │
                     logs / metrics / events
                                │
                                ▼
                     ┌─────────────────────┐
                     │     OpenSearch      │
                     │                     │
                     │ incidentlens-       │
                     │ telemetry           │
                     └──────────┬──────────┘
                                │
                                │ queries
                                ▼
                     ┌─────────────────────┐
                     │ Evidence Collector  │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ Evidence Correlator │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   Strands Agent     │
                     │                     │
                     │ Investigate         │
                     │ Gather evidence     │
                     │ Correlate           │
                     │ Reason              │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │    Streamlit UI     │
                     │                     │
                     │ Evidence + Analysis │
                     └─────────────────────┘
```
The core idea
IncidentLens does not ask AI to guess the incident.
It gives AI the tools to investigate the evidence.
That is the central idea behind the architecture, the reason for using
Strands Agents and OpenSearch together, and the foundation of the
project.
