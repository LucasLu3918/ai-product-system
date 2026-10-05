# Scenario 219: Validation policy taxonomy drift

## Given

Validation shadow selection and graduation use parallel policy fields for full-run classes and protected path prefixes.

## When

The repository runs the validation taxonomy audit.

## Then

The audit reports `ALIGNED` only when both policy sources contain the same unique declarations. Missing, malformed, duplicate, or divergent declarations fail closed with `INCOMPLETE` or `DRIFT`. The audit does not rewrite either configuration or enable selective execution.
