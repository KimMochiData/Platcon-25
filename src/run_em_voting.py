#!/usr/bin/env python3
"""
run_em_voting.py
  LLM-driven majority voting for Entity Matching (EM).

  A single GPT model simulates a committee of three independent reviewers
  (Expert A, B, C). Each expert reads the same record pair in isolation,
  outputs a one-sentence rationale and a binary YES/NO vote, and the final
  decision is taken by a deterministic majority rule (>= 2 YES -> YES).

  Input : processed test data produced by build_test_data.py
          (default: data/processed/test_data(Amazon_Google_Structured).json)
  Output: a CSV with raw responses, predictions and per-row correctness
          (default: results/em_vote_results.csv)

Usage:
    # set your key first (see .env.example)
    export OPENAI_API_KEY="sk-..."
    python src/run_em_voting.py \
        --input "data/processed/test_data(Amazon_Google_Structured).json" \
        --output "results/em_vote_results.csv" \
        --model gpt-4.1
"""

import os
import re
import json
import time
import argparse
from pathlib import Path

import openai
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# Load OPENAI_API_KEY from a local .env file (never hardcode keys in source).
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ── Committee prompt ─────────────────────────────────────
PROMPT_TEMPLATE = """### System
You are a committee of **three independent entity-matching experts** (Expert-A, Expert-B, Expert-C).
Each expert must think on their own before seeing anyone else's answer.

### User
Compare the following two entities and decide whether they refer to the **same real-world entity**.

--- INPUT START ---
Entity-1:
{entity1}

Entity-2:
{entity2}
--- INPUT END ---

**Task**
1. Each expert writes ONE short sentence explaining their key reasoning, then outputs "YES" if the entities match, otherwise "NO".
2. After all three votes, tally them: if at least two experts say "YES", the committee's final decision is "YES"; otherwise "NO".
3. Follow the exact output format below. Do NOT add anything else.

**Output format (strict)**
Expert_A_reason: <one-sentence explanation>
Expert_A_vote: <YES|NO>
Expert_B_reason: <one-sentence explanation>
Expert_B_vote: <YES|NO>
Expert_C_reason: <one-sentence explanation>
Expert_C_vote: <YES|NO>
Vote_Count: <n>/3 YES
Final_Decision: <YES|NO>
"""

VOTE_REGEX = re.compile(r"Final_Decision:\s*(YES|NO)", re.IGNORECASE)


# ── Model call ───────────────────────────────────────────
def call_llm(entity1: str, entity2: str,
             model: str = "gpt-4.1", temperature: float = 0.0) -> str:
    """Return the raw completion text for one record pair."""
    prompt = PROMPT_TEMPLATE.format(entity1=entity1, entity2=entity2)
    response = openai.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


# ── Experiment driver ────────────────────────────────────
def run(test_data, model, sleep):
    records = []
    for sample in tqdm(test_data, desc="Running tests"):
        raw = call_llm(sample["entity1"], sample["entity2"], model=model)
        match = VOTE_REGEX.search(raw)
        pred = match.group(1).upper() if match else "PARSEERROR"
        records.append({
            **sample,
            "raw_response": raw,
            "prediction": pred,
            "correct": pred == sample["label"],
        })
        time.sleep(sleep)  # be gentle with rate limits
    return pd.DataFrame(records)


def report(df: pd.DataFrame) -> None:
    tp = int(((df.label == "YES") & (df.prediction == "YES")).sum())
    tn = int(((df.label == "NO") & (df.prediction == "NO")).sum())
    fp = int(((df.label == "NO") & (df.prediction == "YES")).sum())
    fn = int(((df.label == "YES") & (df.prediction == "NO")).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    accuracy = (tp + tn) / len(df) if len(df) else 0

    print(f"\nAccuracy  : {accuracy:.3f}")
    print(f"Precision : {precision:.3f}")
    print(f"Recall    : {recall:.3f}")
    print(f"F1-score  : {f1:.3f}")
    if len(df):
        print("\nSample response ↓")
        print(df.loc[0, "raw_response"])


def main():
    ap = argparse.ArgumentParser(description="LLM majority-voting EM experiment")
    ap.add_argument("-i", "--input",
                    default="data/processed/test_data(Amazon_Google_Structured).json",
                    help="Path to processed test_data JSON")
    ap.add_argument("-o", "--output", default="results/em_vote_results.csv",
                    help="Path to write the results CSV")
    ap.add_argument("-m", "--model", default="gpt-4.1",
                    help="OpenAI chat model name")
    ap.add_argument("--sleep", type=float, default=0.3,
                    help="Seconds to sleep between calls")
    args = ap.parse_args()

    if not openai.api_key:
        raise SystemExit("OPENAI_API_KEY is not set. Add it to a .env file or export it.")
    if not Path(args.input).is_file():
        raise SystemExit(f"Input file not found: {args.input}")

    with open(args.input, encoding="utf-8") as f:
        test_data = json.load(f)

    df = run(test_data, model=args.model, sleep=args.sleep)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(df.to_csv(index=False), encoding="utf-8")
    print(f"\n→ Saved results to {args.output}")

    report(df)


if __name__ == "__main__":
    main()
