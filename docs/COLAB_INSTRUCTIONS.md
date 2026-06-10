# Colab Fine-Tuning Instructions

If Colab is having trouble reading the `.ipynb` file directly, the easiest and most reliable method is to just copy and paste the code into a fresh Colab notebook!

Here is exactly what you need to do:

### Step 1: Setup
1. Go to [Google Colab](https://colab.research.google.com/) and click **New Notebook**.
2. Go to **Runtime > Change runtime type**, select **T4 GPU**, and hit Save.
3. On the left side of the screen, click the **Folder icon** and upload your `scripts/training_data.jsonl` file.

### Step 2: Install Unsloth
Create a new code block, paste this in, and click the Play button to run it:
```python
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps xformers trl peft accelerate bitsandbytes
```

### Step 3: Load the Base Model
Create another code block, paste this, and run it. This downloads the base Phi-3 model:
```python
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "microsoft/Phi-3-mini-4k-instruct",
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
)
```

### Step 4: Load Your Upwork Data
Create another block, paste this, and run it. This formats your 51 perfect conversations:
```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="training_data.jsonl", split="train")

def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = []
    for convo in convos:
        # Formats the JSON array into the exact chat template the model expects
        text = tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)
        texts.append(text)
    return { "text" : texts }

dataset = dataset.map(formatting_prompts_func, batched = True)
```

### Step 5: Start Training!
Create another block, paste this, and run it. **This will take about 20-40 minutes.**
```python
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = 2048,
    dataset_num_proc = 2,
    packing = False,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)
trainer_stats = trainer.train()
```

### Step 6: Export and Download
Once training finishes, run this final block to convert your brain into a `.gguf` file!
```python
model.save_pretrained_gguf("leif_model", tokenizer, quantization_method = "q4_k_m")
print("✅ Training Complete! Look in the left sidebar for leif_model-unsloth.Q4_K_M.gguf and download it.")
```
