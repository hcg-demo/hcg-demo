# Gates

Quality gates and validation scripts for the HCG Demo project.

- **Pre-deploy validation**: Run before deployment
- **Config checks**: Validate SSM, Secrets Manager, Lambda configs
- **Integration smoke tests**: Quick sanity checks

Run from project root, e.g. `python gates/validate_config.py`
