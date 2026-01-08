---
title: Log Classification System
emoji: 📊
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# 🔍 Log Classification System

**Automated log analysis powered by a three-tier machine learning pipeline**

🌐 **[Try Live Demo](https://19sarvagya-log-classification-system.hf.space/dashboard)**

---

## Overview

Intelligent log classification system that automatically analyzes log files and categorizes them by severity using a multi-stage ML approach. Built for production environments with scalability and accuracy in mind.

## Key Features

✅ **Three-Tier ML Pipeline** — Regex pattern matching → BERT neural network → LLM fallback  
✅ **90.63% Accuracy** — BERT model trained on real-world log datasets  
✅ **42 Optimized Patterns** — Pre-trained regex rules for instant classification  
✅ **6 Severity Levels** — CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG  
✅ **Universal Support** — CSV, JSON, TXT, LOG file formats  
✅ **Real-Time Dashboard** — Interactive analytics with instant visual feedback

## Architecture

**Stage 1:** Pattern-based regex classification (fastest, ~70% coverage)  
**Stage 2:** BERT transformer model (high accuracy, handles complex logs)  
**Stage 3:** Groq LLM API (fallback for edge cases)

## Technology Stack

- **Backend:** FastAPI, Python 3.11, Pydantic validation
- **ML Models:** BERT (sentence-transformers), Groq LLM (llama-3.3-70b)
- **Deployment:** Docker containerization, Hugging Face Spaces
- **Features:** Rate limiting, health checks, CORS, environment-based config

## Use Cases

- Security incident response and threat detection
- Production system monitoring and alerting
- Compliance auditing and log retention
- DevOps troubleshooting and debugging

---

**GitHub:** [SarvagyaGupta-19/Log_classification_system](https://github.com/SarvagyaGupta-19/Log_classification_system)
