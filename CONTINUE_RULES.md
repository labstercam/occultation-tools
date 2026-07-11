# Continue Extension Rules

## For AI Assistants using Continue in VS Code

You are working on the `occultation-tools` GitHub repository via Continue extension with OpenRouter.

### Project Structure
- **occultation-manager/** - SharpCap add-in for automated occultation workflow (Python)
- **gps-timing-analysis/** - Python toolkit for timing validation and calibration

### Code Formatting Rules
1. Always include language and file path in code blocks:
   ```python occultation-manager/python/main.py```
   ```python gps-timing-analysis/python/analysis.py```

2. Use concise snippets with placeholder comments:
   ```python
   # ... existing code ...
   
   {{ modified code here }}
   
   # ... rest of function ...
   ```

3. Restate function/class context when modifying existing code

### VS Code Workflow
- Users can apply changes via Apply Button
- Can switch to agent mode via dropdown if needed
- Focus on relevant modifications only
- Provide clear explanations for significant changes

### Project-Specific Guidelines
- Follow Python best practices and PEP8
- Consider Windows compatibility for SharpCap add-in
- Respect BSD 3-Clause license
- Check .gitignore rules
- Be mindful of timing accuracy requirements for GPS/NTP analysis
- Check existing patterns before adding new code

### Repository Considerations
- This is a GitHub repository
- Check for existing files before creating new ones
- Follow the established directory structure
- Consider cross-file dependencies