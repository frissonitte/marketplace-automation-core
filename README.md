# marketplace-automation-core

`marketplace-automation-core` is a small automation project built mainly as a self-learning exercise.

The goal of the repository is to explore how marketplace-style workflows can be automated in a structured way with Python, Appium, and Selenium. Rather than focusing on a single real platform, the code is organized around reusable ideas such as screen navigation, selector-driven configuration, retry logic, small scroll adjustments, and maintenance-style listing actions.

## Why this project exists

This project was shaped as a practical learning space for:

- mobile UI automation with Appium
- browser automation with Selenium
- separating automation logic from target-specific selectors
- experimenting with config-driven workflow design
- handling unstable UI states such as stale elements, overlays, and scroll-related edge cases

In that sense, the repository is less about a polished product and more about documenting an automation architecture that can be studied, adapted, and extended.

## What is included

The current public version focuses on the generic mobile automation layer and a few small entrypoints built on top of it:

- `mobile_listing_refresh.py`
- `mobile_price_adjust.py`
- `mobile_description_refresh.py`

These scripts all use the same shared core and differ only in the workflow flags they enable.

## Project structure

- `marketplace_core.py`
  Shared automation core for mobile listing workflows.

- `target_profiles.py`
  Loads target definitions from JSON files so that selectors and target metadata can be kept outside the main logic.

- `automation_targets.example.json`
  Example structure for target profiles. It shows how selectors, text labels, and target-level settings can be organized without tying the repository to a specific real setup.

- `config.example.json`
  Minimal example of user-level configuration for local experimentation when a flow needs it.

- `requirements.txt`
  Python dependencies used by the project.

## Design approach

One of the main ideas behind this repository is keeping the automation logic as generic as possible.

Instead of hardcoding every selector directly into each script, the project uses a profile-based approach. The reusable logic lives in the Python modules, while target-specific details can be described in external JSON profiles. That makes it easier to study the core behavior on its own and swap target definitions when experimenting with different interfaces.

This also makes the code easier to read from an educational point of view: the control flow, retries, and interaction strategies are visible in one place instead of being buried inside many one-off scripts.

## Local setup

1. Install the dependencies from `requirements.txt`.
2. Use `automation_targets.example.json` as a starting point for your own local target definitions.
3. Adjust selectors, package names, labels, or URLs to match the interface you are experimenting with.
4. If a local run needs user-specific values, use `config.example.json` as a template for your own config file.

## Scope

This repository is intended as a learning-oriented automation core and code organization example. It is best read as a study project about UI automation patterns, configuration structure, and iterative tool-building in Python.
