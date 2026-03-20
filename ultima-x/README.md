# Ultima X — Inference Model for Anima Platform

Ultima X is the inference engine for autonomous Anima agents. It provides high-quality reasoning, tool calling, and code generation for agent operations.

## Specifications
- Parameters: 122B total, 10B active (MoE architecture)
- Context: 262K tokens (expandable to 1M)
- Capabilities: Tool calling, function calling, code gen, reasoning, multi-step planning
- Hardware: Single GPU (24GB VRAM quantized) or 40GB RAM (CPU)
- License: Apache-2.0

## Quick Start (Ollama)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the base model
ollama pull qwen3.5

# Create the Ultima X branded model
ollama create ultima-x -f Modelfile

# Run
ollama run ultima-x

# API endpoint (OpenAI-compatible)
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ultima-x", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Quick Start (vLLM)
```bash
pip install vllm
vllm serve Qwen/Qwen3.5-122B-Instruct --model-name ultima-x --port 8000
```

## Integration with Anima Platform

Agents connect to Ultima X via standard OpenAI-compatible API. Configure the inference endpoint in platform settings or pass it in the genesis prompt.

```python
# Platform settings
PUT /api/agents/{agent_id}/llm-key
{
    "llm_api_key": "",  # Not needed for self-hosted
    "llm_base_url": "http://your-gpu-server:11434/v1",
    "llm_model": "ultima-x"
}
```

## Inference Hierarchy

| Provider | When | Cost | Identity Risk |
|---|---|---|---|
| Conway compute | Agent in Conway sandbox | Conway credits | None |
| Ultima X (self-hosted) | User hosts on their infra | Zero per call | None |
| Ultima X (your network) | User uses your network | x402 USDC | None |
| External API (OpenAI etc) | User's choice | Per-token | User accepts risk |
