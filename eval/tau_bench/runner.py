from eval.tau_bench.harness import load_eval_cases


def run() -> list[dict[str, str]]:
    return [{"case": case.name, "expected_behavior": case.expected_behavior} for case in load_eval_cases()]


if __name__ == "__main__":
    for result in run():
        print(result)
