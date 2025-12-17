import sys
import json

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print('Failed to read input JSON', file=sys.stderr)
        sys.exit(2)

    # inputs may be passed as strings
    create = data.get('create_secret_versions')
    # accept booleans or strings
    if isinstance(create, str):
        create = create.lower() in ('1','true','yes')
    create = bool(create)

    gemini = data.get('gemini', '') or ''
    anthropic = data.get('anthropic', '') or ''
    custom = data.get('custom', '') or ''

    def empty(s):
        return len(s.strip()) == 0

    if create and (empty(gemini) or empty(anthropic) or empty(custom)):
        msg = (
            'Terraform requires secret values when create_secret_versions=true.\n'
            'Please provide `gemini_api_key_value`, `anthropic_api_key_value`, and `custom_llm_api_key_value`\n'
            'in terraform.tfvars or pass them via TF_VAR_* environment variables.'
        )
        print(msg, file=sys.stderr)
        sys.exit(1)

    print(json.dumps({'ok': 'true'}))

if __name__ == '__main__':
    main()
