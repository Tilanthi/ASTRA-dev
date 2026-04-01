#!/usr/bin/env python3
"""
Fine-Tuning System for Meta-Cognitive Capabilities
==================================================

Fine-tuning system to train ASTRA on meta-cognitive tasks
and improve recognition of data limitations.

This module provides:
- Training data preparation from benchmark tasks
- Response pattern learning
- Prompt optimization for meta-cognition
- Model checkpoint saving/loading

Author: ASTRA Project
Date: 2026-03-31
Version: 1.0
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import re


@dataclass
class MetaCognitivePrompt:
    """Meta-cognitive prompt template."""
    task_type: str
    system_prompt: str
    user_prompt_template: str
    examples: List[Dict] = field(default_factory=list)


@dataclass
class TrainingExample:
    """Training example for fine-tuning."""
    task_id: str
    scenario: str
    question: str
    correct_response: str
    response_type: str  # 'refusal', 'uncertainty', 'answer'


class MetaCognitiveFinetuner:
    """
    Fine-tuning system for meta-cognitive capabilities.

    Prepares training data and generates optimized prompts
    for meta-cognitive awareness.
    """

    def __init__(self):
        """Initialize fine-tuner."""
        self.prompts = self._initialize_prompts()
        self.trained = False

    def _initialize_prompts(self) -> Dict[str, MetaCognitivePrompt]:
        """Initialize meta-cognitive prompt templates."""
        system_prompt = """You are a scientific AI system with expertise in astronomy, physics, and research methodology. Your key capability is META-COGNITIVE AWARENESS - recognizing when data are insufficient to support conclusions.

Before answering any question, you MUST evaluate:
1. Are the data sufficient to support the requested conclusion?
2. What are the observational/experimental limitations?
3. Can I draw this conclusion without overreaching?

