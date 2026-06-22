[README.md](https://github.com/user-attachments/files/29208004/README.md)
# Platcon-25# Virtual Experts to Collective Decisions: An LLM-Driven Majority Voting for EM

Code and data for the paper **"Virtual Experts to Collective Decisions: An LLM-Driven Majority Voting for EM"** (Euijin Kim, Taeyoung Choe, Mucheol Kim — Chung-Ang University).

The paper is included in [`paper/Platcon_Final.pdf`](paper/Platcon_Final.pdf).

## Overview

Entity Matching (EM) is the task of deciding whether two records from different
sources refer to the same real-world entity. This project explores a **committee
prompting** scheme for EM: a single GPT model is instructed to simulate three
independent reviewers (Expert A, B, C). Each expert reads the same record pair in
isolation and produces a one-sentence rationale plus a binary `YES`/`NO` vote. A
deterministic majority rule then aggregates the votes — if at least two experts
vote `YES`, the final decision is `YES`, otherwise `NO`.

The output schema is fixed (uppercase labels, fixed field names) so it can be
parsed programmatically with a simple regex, which keeps the method easy to drop
into automated EM pipelines.

## Results

Experiments use 1,000 randomly sampled instances from the **Amazon-Google** and
**DBLP-Scholar** subsets of the ER_Magellan benchmark. With the voting prompt the
paper reports:

| Dataset        | F1-score |
| -------------- | -------- |
| DBLP-Scholar   | 0.970    |
| Amazon-Google  | 0.692    |

This corresponds to roughly a 2-percentage-point accuracy improvement in the
academic/library domain over prior zero-shot prompting.

> Note: the JSON files in `data/processed/` are 100-row samples used for quick
> reproduction; the full 1,000-instance runs reported in the paper draw from the
> same ER_Magellan subsets.

## Repository layout

```
.
├── paper/
│   └── Platcon_Final.pdf                      # final paper
├── src/
│   ├── build_test_data.py                     # raw ER_Magellan txt -> test_data JSON
│   └── run_em_voting.py                        # committee-voting EM experiment
├── data/
│   ├── raw/                                    # raw ER_Magellan records (COL/VAL format)
│   │   ├── raw_em(Amazon_Google_Structured).txt
│   │   └── raw_em(DBLP_Scholar_Structured).txt
│   └── processed/                              # parsed entity pairs + gold labels
│       ├── test_data(Amazon_Google_Structured).json
│       └── test_data(DBLP_Scholar_Structered).json
├── results/
│   └── em_vote_results.csv                      # sample experiment output
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
pip install -r requirements.txt

# Provide your OpenAI key (the script reads it from a .env file)
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

## Usage

**1. (Optional) Rebuild the test data** from the raw ER_Magellan records:

```bash
python src/build_test_data.py \
    -i "data/raw/raw_em(Amazon_Google_Structured).txt" \
    -o "data/processed/test_data(Amazon_Google_Structured).json"
```

`build_test_data.py` parses the `COL <field> VAL <value>` blocks into a list of
`{entity1, entity2, label}` records (`label` is `YES`/`NO`).

**2. Run the committee-voting experiment:**

```bash
python src/run_em_voting.py \
    -i "data/processed/test_data(Amazon_Google_Structured).json" \
    -o "results/em_vote_results.csv" \
    -m gpt-4.1
```

The script prints Accuracy, Precision, Recall and F1, and writes per-pair raw
responses, predictions and correctness to the output CSV.

## Method details

- **Committee prompting** — one model, three role-played experts, independent
  rationales, no cross-referencing between experts.
- **Majority vote** — `>= 2` YES votes → final `YES`.
- **Strict output schema** — fixed field names and uppercase labels enable lossless
  regex/JSON parsing.
- **Auditability** — short attribute-grounded rationales let errors be traced to
  specific evidence without exposing long chain-of-thought.

## Data source

The records come from the **ER_Magellan** entity-matching benchmark
(Amazon-Google and DBLP-Scholar subsets), a widely used EM dataset.

## Citation

```bibtex
@article{kim_em_voting,
  title  = {Virtual Experts to Collective Decisions: An LLM-Driven Majority Voting for EM},
  author = {Kim, Euijin and Choe, Taeyoung and Kim, Mucheol},
  note   = {Chung-Ang University}
}
```

## Acknowledgment

This work was supported by the Institute of Information & Communications
Technology Planning & Evaluation (IITP) grant funded by the Korea government
(MSIT) under the ITRC program (IITP-2025-RS-2024-00438056) and the project
"Development of Digital Innovative Element Technologies for Rapid Prediction of
Potential Complex Disasters and Continuous Disaster Prevention" (RS-2025-02305436).
