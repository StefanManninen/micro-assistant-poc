## 🧠 Micro-Assistant PoC

An adaptive local terminal assistant designed to be small, fast, and resource-aware.

This project explores the opposite direction of bloated cloud-based AI agents. Instead of relying on a large always-on model, it combines two tiny local models with a SQLite-based reinforcement policy layer.

The assistant learns when a previous route or answer was good enough to reuse locally, allowing it to skip unnecessary LLM calls.

## 📉 Core Metric

The goal is simple:

> **API calls, web searches, and model invocations should decrease over time.**

As the assistant is used, repeated patterns are promoted from external tool usage into local SQLite-based intuition. Over time, this can become training data for a distilled local adapter or LoRA.

### 🚀 Performance Proof: 0.83 ms Local Intuition

```text
[server_env] $ I'm getting an error in my docker compose file, search for the flag

🚀 [Local Intuition Hit] Source: generated_and_verified
-> Resolved from SQLite in 0.83 ms. Ollama invocation skipped to save compute.
```

## 🛠️ Architecture

1. **gemma3:270m** — Voice & Intent  
   Conversational front-end and basic intent detection.

2. **functiongemma** — Tool Router  
   Function-calling model used to select tools and generate structured JSON actions.

3. **SQLite Policy Layer** — Local Intuition  
   Stores reinforced routes, cached answers, usage stats, and feedback weights.

4. **Cleaner / Critic Layer** — Immune System  
   Detects bad cached answers, noisy memories, and weak training candidates before they become permanent behavior.

## 🔄 Execution Flow Matrix

When an input is received, the system evaluates the local policy state before invoking any model weights:

1. 🟢 **Full Intuition Hit**  
   `route_weight >= 2.0 && answer_weight >= 2.0`

   Returns the verified answer directly from SQLite.  
   **Ollama skipped. Latency: ~0.8 ms.**

2. 🟡 **Routing Intuition Hit**  
   `route_weight >= 2.0 && answer_weight < 2.0`

   Bypasses `gemma3:270m` intent analysis and directly triggers the required tool, such as `browser_search`.

3. 🔴 **Cache Miss**
   No existing policy, weak weight, or negative feedback.

   Runs the standard MoE pipeline:

   ```text
   gemma3:270m → functiongemma → tool execution → human feedback loop
   ```

## 🧪 Current Limitations

* Exact hash matching only
* No semantic similarity yet
* Weak answer validation
* Tool execution is early-stage
* Rewards are manual
* No real LoRA or fine-tuning pipeline yet

## 🎯 Long-Term Idea

Most current AI memory systems are variations of retrieval:

```text
store text → search text → inject text into the prompt
```

This project explores a different path:

> **Memory should not only be retrieved.**  
> **Useful behavior should eventually be learned.**

The long-term goal is a small personal assistant that becomes better at understanding its user, their systems, and their preferred workflows — while reducing external calls instead of increasing them.

## Why?

A personal assistant does not need to know everything.

It needs to know what is relevant to its user, when to use tools, and when it can avoid expensive model calls.

## 🚀 Quickstart

Make sure [Ollama](https://ollama.com) is installed and running locally.

Pull the required sub-1B experts:

```bash
ollama pull gemma3:270m
ollama pull functiongemma
```

Install Python dependencies:

```bash
pip install requests
```

Run the assistant:

```bash
python core/orchestrator.py
```

## Philosophy

This project follows a simple principle:

> AI should assist understanding, not replace it.

The assistant is intentionally transparent and traceable.  
Every learned shortcut is stored locally, weighted explicitly, and can be inspected or cleaned.

No hidden autonomous behavior.  
No black-box agent swarm.  
No unnecessary cloud dependency.

## Support

This is an experimental proof-of-concept.

No support is promised.  
Issues may be ignored.  
Pull requests may be ignored.

## License

MIT License. See [LICENSE](LICENSE).