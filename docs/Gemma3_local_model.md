# Gemma3‑4B: Local Model Documentation

## 1. Overview  
Gemma3‑4B is part of Google’s open‑weight Gemma3 family (1B, 4B, 12B, 27B parameters). The 4B variant:

- Supports both **text** and **image** inputs  
- Offers a **128 K‑token** context window  
- Covers **140+ languages**  
- Runs comfortably on laptops or modest servers  
- Excels at question answering, summarization, reasoning, and basic code tasks  

Model page: [google/gemma-3-4b-it on Hugging Face](https://huggingface.co/google/gemma-3-4b-it)

Gemma is a family of generative artificial intelligence (AI) models and you can use them in a wide variety of generation tasks, including question answering, summarization, and reasoning. Gemma models are provided with open weights and permit responsible commercial use, allowing you to tune and deploy them in your own projects and applications.

The Gemma 3 release includes the following key features. Try it in AI Studio:

Image and text input: Multimodal capabilities let you input images and text to understand and analyze visual data. Start building
128K token context: 16x larger input context for analyzing more data and solving more complex problems.
Function calling: Build natural language interfaces for working with programming interfaces. Start building
Wide language support: Work in your language or expand your AI application's language capabilities with support for over 140 languages. Start building
Developer friendly model sizes: Choose a model size (1B, 4B, 12B, 27B) and precision level that works best for your task and compute resources.


---

## 2. Licensing & Access  
To use `google/gemma-3-4b-it`:

1. Visit the model page on Hugging Face  
2. **Log in** and **accept Google’s usage license**  
3. License permits **research & educational** deployment—review before production use  

---

## 3. Installation  
Install core dependencies:

```pip install transformers accelerate torch```

## 4. Loading the Model

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "google/gemma-3-4b-it"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model     = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
).to(DEVICE)
```


## 5. Generating Structured Feedback

Replace your OpenAI call with:

```python
def get_structured_feedback(prompt: str, max_tokens: int = 700) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.5,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
