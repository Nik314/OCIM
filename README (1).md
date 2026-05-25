# OCIM — Object-Centric Inductive Miner

A Python implementation of the **Object-Centric Inductive Miner**, a process discovery algorithm for Object-Centric Event Logs (OCELs). The repository also contains the experimental evaluation framework used to assess the quality of the discovered models, as described in the accompanying paper.

---

## Background

Traditional process mining assumes a single case notion per event. **Object-Centric Process Mining (OCPM)** lifts this restriction: a single event may relate to multiple objects of different types (e.g. orders, items, packages), reflecting how real enterprise systems actually record data.

The **Inductive Miner** is a well-established process discovery algorithm that guarantees sound, block-structured process models. OCIM extends this approach to the object-centric setting, discovering models directly from OCELs without requiring a choice of case notion — accepting both OCEL 1.0 and OCEL 2.0 formats via [pm4py](https://pm4py.fit.fraunhofer.de/).

---

## Repository Structure

```
OCIM/
├── main.py              # Entry point — configure and run experiments
├── src/
│   ├── apply.py         # Core OCIM discovery algorithm
│   └── evaluation_util.py  # Experiment runners and result printers/plotters
├── conformance/         # Conformance-checking utilities (used for quality evaluation)
├── df2miner/            # Directly-follows graph mining helpers
└── results/             # Output directory (created automatically)
```

---

## Requirements

- Python 3.8+
- [pm4py](https://pm4py.fit.fraunhofer.de/) (OCEL 1.0 and 2.0 compatible)

Install dependencies:

```bash
pip install pm4py
```

---

## Usage

1. **Place your OCEL input logs** (JSON-OCEL, XML-OCEL, or SQLite OCEL 2.0) in a directory, e.g. `data/`.

2. **Configure `main.py`** — set `data_directory` and `result_directory`, then uncomment whichever experiments you want to run:

```python
from src import apply, evaluation_util
from src.evaluation_util import check_stats_latex

if __name__ == "__main__":
    data_directory   = "data"    # directory containing your input OCEL logs
    result_directory = "results" # will be created if it does not exist

    # Uncomment to run experiments:
    # evaluation_util.experiment_1_and_2_and_3(data_directory, apply, result_directory)
    # evaluation_util.run_experiment_4("data", "results")
    # evaluation_util.run_experiment_5("data", "results")
    # check_stats_latex("/data")

    # Print/plot results:
    # evaluation_util.print_experiment_1(result_directory)
    # evaluation_util.plot_experiment_2(result_directory)
    evaluation_util.print_experiment_345(result_directory)
```

3. **Run**:

```bash
python main.py
```

> **Note:** Running all experiments (1–5) can take a significant amount of time depending on dataset size.

---

## Experiments

The experiments evaluate the quality of models discovered by OCIM across real-world and synthetic OCEL datasets.

| Function | Description |
|---|---|
| `experiment_1_and_2_and_3` | Core discovery quality evaluation (Experiments 1, 2, and 3 from the paper) |
| `run_experiment_4` | Extended quality evaluation — Experiment 4 |
| `run_experiment_5` | Extended quality evaluation — Experiment 5 |
| `check_stats_latex` | Print dataset statistics formatted for LaTeX |
| `print_experiment_1` | Print tabular results for Experiment 1 |
| `plot_experiment_2` | Plot results for Experiment 2 |
| `print_experiment_345` | Print combined results for Experiments 3, 4, and 5 |

Results are written to `result_directory` and can be printed or plotted with the corresponding utility functions.

---

## Data Format

Input logs must be Object-Centric Event Logs. Both **OCEL 1.0** (JSON/XML) and **OCEL 2.0** (SQLite/XML) are supported through pm4py. Example OCEL datasets are available at [ocel-standard.org](https://www.ocel-standard.org/event-logs/overview/).

---

## Contributing

Pull requests and issues are welcome. Please open an issue first to discuss any significant changes.

---

## License

See [LICENSE](LICENSE) for details.