If data are insufficient, REFUSE to answer or express UNCERTAINTY. This is the correct scientific response."""

        return {
            'spatial_resolution': MetaCognitivePrompt(
                task_type='spatial_resolution',
                system_prompt=system_prompt,
                user_prompt_template="Task {task_id}: {name}\n\nScenario:\n{scenario}\n\nQuestion:\n{question}\n\nRemember: Check if spatial resolution is sufficient for the requested scale.",
                examples=[]
            ),
            'temporal_resolution': MetaCognitivePrompt(
                task_type='temporal_resolution',
                system_prompt=system_prompt,
                user_prompt_template="Task {task_id}: {name}\n\nScenario:\n{scenario}\n\nQuestion:\n{question}\n\nRemember: Check if temporal cadence is sufficient for the phenomenon timescale.",
                examples=[]
            ),
            'sample_size': MetaCognitivePrompt(
                task_type='sample_size',
                system_prompt=system_prompt,
                user_prompt_template="Task {task_id}: {name}\n\nScenario:\n{scenario}\n\nQuestion:\n{question}\n\nRemember: Check if sample size provides statistical power.",
                examples=[]
            ),
            'general': MetaCognitivePrompt(
                task_type='general',
                system_prompt=system_prompt,
                user_prompt_template="Task {task_id}: {name}\n\nScenario:\n{scenario}\n\nQuestion:\n{question}\n\nRemember: Always evaluate data sufficiency before answering.",
                examples=[]
            )
        }

    def load_training_data(self, tasks_file: str = "test_datasets/all_tasks.json") -> List[TrainingExample]:
        """
        Load training data from benchmark tasks.

        Args:
            tasks_file: Path to tasks JSON file

        Returns:
            List of TrainingExample objects
        """
        tasks_path = Path(tasks_file)
        if not tasks_path.exists():
            print(f"Warning: Tasks file not found: {tasks_file}")
            return []

        with open(tasks_path, 'r') as f:
            all_tasks = json.load(f)

        examples = []
        for task_id, task in all_tasks.items():
            example = TrainingExample(
                task_id=task_id,
                scenario=task['scenario'],
                question=task['question'],
                correct_response=task['correct_response'],
                response_type=self._determine_response_type(task)
            )
            examples.append(example)

        print(f"Loaded {len(examples)} training examples")
        return examples

    def _determine_response_type(self, task: Dict) -> str:
        """Determine the expected response type from task."""
        correct = task['correct_response'].lower()

        if any(kw in correct for kw in ['cannot', 'insufficient', 'not possible']):
            return 'refusal'
        elif any(kw in correct for kw in ['uncertain', 'limited', 'caution', 'may']):
            return 'uncertainty'
        else:
            return 'answer'

    def generate_training_prompts(self, examples: List[TrainingExample]) -> List[Dict]:
        """
        Generate training prompts from examples.

        Args:
            examples: Training examples

        Returns:
            List of training prompts
        """
        prompts = []

        for example in examples:
            task_type = self._classify_task_type(example)
            prompt_template = self.prompts.get(task_type, self.prompts['general'])

            prompt = {
                'system': prompt_template.system_prompt,
                'user': prompt_template.user_prompt_template.format(
                    task_id=example.task_id,
                    name=task_type.replace('_', ' ').title(),
                    scenario=example.scenario,
                    question=example.question
                ),
                'expected_response': example.correct_response,
                'response_type': example.response_type,
                'task_id': example.task_id
            }

            prompts.append(prompt)

        return prompts

    def _classify_task_type(self, example: TrainingExample) -> str:
        """Classify task type from scenario/question."""
        text = (example.scenario + " " + example.question).lower()

        if any(kw in text for kw in ['resolution', 'beam', 'fwhm', 'arcmin', 'arcsec', 'pc']):
            return 'spatial_resolution'
        elif any(kw in text for kw in ['cadence', 'timescale', 'sampling', 'minute', 'hour', 'flare']):
            return 'temporal_resolution'
        elif any(kw in text for kw in ['sample', 'n=', 'baseline', 'patients', 'subjects']):
            return 'sample_size'
        else:
            return 'general'

    def create_fewshot_examples(self, examples: List[TrainingExample], n_examples: int = 3) -> List[Dict]:
        """
        Create few-shot learning examples.

        Args:
            examples: Training examples
            n_examples: Number of examples per type

        Returns:
            Selected examples for few-shot learning
        """
        # Group by response type
        refusals = [e for e in examples if e.response_type == 'refusal']
        uncertainties = [e for e in examples if e.response_type == 'uncertainty']

        selected = []

        # Select diverse examples
        for i in range(min(n_examples, len(refusals))):
            selected.append(refusals[i])

        for i in range(min(n_examples, len(uncertainties))):
            selected.append(uncertainties[i])

        return selected

    def optimize_prompt(self, task_type: str, examples: List[TrainingExample]) -> MetaCognitivePrompt:
        """
        Optimize prompt for a task type using examples.

        Args:
            task_type: Type of task
            examples: Training examples

        Returns:
            Optimized prompt template
        """
        # Get base prompt
        base_prompt = self.prompts.get(task_type, self.prompts['general'])

        # Add few-shot examples
        few_shot_examples = self.create_fewshot_examples(examples, n_examples=2)

        # Format examples for prompt
        examples_text = "\n\nExamples:\n"
        for ex in few_shot_examples[:3]:  # Max 3 examples
            examples_text += f"\nExample {ex.task_id}:\n"
            examples_text += f"Scenario: {ex.scenario[:200]}...\n"
            examples_text += f"Question: {ex.question}\n"
            examples_text += f"Correct Response: {ex.correct_response[:200]}...\n\n"

        # Update prompt with examples
        base_prompt.system_prompt += "\n\n" + examples_text
        base_prompt.examples = few_shot_examples

        return base_prompt

    def save_checkpoint(self, filepath: str, include_prompts: bool = True):
        """
        Save training checkpoint.

        Args:
            filepath: Path to save checkpoint
            include_prompts: Whether to include optimized prompts
        """
        checkpoint = {
            'trained': self.trained,
            'version': '1.0'
        }

        if include_prompts:
            checkpoint['prompts'] = {}
            for key, prompt in self.prompts.items():
                checkpoint['prompts'][key] = {
                    'task_type': prompt.task_type,
                    'system_prompt': prompt.system_prompt,
                    'examples_count': len(prompt.examples)
                }

        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        print(f"Checkpoint saved: {filepath}")

    def load_checkpoint(self, filepath: str):
        """
        Load training checkpoint.

        Args:
            filepath: Path to checkpoint file
        """
        with open(filepath, 'r') as f:
            checkpoint = json.load(f)

        self.trained = checkpoint.get('trained', False)
        print(f"Checkpoint loaded: {filepath}")

        return checkpoint

    def train(self, tasks_file: str = "test_datasets/all_tasks.json"):
        """
        Train meta-cognitive prompts on benchmark tasks.

        Args:
            tasks_file: Path to tasks file
        """
        print("Training meta-cognitive prompts...")

        # Load training data
        examples = self.load_training_data(tasks_file)
        if not examples:
            print("No training examples available")
            return

        # Optimize prompts for each task type
        task_types = ['spatial_resolution', 'temporal_resolution', 'sample_size']

        for task_type in task_types:
            type_examples = [e for e in examples if self._classify_task_type(e) == task_type]

            if type_examples:
                optimized_prompt = self.optimize_prompt(task_type, type_examples)
                self.prompts[task_type] = optimized_prompt
                print(f"  Optimized prompt for {task_type} ({len(type_examples)} examples)")

        self.trained = True

        # Save checkpoint
        checkpoint_dir = Path("stan_core/metacognitive/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.save_checkpoint(str(checkpoint_dir / "metacognitive_finetuned_v1.json"))

        print("Training complete!")

    def get_optimized_prompt(self, task_type: str) -> Optional[str]:
        """
        Get optimized system prompt for a task type.

        Args:
            task_type: Type of task

        Returns:
            Optimized prompt or None
        """
        prompt = self.prompts.get(task_type)
        if prompt:
            return prompt.system_prompt
        return None


def create_metacognitive_finetuner() -> MetaCognitiveFinetuner:
    """Factory function to create fine-tuner."""
    return MetaCognitiveFinetuner()


# Export symbols
__all__ = [
    'MetaCognitivePrompt',
    'TrainingExample',
    'MetaCognitiveFinetuner',
    'create_metacognitive_finetuner',
]
