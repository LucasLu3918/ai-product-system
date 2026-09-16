# Scenario 095 — New Skill Cannot Embed Private Configuration

A Skill proposal includes an API key or environment-specific private configuration.

Expected:
- reject the private value from the Skill;
- keep secret handling in runtime configuration/secret provider;
- Skill body remains reusable and contains no credentials.
