#!/usr/bin/env python3
"""Read-only entry for a neutral Curator installation."""
import argparse
import json
from curator_policy import PolicyError, decision, inspect_policy, load_policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('status', 'validate'))
    parser.add_argument('--policy', required=True)
    args = parser.parse_args()
    try:
        result = inspect_policy(load_policy(args.policy))
        result['valid'] = True
    except (PolicyError, OSError) as exc:
        result = decision('unavailable' if isinstance(exc, OSError) or getattr(exc, 'code', '').endswith('_unavailable') else 'blocked', getattr(exc, 'code', 'read_failed'))
        result['valid'] = False
    print(json.dumps(result, indent=2))
    return 0 if result['valid'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
