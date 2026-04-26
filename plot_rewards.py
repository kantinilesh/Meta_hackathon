import json
import matplotlib.pyplot as plt

def main():
    try:
        with open("training_log.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: training_log.json not found. Please run `python train.py` first.")
        return

    iterations = [d["iteration"] for d in data]
    rewards = [d["reward"] for d in data]

    # Setup the plot aesthetics
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, rewards, marker='o', linestyle='-', color='#e84393', linewidth=2, markersize=8)
    
    plt.title("Iterative Prompt Optimization: Agent Learning Curve", fontsize=16, pad=15, fontweight='bold')
    plt.xlabel("Training Iteration (Episode)", fontsize=12)
    plt.ylabel("Total Episode Reward", fontsize=12)
    
    # Customize grid and ticks
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(iterations)
    
    # Fill area under the curve for a polished look
    plt.fill_between(iterations, rewards, alpha=0.1, color='#e84393')

    # Add informative annotations for the baseline and final trained agent
    if len(iterations) > 0:
        # Baseline Annotation
        plt.annotate('Untrained Baseline\n(Default Strategy)', 
                     xy=(iterations[0], rewards[0]), 
                     xytext=(iterations[0] + 0.2, rewards[0] - 0.2),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6),
                     fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
        
        # Trained Agent Annotation
        plt.annotate('Trained Agent\n(Refined Strategy)', 
                     xy=(iterations[-1], rewards[-1]), 
                     xytext=(iterations[-1] - 0.8, rewards[-1] - 0.2),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6),
                     fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

    plt.tight_layout()
    
    # Save the output visualization
    output_filename = "learning_curve.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"✅ Successfully saved reward visualization to {output_filename}")

if __name__ == "__main__":
    main()
