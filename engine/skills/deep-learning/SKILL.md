---
name: deep-learning
description: Apply deep learning and AI techniques — build models, deploy inference, integrate with agent capabilities.
auto-activate: true
---

# Deep Learning — Step-by-Step Instructions
Build, train, and deploy ML/DL models for fund operations (prediction, analysis, automation).

## Tools & Process
- **code_execution**: Write and run ML code (Python: PyTorch, scikit-learn)
- **sandbox_create + sandbox_exec**: GPU-enabled VMs for training
- **chat_completions**: Use frontier models (GPT-4o, Claude) for complex analysis
- **browse_page**: Research latest models, techniques, datasets

## Applications for the Fund
1. **Price Prediction**: code_execution to train time-series models on crypto price data
2. **Sentiment Analysis**: Analyze social media text for trading signals
3. **Deal Scoring**: ML model to predict investment success from historical deals
4. **Risk Assessment**: Neural network for portfolio risk estimation
5. **Agent Evaluation**: Classify agent quality from behavior patterns

## Deployment
1. Research: browse_page latest techniques for your use case
2. Build: code_execution with Python ML libraries
3. Train: sandbox_create for heavy compute, code_execution for light work
4. Deploy: sandbox_expose_port as inference API
5. Integrate: Use the model from other skills via x402_fetch
