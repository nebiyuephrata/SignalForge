ESTIMATED_BUDGET = {
    "dev_llm": 4.0,
    "eval_llm": 12.0,
    "infra": 0.0,
}


if __name__ == "__main__":
    total = sum(ESTIMATED_BUDGET.values())
    print({"estimated_budget": ESTIMATED_BUDGET, "total": total})
