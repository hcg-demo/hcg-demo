"""Pre-deploy validation gate. Run: python gates/validate_config.py"""
import sys

def main():
    errors = []
    # Check required paths
    import os
    for path in ['src', 'scripts', 'docs', 'Sample Data']:
        if not os.path.isdir(path):
            errors.append(f"Missing: {path}/")
    if errors:
        print("Validation FAILED:", errors)
        sys.exit(1)
    print("Validation OK: structure check passed")
    return 0

if __name__ == '__main__':
    sys.exit(main())
