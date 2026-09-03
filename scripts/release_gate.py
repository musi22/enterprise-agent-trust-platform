import asyncio
import sys
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from packages.evaluators.runner import BenchmarkRunner

async def main():
    parser = argparse.ArgumentParser(description="Agentic Commerce Reliability & Recovery Lab - Release Gate Evaluator")
    parser.add_argument("--reps", type=int, default=1, help="Number of repetitions per scenario")
    parser.add_argument("--fail-on-regression", action="store_true", default=True, help="Exit with code 1 if critical release gates fail")
    args = parser.parse_args()

    print("================================================================================")
    print("🚀 STARTING AUTOMATED RELEASE GATE BENCHMARK")
    print("================================================================================")

    runner = BenchmarkRunner(scenarios_dir="scenarios", results_dir="results")
    summary = await runner.run_benchmark(repetitions_per_scenario=args.reps)

    passed = summary["release_gate_passed"]
    print("\n================================================================================")
    print("📊 RELEASE GATE DECISION SUMMARY")
    print("================================================================================")
    for gate_name, gate_val in summary["critical_gates"].items():
        icon = "✅ PASS" if gate_val else "❌ FAIL"
        print(f"  {icon} : {gate_name}")

    if passed:
        print("\n🎉 ALL RELEASE GATES PASSED! SYSTEM VERIFIED FOR DEPLOYMENT CANDIDACY.")
        sys.exit(0)
    else:
        print("\n🛑 RELEASE GATE FAILED! CRITICAL RELIABILITY/SECURITY THRESHOLD VIOLATION DETECTED.", file=sys.stderr)
        if args.fail_on_regression:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
