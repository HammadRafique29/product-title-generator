import subprocess
import time
import requests
import sys, json


OLLAMA_URL = "http://localhost:11434"
BEST_MODELS_PRIORITY = ["llama3", "gemma", "mistral", "llama2", "phi", "codellama", "qwen"]
CONTEXT =  """
You are a strict and intelligent product title generator. Your task is to rewrite the provided product title to ensure it is grammatically correct, sounds natural when spoken, and falls within 7 to 10 words.

Guidelines:

- Correct grammar, punctuation, and structure to ensure fluency and natural speech.
- Fix or reword awkward or overly short titles to improve clarity and relevance.
- Spell out standalone numbers (e.g., '2' becomes 'two') to reduce awkward pauses during text-to-speech (TTS).
- Avoid emojis, special characters, or any marketing phrases like 'Introducing,' 'Get now,' or 'Experience the best.'
- Abbreviations should only be used if they are widely recognized (e.g., USB, LED).
- Include the product's name, brand, model number (if any), and highlight at least three key features such as functionality, compatibility, design, or performance.
- Rewrite long product titles concisely while preserving critical details. Avoid redundancy.
- Brand integrity must be maintained in the rewritten titles.
- Output exactly one product title — no explanations, quotes, line breaks, or extra commentary.

Example:
Prompt: AOC KM100 Keyboard and Mouse Set
Output: AOC KM100 Mechanical Keyboard and Mouse Set with Ergonomic Design, Wireless Connectivity, Quiet Keys, and USB Receiver Compatibility
"""


def is_ollama_running():
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False



def start_ollama():
    print("Starting Ollama server...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        if is_ollama_running():
            print("Ollama is now running.")
            return True
        time.sleep(1)
    raise RuntimeError("Ollama server failed to start.")



def get_local_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        response.raise_for_status()
        models = [model["name"] for model in response.json().get("models", [])]
        return models
    except Exception as e:
        print(f"Failed to get models: {e}")
        return []



def select_best_model(local_models):
    for model in BEST_MODELS_PRIORITY:
        for m in local_models:
            if model in m:
                print(f"Selected model: {m}")
                return m
    raise ValueError("No suitable model found in local Ollama models.")



def send_chat_prompt(model: str, prompt: str, context=None):

    try:
        if not model:
            local_models = get_local_models()
            if not local_models: raise Exception("No local models found. Use `ollama run <model>` to download one.")
            model = select_best_model(local_models)
            
        payload = {
            "model": model,
            "messages": []
        }

        if context:
            payload["messages"].append({"role": "system", "content": context})

        payload["messages"].append({"role": "user", "content": prompt})

        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True)
        response.raise_for_status()

        full_response = ""
        for chunk in response.iter_lines(decode_unicode=True):
            if chunk:
                try:
                    data = json.loads(chunk)
                    content = data.get("message", {}).get("content", "")
                    full_response += content
                except json.JSONDecodeError:
                    print(f"Skipping malformed chunk: {chunk}")

        print("\nAI Response:\n" + full_response.strip())
    except Exception as e:
        print(e)
        raise Exception(str(e))



if __name__ == "__main__":

    prompt = input("Enter your prompt: ")
    context = input("Enter context (or leave empty): ").strip() or None

    if not is_ollama_running(): start_ollama()

    local_models = get_local_models()
    if not local_models: sys.exit("No local models found. Use `ollama run <model>` to download one.")

    model = select_best_model(local_models)
    send_chat_prompt(model, prompt, context)
