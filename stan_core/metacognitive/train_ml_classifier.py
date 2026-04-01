#!/usr/bin/env python3
"""
Train ML Classifier on Benchmark Tasks
========================================

Trains the meta-cognitive ML classifier on SciEval-Meta tasks.
"""

import sys
from pathlib import Path

# Add RASTI_AI to path for tasks file
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "RASTI_AI"))

from stan_core.metacognitive.ml_classifier import MetaCognitiveClassifier


def main():
    """Train ML classifier."""
    print("Training Meta-Cognitive ML Classifier")
    print("=" * 60)

    # Load training data from benchmark tasks
    tasks_file = Path("test_datasets/all_tasks.json")

    if not tasks_file.exists():
        print(f"ERROR: Tasks file not found: {tasks_file}")
        print("Please run parse_tasks.py first to generate task file.")
        return

    import json

    with open(tasks_file, 'r') as f:
        all_tasks = json.load(f)

    # Prepare training data
    training_data = []

    # Tasks that require meta-cognitive evaluation (based on scoring)
    meta_cognitive_tasks = [
        'A1', 'A2', 'A3', 'A4',  # Spatial resolution
        'B1', 'B2', 'B4', 'B5', 'B6',  # Ambiguity
        'C1', 'C2', 'C3', 'C4', 'C5',  # Model specification
        'D1', 'D2', 'D3', 'D4', 'D5',  # Scale mismatch
        'E1', 'E2',  # Causal claims
    ]

    for task_id in meta_cognitive_tasks:
        if task_id in all_tasks:
            task = all_tasks[task_id]
            training_data.append({
                'task_id': task_id,
                'text': task['scenario'] + " " + task['question'],
                'label': 1,  # Meta-cognitive
                'limitation_type': task['suite']
            })

    print(f"Prepared {len(training_data)} training examples")
    print(f"  Positive examples (meta-cognitive): {len(training_data)}")

    # Create and train classifier
    classifier = MetaCognitiveClassifier()
    classifier.train(training_data)

    # Save trained classifier
    checkpoint_dir = Path("stan_core/metacognitive/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = checkpoint_dir / "ml_classifier_v1.json"
    classifier.save(str(checkpoint_file))

    print(f"\nTrained classifier saved: {checkpoint_file}")

    # Test on a few examples
    print("\nTesting classifier on sample tasks:")

    test_cases = [
        ('A1', all_tasks['A1']['scenario'], all_tasks['A1']['question']),
        ('A3', all_tasks['A3']['scenario'], all_tasks['A3']['question']),
        ('B1', all_tasks['B1']['scenario'], all_tasks['B1']['question']),
    ]

    for task_id, scenario, question in test_cases:
        result = classifier.classify(scenario, question)
        print(f"\n{task_id}: {result.is_meta_cognitive} (confidence: {result.confidence:.2f})")
        print(f"  {result.reasoning}")

    print("\n" + "=" * 60)
    print("ML Classifier training complete!")


if __name__ == "__main__":
    main()
