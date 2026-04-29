# Synthesis Memo: A Survey on LLM-as-a-Judge

## What I took from the paper

The survey is useful because it separates “LLMs can score things” from “LLMs are reliable judges.” The gap between those two claims is where most of the engineering work lives. Reliability depends on consistency, bias control, scenario fit, and meta-evaluation. That framing is exactly right for Tenacious-Bench because our judge does not need to be universal. It needs to be dependable on a narrow but business-critical surface: groundedness, confidence alignment, tone safety, and routing correctness.

Source: https://huggingface.co/papers/2411.15594

## Where I disagree

I disagree with the temptation, common in judge discussions, to use an LLM judge as the primary source of truth once it performs well enough on benchmark correlations. In this project, the judge should not be the truth. The structured brief, typed rubric, and deterministic lifecycle state are the truth. The judge is a filter layered on top of those artifacts.

That distinction matters because sales-domain evaluation is full of seductive fluent outputs. If the judge is allowed to free-associate about “quality” rather than score explicit constraints, it will reward the wrong thing.

## How it changes my design

This paper pushed me toward a hybrid evaluation stack:

1. deterministic fields for the parts that can be scored exactly,
2. a narrow judge for the parts that still require preference-style assessment,
3. explicit meta-evaluation of judge behavior.

That is why `scoring_evaluator.py` is machine-verifiable first, and why the eventual trained critic should sit beside it rather than replace it. The judge’s job is not to invent new standards. It is to become more reliable at enforcing Tenacious’s existing standards.
