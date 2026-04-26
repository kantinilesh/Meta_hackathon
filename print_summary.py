import json
import os

LOG_FILE = "training_log.json"

try:
    with open(LOG_FILE) as f:
        training_log = json.load(f)
except FileNotFoundError:
    print("No training log found.")
    training_log = []

if training_log:
    print("Training Results Summary")
    print("=" * 55)
    print(f"{'Episode':^10} {'Avg Reward':^14} {'Total Reward':^14} {'Duration':^12}")
    print("-" * 55)
    for d in training_log:
        ep = d['iteration'] + 1
        avg = d.get('reward', 0)
        total = d.get('total_reward', avg * 3)
        dur = d.get('duration_seconds', 0)
        print(f"  {ep:^8}   {avg:^14.4f}   {total:^14.4f}   {dur:^10.1f}s")
    print("-" * 55)

    rewards = [d['reward'] for d in training_log]
    improvement = rewards[-1] - rewards[0]
    print(f"\nBaseline avg reward : {rewards[0]:.4f}")
    print(f"Final avg reward    : {rewards[-1]:.4f}")
    print(f"Net improvement     : {improvement:+.4f}")

    if rewards[0] != 0:
        pct = (improvement / rewards[0]) * 100
        print(f"Improvement %       : {pct:+.1f}%")

    print("\nFinal Learned Strategy:")
    print("-" * 55)
    print(training_log[-1]['strategy'])
