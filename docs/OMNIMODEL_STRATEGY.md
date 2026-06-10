# The OmniModel Strategy (The Infinite Brain)

This document outlines the long-term architectural strategy for Leif: moving beyond a multi-model router (MoE) to build a single, deeply personalized "Omni-Brain."

## 🧠 What is the OmniModel?
While a Mixture of Experts (MoE) uses an orchestrator to pass tasks to generic models (`llama3` for text, `deepseek` for code), the **OmniModel** strategy focuses on continuously training ONE powerful base model (like `Qwen 2.5 7B`) to be a master of everything you need.

Instead of plugging in more external brains, you grow a single, cohesive brain that shares deep, nuanced context of your projects and coding style.

## 🏗️ The Training Pipeline (Knowledge Distillation)
To create the OmniModel, we use a Teacher-Student architecture:

1. **The Teacher (DeepSeek / GPT-4o):** Used offline to generate thousands of high-quality examples, solutions, and reasoning paths.
2. **The Filter (The Sandbox):** A script that automatically tests the Teacher's code. If the code crashes, it is thrown out. If it works, it is saved to `training_data.jsonl`.
3. **The Student (Qwen 7B):** Your local `auto_trainer.py` script continuously fine-tunes the Qwen model on this verified dataset, physically absorbing the Teacher's knowledge.

## 📚 Curriculum Learning
You don't have to teach the OmniModel everything at once. You can train it sequentially over months:
*   **Stage 1:** Fine-tune on Coding Data (Leif learns to code).
*   **Stage 2:** Fine-tune on Prompting/Reasoning Data.
*   *Crucial Rule:* Always mix ~20% of your old coding data into the new prompting dataset during Stage 2. This prevents **Catastrophic Forgetting** (where the model overwrites old skills with new ones).

## 💾 Overcoming the 7B Parameter Capacity Limit
A 7 Billion parameter model fits perfectly in a 4GB VRAM GPU (like an RTX 3050). However, it has a physical limit on how much it can learn before it gets "full" and becomes mediocre.

When the OmniModel hits this limit, we use **LoRA Adapters ("Cartridges")**:
Instead of rewriting the base model, the fine-tuning saves tiny 50MB adapter files.
*   `leif-coding-lora.safetensors`
*   `leif-copywriting-lora.safetensors`
When you ask Leif a question, she seamlessly unplugs one cartridge and plugs in another in milliseconds, granting her infinite knowledge capacity without exceeding hardware limits.

## 🛠️ Mitigating 7B Mistakes
Because a 7B model will naturally make more logic errors than a 70B model, the architecture compensates:
1. **The Sandbox (Phase 6):** Leif compiles and runs her own code. If it crashes, she reads the error and fixes it before showing you the output.
2. **The Escalation Clause:** If Leif fails 3 times in the sandbox, she admits the problem is too complex for her local 7B brain and escalates the request to GPT-4o or Claude via API.
