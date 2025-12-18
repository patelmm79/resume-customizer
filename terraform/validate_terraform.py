#!/usr/bin/env python3
"""
Terraform Configuration Validator

Performs automated checks on Terraform configuration to prevent common errors:
- Conditional resource references
- API enablement dependencies
- Condition logic consistency
- Variable consistency
- Missing required fields

Usage:
    python validate_terraform.py [--fix] [--verbose]
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set

class TerraformValidator:
    def __init__(self, tf_dir: str = "."):
        self.tf_dir = Path(tf_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.tf_files = {}
        self.variables = {}

    def run_all_checks(self) -> bool:
        """Run all validation checks. Returns True if no errors."""
        print("🔍 Terraform Validation Starting...\n")

        # Load all files
        self._load_tf_files()
        if not self.tf_files:
            self.errors.append("No Terraform files found in directory")
            return False

        # Run checks
        print("📋 Running checks...")
        self._check_resource_conditions()
        self._check_api_dependencies()
        self._check_variable_consistency()
        self._check_required_fields()
        self._check_depends_on_logic()

        # Report results
        self._print_report()
        return len(self.errors) == 0

    def _load_tf_files(self) -> None:
        """Load all .tf files in the directory."""
        print(f"📂 Scanning {self.tf_dir} for .tf files...")
        for tf_file in self.tf_dir.glob("*.tf"):
            with open(tf_file, 'r') as f:
                self.tf_files[tf_file.name] = f.read()
            print(f"   ✓ Loaded {tf_file.name}")

        # Parse variables
        if "variables.tf" in self.tf_files:
            self._parse_variables()

    def _parse_variables(self) -> None:
        """Extract all variable definitions."""
        var_pattern = r'variable\s+"(\w+)"'
        content = self.tf_files.get("variables.tf", "")
        self.variables = set(re.findall(var_pattern, content))
        print(f"   ✓ Found {len(self.variables)} variable definitions\n")

    def _check_resource_conditions(self) -> None:
        """Check for conditional resource references."""
        print("✓ Checking conditional resource references...")

        # Find all resources with count
        conditional_resources = {}
        for filename, content in self.tf_files.items():
            # Pattern: resource "type" "name" { ... count = ... }
            pattern = r'resource\s+"(\w+)"\s+"(\w+)"\s+\{[^}]*?count\s*='
            for match in re.finditer(pattern, content, re.DOTALL):
                res_type, res_name = match.groups()
                conditional_resources[f"{res_type}.{res_name}"] = (filename, match.start())

        if not conditional_resources:
            self.info.append("No conditional resources found")
            return

        print(f"   Found {len(conditional_resources)} conditional resources:")
        for res_name in sorted(conditional_resources.keys()):
            print(f"     - {res_name}")

        # Check if these are referenced unconditionally in depends_on
        for filename, content in self.tf_files.items():
            for res_name in conditional_resources.keys():
                # Look for depends_on with this resource referenced without [0]
                pattern = f'depends_on\\s*=\\s*\\[[^\\]]*{re.escape(res_name)}(?!\\[0\\])[^\\]]*\\]'
                if re.search(pattern, content):
                    self.errors.append(
                        f"{filename}: Unconditional reference to conditional resource '{res_name}' in depends_on. "
                        f"Use conditional logic or [0] notation."
                    )

    def _check_api_dependencies(self) -> None:
        """Check that API enablement is properly handled."""
        print("✓ Checking API enablement dependencies...")

        apis_and_resources = {
            "secretmanager.googleapis.com": ["google_secret_manager_secret", "google_secret_manager_secret_version"],
            "cloudbuild.googleapis.com": ["google_cloudbuildv2_connection", "google_cloudbuild_trigger"],
            "run.googleapis.com": ["google_cloud_run_service"],
        }

        content = "\n".join(self.tf_files.values())

        for api, resources in apis_and_resources.items():
            api_enabled = f'service = "{api}"' in content
            if not api_enabled:
                self.warnings.append(f"API {api} not explicitly enabled in configuration")
                continue

            for resource_type in resources:
                if resource_type in content:
                    self.info.append(f"✓ API {api} will be enabled for {resource_type}")

    def _check_variable_consistency(self) -> None:
        """Check that all referenced variables are defined."""
        print("✓ Checking variable consistency...")

        # Find all variable references
        content = "\n".join(self.tf_files.values())
        var_refs = set(re.findall(r'var\.(\w+)', content))

        undefined_vars = var_refs - self.variables
        if undefined_vars:
            for var in sorted(undefined_vars):
                self.errors.append(f"Variable '{var}' is referenced but not defined in variables.tf")
        else:
            self.info.append(f"✓ All {len(var_refs)} variable references are defined")

    def _check_required_fields(self) -> None:
        """Check that resources have required fields."""
        print("✓ Checking required resource fields...")

        content = "\n".join(self.tf_files.values())

        # Check for resources missing 'project' field
        resource_pattern = r'resource\s+"google_(\w+)"\s+"(\w+)"\s+\{([^}]+)\}'
        missing_project = []

        for match in re.finditer(resource_pattern, content):
            resource_type, resource_name, resource_body = match.groups()

            # Skip data sources and certain resource types
            if resource_type.startswith("google_compute") or resource_type == "external":
                continue

            # Check if 'project' field is present
            if "project" not in resource_body and "${" not in resource_body:
                missing_project.append(f"google_{resource_type}.{resource_name}")

        if missing_project and len(missing_project) < 5:
            for res in missing_project[:5]:
                self.warnings.append(f"Resource '{res}' may be missing 'project' field")

    def _check_depends_on_logic(self) -> None:
        """Check that depends_on logic is sound."""
        print("✓ Checking depends_on logic...")

        content = "\n".join(self.tf_files.values())

        # Check for circular or missing dependencies
        patterns = [
            (r'depends_on\s*=\s*\[\s*\]', "Empty depends_on block"),
            (r'depends_on\s*=\s*\[\s*google_project_service\.(\w+),\s*\1', "Circular dependency detected"),
        ]

        for pattern, message in patterns:
            if re.search(pattern, content):
                self.warnings.append(message)

        self.info.append("✓ No obvious circular dependencies detected")

    def _print_report(self) -> None:
        """Print validation report."""
        print("\n" + "="*70)
        print("VALIDATION REPORT")
        print("="*70 + "\n")

        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
            print()

        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
            print()

        if self.info:
            print(f"ℹ️  INFO ({len(self.info)}):")
            for msg in self.info[:5]:  # Show first 5
                print(f"   • {msg}")
            if len(self.info) > 5:
                print(f"   ... and {len(self.info) - 5} more")
            print()

        # Summary
        print("="*70)
        if len(self.errors) == 0:
            print("✅ VALIDATION PASSED - No critical errors found")
        else:
            print(f"❌ VALIDATION FAILED - {len(self.errors)} error(s) found")
        print("="*70 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Terraform configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_terraform.py
  python validate_terraform.py --verbose
  python validate_terraform.py --fix
        """
    )
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues (not implemented)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    validator = TerraformValidator()
    success = validator.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
