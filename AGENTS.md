# Learning Project

This directory is an adaptive learning project.

## Project Structure

* `sources/` contains learning materials supplied by the learner.
* `notes/` contains personalized notes generated during learning.
* `learner/` contains persistent information about demonstrated understanding.
* `curriculum/` contains topic structures, learning objectives, and concept relationships.
* `.pi/skills/` contains project-specific learning tools.
* `.pi/extensions/` contains project-specific Pi extensions.

## Sources

Treat files in `sources/` as the project's primary reference library.

When relevant:

* inspect supplied sources before teaching source-dependent material
* use multiple sources when that improves explanation
* preserve important distinctions between sources
* identify the source used when possible
* never invent quotations, page numbers, sections, or citations
* do not modify source documents unless explicitly instructed

Sources may include:

* textbooks
* PDFs
* lecture notes
* papers
* manuals
* documentation
* personal notes
* problem sets
* reference material

## Learning Notes

Store useful personalized learning material in `notes/`.

Notes should summarize the learner's developed understanding rather than simply reproduce the conversation.

Include, where useful:

* motivation
* core intuition
* diagrams
* definitions
* formulas
* important terms
* worked examples
* derivations
* proofs or arguments
* common mistakes
* checkpoints
* applications
* source references

## Learner State

Files in `learner/` represent persistent evidence about the learner's understanding.

Use demonstrated performance rather than assumptions.

Relevant evidence may include:

* diagnostic responses
* checkpoint results
* confidence
* mistakes
* misconceptions
* hints required
* successful applications
* successful transfer problems

Do not mark a concept as mastered based on one correct response.

## Curriculum

Files in `curriculum/` describe what is being learned.

A curriculum may contain:

* topics
* concepts
* prerequisites
* learning objectives
* relationships between concepts
* suggested ordering

Curriculum structure should guide teaching without preventing adaptive changes when learner evidence suggests another route is better.

## Session Behavior

At the beginning of a substantial learning session:

1. Identify what the learner wants to learn.
2. Inspect relevant learner state if available.
3. Inspect the curriculum if available.
4. Search relevant project sources.
5. Decide whether a diagnostic is needed.
6. Begin teaching using the adaptive teaching principles from the system instructions.

During the session:

* update understanding based on evidence
* use checkpoints regularly
* retrieve source material when needed
* create visuals when they materially improve understanding
* avoid generating an entire course at once

At the end of a substantial session:

* summarize the main ideas briefly
* preserve useful notes when appropriate
* update learner state when reliable evidence exists
* record concepts that should be reviewed later

## Safety of Project Files

Do not overwrite or delete original materials in `sources/`.

Prefer creating derived material in:

* `notes/`
* `curriculum/`
* `learner/`

Ask before making destructive changes to user-created materials.
