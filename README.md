# Agentic Workflow System

> **Structured Architectural Scaffolding for AI Development**

[![Version](https://img.shields.io/badge/version-0.0.1-blue.svg)](https://github.com/agentic-workflow-os)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](pkgs/container/agentic)

**Agentic Workflow** is a development platform that orchestrates Multi-Agent Systems to plan, architect, and implement complex software projects. Unlike "Chat with Code" tools that rely on messy, unstructured conversation history, this system enforces a **Context-First** philosophy. It treats Agent Context as a file-system state machine, ensuring that your AI Engineer knows exactly what your AI Architect decided.

---

## ⚡ Why Use This?

Most AI coding tools suffer from **Context Drift**. After 20 messages, the AI forgets the architectural constraints you set in message #1.

AI for projects and work is like a rocket: it gives a quick boost of velocity if you have direction, but soon everyone realizes it's only a first-stage booster that stops midway once context is off. The velocity drops, and to carry forward and build production-grade applications needs a 2nd and 3rd stage booster with precision guidance to reach and stay in orbit. **This project is that 2nd and 3rd stage.**

**Agentic Workflow solves this by:**
1.  **Strict Role Separation:** "Architects" write specs. "Engineers" write code. They never swap roles.
2.  **Artifact-Driven Handoffs:** An agent cannot proceed until it receives a specific, validated artifact from its predecessor.
3.  **No "Chatting":** You don't chat in the terminal. The system generates a comprehensive **Context File** that you drop into your preferred AI (ChatGPT, Claude, Gemini, VS Code Copilot). The AI does the work, and you save the result. The system tracks the state.

---

## 🚀 Landing soon
