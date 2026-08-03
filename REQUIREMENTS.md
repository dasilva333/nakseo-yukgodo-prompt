# Research Environment Setup & Requirements Guide

This document records the exact system requirements, toolchains, Python environment setup, and disk/memory precautions needed for an AI agent (or human researcher) to execute the formal proofs and verification scripts for the **Nakseo Yukgodo (洛書六觚圖)** orbit classification project.

---

## 1. Directory Structure

All prompt materials, local code packages, virtual environments, and Lean specs are located in:
`/Users/richardpinedo/Projects.nosync/airi/personal_airi/nakseo_yukgodo_prompt/`

```
nakseo_yukgodo_prompt/
├── PROMPT.md           # The primary research prompt & step-by-step task specification
├── GENERATOR.md        # Problem mathematical formulation, targets, and empirical logs
├── z3_solver_spec.py   # Baseline Z3 constraint solver and pruning DFS code
├── REQUIREMENTS.md     # This setup and requirements document
├── venv/               # Isolated Python 3 virtual environment (pre-configured)
└── yukgodo/            # Local copy of the Nakseo Yukgodo graph & solver package
```

---

## 2. Python Environment Requirements

A dedicated Python 3 virtual environment has been pre-created at `./venv/`.

### Installed Dependencies
- `z3-solver` ($\ge 5.0.0.0$) — Automated SMT constraint solving.
- `numpy` — Array manipulation and permutation matrix operations.
- `scipy` — Structural graph/group action metrics.
- `matplotlib` — Visualization of hexagonal lattice solutions.

### Activation & Execution
Any Python verification script must be run within the virtual environment:
```bash
cd /Users/richardpinedo/Projects.nosync/airi/personal_airi/nakseo_yukgodo_prompt
source ./venv/bin/activate
python3 z3_solver_spec.py
```
*Note: The local `yukgodo/` package is in the root of `nakseo_yukgodo_prompt/`, so `import yukgodo` works out of the box without modifying system `PYTHONPATH`.*

---

## 3. Lean 4 Formal Proof Toolchain

The Lean 4 version manager `elan` is installed on the host system.

### Executable Paths & Versions
- **`elan`**: `~/.elan/bin/elan` (v4.2.3)
- **`lean`**: `~/.elan/bin/lean` (`Lean v4.32.2`)
- **`lake`**: `~/.elan/bin/lake` (`Lake v5.0.0`)

Before running Lean 4 commands, ensure `~/.elan/bin` is present in your shell `PATH`:
```bash
export PATH="$HOME/.elan/bin:$PATH"
lean --version
```

---

## 4. CRITICAL: Mathlib Cache & Disk Space Warning ⚠️

### Disk Space Bottleneck
The Lean 4 ecosystem's primary mathematics library (`mathlib4`) requires downloading large precompiled binary archives (`.ltar`). Downloading and decompressing full `mathlib` can consume **over 10–15 GB of disk space**, which will cause a `No space left on device` error if system storage is low.

### Guidelines for Agents Working on Lean Specs:
1. **Avoid full `mathlib` dependency downloads**: Write standalone Lean 4 files using standard library types (`Mathlib.GroupTheory` or core Lean 4 `Group` / `Structure` abstractions) whenever possible, or lightweight imports.
2. **If Mathlib is required**:
   - Check available disk space before running `lake build` or `lake exe cache get`:
     ```bash
     df -h /System/Volumes/Data
     ```
   - Ensure at least **15–20 GB of free disk space** is available before pulling full `mathlib`.
3. **Cache Cleanup Command**: If disk space becomes exhausted, run:
   ```bash
   rm -rf ~/.cache/mathlib .lake
   ```

---

## 5. Agent Handoff Summary

When delegating this task to a subagent or external LLM:
1. Provide `PROMPT.md` as the main system instruction.
2. Direct the agent to activate `./venv/` for Python scripts.
3. Ensure `PATH="$HOME/.elan/bin:$PATH"` is exported when invoking `lean` or `lake`.
4. Warn the agent against triggering heavy `mathlib` downloads without checking disk space first.
