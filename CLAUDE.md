# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of **LiveKit Agents** examples for building voice, video, and telephony AI agents. It contains 50+ focused single-concept demos in `docs/examples/` and 20+ production-style applications with frontends in `complex-agents/`.

## Common Commands

```bash
# Run any agent in dev mode (interactive console)
python <path-to-agent>.py dev

# Run with console for voice/text interaction
python <path-to-agent>.py console

# Run tests (from testing directory)
cd complex-agents/testing && pytest -v

# Install dependencies
pip install -r requirements.txt

# For frontends (Next.js with pnpm)
cd <frontend-directory> && pnpm install && pnpm dev
```

## Environment Setup

Required `.env` file in repository root:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
```

## Architecture Patterns

### Agent Structure
Every Python agent uses YAML frontmatter metadata at the top of the file:
```python
"""
---
title: Example Agent
category: basics
tags: [tag1, tag2]
difficulty: beginner|intermediate|advanced
description: What this agent demonstrates
demonstrates:
  - Feature 1
  - Feature 2
---
"""
```

### Core LiveKit Agents Pattern
```python
from livekit.agents import JobContext, AgentSession, Agent, cli
from livekit.plugins import silero, openai, deepgram, cartesia

class MyAgent(Agent):
    def __init__(self):
        super().__init__(instructions="...")

    async def on_enter(self):
        self.session.generate_reply()

# Entrypoint pattern
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=...,  # Speech-to-Text
        llm=...,  # Language Model
        tts=...,  # Text-to-Speech
        vad=...,  # Voice Activity Detection
    )
    await session.start(agent=MyAgent(), room=ctx.room)
```

### Multi-Agent Transfer Pattern
Used in `medical_office_triage`, `personal_shopper`, `doheny-surf-desk`:
- Agents inherit from a `BaseAgent` with handoff logic
- `UserData` dataclass stores shared state across agents
- Context preservation via `chat_ctx` truncation on transfer
- Agent references stored in `UserData.personas` dict

### Background Observer Pattern
Used in `doheny-surf-desk`:
- Observer agent runs in parallel, monitoring conversation
- Uses slower/more capable LLM for analysis without blocking
- Injects context via `update_chat_ctx()` when triggers detected

### Task Groups Pattern
Sequential task execution with structured results:
```python
task_group = TaskGroup()
task_group.add(lambda: NameTask(), id="name_task")
results = await task_group
name = results.task_results["name_task"].name
```

### Prompt Management
Agent instructions loaded from YAML files in `prompts/` directories:
```python
from utils import load_prompt
instructions = load_prompt("triage_prompt.yaml")
```

## Key Directories

- `docs/examples/` - Single-concept demos (basics, telephony, pipeline, vision, etc.)
- `docs/index.yaml` - Complete catalog with metadata for all 77 examples
- `complex-agents/` - Full applications with frontends
- `complex-agents/testing/` - pytest fixtures and patterns for agent testing

## Provider Plugins

Common imports:
```python
from livekit.plugins import (
    silero,      # VAD
    deepgram,    # STT
    openai,      # LLM
    cartesia,    # TTS
    elevenlabs,  # TTS
    anthropic,   # LLM
    google,      # LLM (Gemini)
)
from livekit.agents import inference  # Unified inference API
```

## Testing Agents

```python
from livekit.agents.voice.run_result import mock_tools

# Mock function tools
async with mock_tools(agent_session, {"tool_name": mock_return_value}):
    result = await session.generate_reply(user_input="test input")
    await result.expect.next_event().is_message(role="assistant")
```
