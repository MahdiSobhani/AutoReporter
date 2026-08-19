# AutoReporter
## Features

### Database Metadata

AutoReporter analyzes database-level and table-level metadata, including:

- Number of tables
- Number of columns
- Number of records
- Database size
- Table size
- NULL value statistics
- Unique value statistics
- Column-level information
- Other database profiling information

---

### Algorithm Detection

AutoReporter detects the following **16 data patterns / algorithms**:

| # | Algorithm |
|---|---|
| 1 | National Code |
| 2 | National ID |
| 3 | ZIP Code |
| 4 | Foreign Code |
| 5 | Mobile Number |
| 6 | Home Telephone |
| 7 | Bank Code (Sheba) |
| 8 | ID Card (National Code Serial) |
| 9 | License Plate |
| 10 | Job |
| 11 | First Name / Last Name |
| 12 | Family Relationship |
| 13 | Car Name |
| 14 | Color |
| 15 | Date Detection |
| 16 | Latitude / Longitude |

---

### ERD Generation

AutoReporter can automatically analyze the database structure and generate an **Entity-Relationship Diagram (ERD)** using **Graphviz**.

The ERD provides a visual representation of:

- Database tables
- Table columns
- Potential relationships between tables
- Connections between related columns

This feature is particularly useful for databases where relationships are not fully documented or where an existing database structure needs to be reverse-engineered.

The generated graph can be used as a visual representation of the database structure and its inferred relationships.

---

### Geographic Analysis

AutoReporter performs geographic analysis based on detected:

- National Codes
- ZIP Codes
- Latitude / Longitude coordinates

It calculates city frequency distributions and provides geographic insights into the analyzed data.

---

### National Code & Birth Date Detection

The system can identify columns that potentially represent:

- National Code
- Birth Date

It then analyzes the relationship between these columns to determine whether they correspond to the expected National Code / Birth Date pattern.

---

### Database Data Quality Analysis

AutoReporter calculates information related to data availability and completeness.

For example, it can identify the number of:

- National Codes that are not available in the reference data source
- ZIP Codes that are not available in the reference data source
- National IDs that are not available in the reference data source

---

## Technologies

The project is implemented using Python and the following technologies:

- **Python**
- **Pandas** — Data processing and analysis
- **SQLAlchemy** — Database connectivity
- **SciPy** — Scientific and spatial calculations
- **ThreadPoolExecutor** — Parallel processing
- **ReportLab** — PDF report generation
- **Graphviz** — ERD generation and database relationship visualization

---

## Output

AutoReporter produces analysis results and visual documentation of the target database.

### PDF Report

The main output is a comprehensive **PDF report** containing:

- Database metadata
- Database size
- Number of tables
- Detected algorithms
- Data quality statistics
- Geographic analysis
- Reference data validation
- Database-specific information

### ERD

The project also generates an **Entity-Relationship Diagram (ERD)** using Graphviz.

The ERD visualizes the database structure and detected/inferred relationships between tables and columns.

Therefore, the final outputs can be summarized as:

```text
SQL Server Database
        │
        ├──────────────► PDF Report
        │
        └──────────────► ERD / Graph Visualization
```

---

## Project Workflow

The overall workflow can be summarized as:

```text
                 SQL Server Database
                         │
                         ▼
                 Database Metadata
                         │
                         ▼
               Column / Data Analysis
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Algorithm Detection      ERD Analysis
              │                     │
              ▼                     ▼
       Data Quality          Relationship Graph
              │                     │
              └──────────┬──────────┘
                         ▼
                  Geographic Analysis
                         │
                         ▼
                    PDF Report
```

---

## Use Cases

AutoReporter can be useful for:

- Database profiling
- Data discovery
- Data quality assessment
- Legacy database analysis
- Database reverse engineering
- ERD generation
- Identifying sensitive or important data patterns
- Database documentation
- Data migration preparation
- Data governance
- Data engineering workflows
