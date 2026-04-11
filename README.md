# Marketplace Automation Core

`marketplace-automation-core` is a Python automation project built to explore how marketplace-style workflows can be organized in a structured and reusable way.

The repository focuses on shared automation patterns such as screen navigation, selector-driven configuration, retry handling, small scroll adjustments, and maintenance-style listing actions. Rather than targeting a single platform, it is organized around reusable workflow ideas and profile-based configuration.

## Why this project exists

This project was built to explore and document practical UI automation patterns, including:

- browser automation with Selenium
- mobile-oriented workflow automation patterns
- separating shared automation logic from target-specific selectors
- config-driven workflow design
- handling unstable UI states such as stale elements, overlays, and scroll-related edge cases

The goal is to keep the reusable automation logic visible and easy to study, while moving target-specific details into external configuration.

## What is included

The current public version focuses on the generic mobile automation layer and a few small entrypoints built on top of it:

- `mobile_listing_refresh.py`
- `mobile_price_adjust.py`
- `mobile_description_refresh.py`

These scripts share the same automation core and differ mainly in the workflow flags they enable.

## Project structure

- `marketplace_core.py`  
  Shared automation core for listing-style workflows.

- `target_profiles.py`  
  Loads target definitions from JSON files so that selectors and target metadata can be kept outside the main logic.

- `automation_targets.example.json`  
  Example structure for target profiles, showing how selectors, labels, and target-level settings can be organized without coupling the repository to a specific setup.

- `config.example.json`  
  Minimal example of user-level configuration for local experimentation.

- `requirements.txt`  
  Python dependencies used by the project.

## Design approach

One of the main ideas behind this repository is keeping the automation logic as generic as possible.

Instead of hardcoding every selector directly into each script, the project uses a profile-based approach. The reusable logic lives in the Python modules, while target-specific details are described in external JSON profiles. This makes it easier to study the core behavior on its own and experiment with different target definitions.

It also keeps the control flow, retries, and interaction strategies in one place instead of spreading them across many one-off scripts.

## Local setup

1. Install the dependencies from `requirements.txt`.
2. Use `automation_targets.example.json` as a starting point for your own local target definitions.
3. Adjust selectors, package names, labels, or URLs to match the interface you want to experiment with.
4. If a local run needs user-specific values, use `config.example.json` as a template for your own config file.

## Scope

This repository is best read as a reusable automation core and code organization example focused on UI automation patterns, configuration structure, and iterative tool-building in Python.
