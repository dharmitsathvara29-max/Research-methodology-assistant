# System Workflow Diagram: Research Methodology Recommendation Assistant

The following Mermaid diagram visualizes the end-to-end 4-stage pipeline, including adversarial input rejection, structured methodology generation, multi-dimensional validation, automated refinement, report delivery, and verifiable execution logging.

```mermaid
flowchart TD
    subgraph STAGE_1["Stage 1: Input Validation & Parsing"]
        A["User Input:<br/>Research Question<br/>Discipline & Constraints<br/>Prompt Strategy (v1/v2/v3)"] --> B{"Input Safety &<br/>Integrity Check"}
        B -->|Prompt Injection /<br/>Gibberish / Malformed| C["Graceful Clarification Guide<br/>(Refusal without crash)"]
        B -->|Genuine Question| D["LLM Question Deconstruction<br/>(Extract Type, Variables, Population, Setting)"]
    end

    subgraph STAGE_2["Stage 2: Methodology Generation"]
        D --> E["Pydantic JSON Generation<br/>(v1_basic / v2_structured / v3_decomposed)"]
        E --> F{"Valid Schema<br/>JSON?"}
        F -->|No| G["Retry 1x with Schema Enforcement"]
        G --> F
        F -->|Yes| H["Validated Methodology Recommendation"]
    end

    subgraph STAGE_3["Stage 3: Multi-Dimensional Validation & Scoring"]
        H --> I["Validation Engine"]
        I --> J["A. LLM-as-Judge 5-Criteria Rubric<br/>(Alignment, Justification, Completeness, Feasibility, Ethics)"]
        I --> K["B. Reference-Based Ground Truth Match<br/>(against data/reference_cases.json)"]
        I --> L["C. Rule-Based Integrity Checks<br/>(Zero fake citations, sample power, paradigm consistency)"]
        J & K & L --> M["Composite Quality Score<br/>PASS (>=75%) | REVIEW (50-74%) | FAIL (<50%)"]
    end

    subgraph STAGE_4["Stage 4: Automated Refinement & Delivery Engine"]
        M --> N{"Composite Score<br/>>= 75% PASS?"}
        N -->|No (Score < 75%)| O["Automated 1-Shot Refinement<br/>(Feedback Evaluator Critique to Stage 2)"]
        O --> I
        N -->|Still < 75% after refinement| P["Status: FLAGGED_FOR_HUMAN_REVIEW<br/>(Review notes attached)"]
        N -->|Yes (PASS)| Q["Status: DELIVERED<br/>(Generate Publication-Grade Report)"]
        
        Q & P --> R["Automated Actions:"]
        R --> S["Generate Markdown & HTML Report<br/>(reports/&lt;timestamp&gt;_methodology_report.md)"]
        R --> T["Append to SQLite Database<br/>(runs, evaluations, execution_log tables)"]
        R --> U["Synchronize CSV Export<br/>(data/results_log.csv)"]
    end

    subgraph INTERFACE["Streamlit Interactive UI (6 Tabs)"]
        S & T & U --> V["Tab 1: Recommend (Form, Cards, Scorecard, Downloads)"]
        S & T & U --> W["Tab 2: Prompt Lab (v1 vs v2 vs v3 Comparison)"]
        S & T & U --> X["Tab 3: Test Results (Automated Suite Evidence)"]
        S & T & U --> Y["Tab 4: Automation Log (Verifiable Trigger Log & Report Viewer)"]
        S & T & U --> Z["Tab 5: History & Data Privacy (Search, Filter, Export, Delete)"]
        S & T & U --> AA["Tab 6: About (Architecture, Rubrics, Responsible AI)"]
    end

    style STAGE_1 fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px;
    style STAGE_2 fill:#F0FDF4,stroke:#22C55E,stroke-width:2px;
    style STAGE_3 fill:#FEFCE8,stroke:#EAB308,stroke-width:2px;
    style STAGE_4 fill:#FAF5FF,stroke:#A855F7,stroke-width:2px;
    style INTERFACE fill:#F8FAFC,stroke:#64748B,stroke-width:1px;
```

