SEQUENCES FOLDER
================

This folder stores generated SharpCap sequence files (.scs).

The Occultation Manager generates SharpCap sequences for selected occultation
events using templates from data/templates/.

Usage:
1. Generate sequences using the "Create Sequences" button
2. Generated .scs files are saved here automatically
3. Load the generated .scs files in SharpCap to run observations
4. Optionally use the "Run Sequences" button in-app for async execution

Templates:
Working templates are in data/templates/.
Master templates are distributed in resources/templates_master/sequencer/.

Notes:
- This folder is fixed at data/sequences/ in the install layout
- Configuration is stored in data/config/occultation_config.json
- Event cache files are stored in data/events/
- Generated reports are stored in data/reports/
