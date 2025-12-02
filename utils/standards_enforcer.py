"""Standards enforcement system with retry logic for agents."""
from typing import Dict, Callable, Any
from utils.resume_standards import validate_resume_against_standards, RESUME_STANDARDS


class StandardsEnforcer:
    """Enforces resume standards with retry logic for agents."""

    def __init__(self, max_retries: int = 2):
        """
        Initialize enforcer.

        Args:
            max_retries: Maximum number of retry attempts if standards violated
        """
        self.max_retries = max_retries

    def enforce_with_retry(
        self,
        agent_func: Callable,
        agent_name: str,
        input_resume: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute agent with standards enforcement and retry logic.

        Args:
            agent_func: The agent function to execute (must return modified_resume)
            agent_name: Name of the agent for logging
            input_resume: Original resume before modification
            *args, **kwargs: Additional arguments for agent function

        Returns:
            Dictionary containing:
                - modified_resume: The final resume after enforcement
                - validation_result: Validation details
                - retry_count: Number of retries performed
                - enforcement_log: List of issues and fixes
        """
        enforcement_log = []
        retry_count = 0

        print(f"[STANDARDS] {agent_name}: Starting with {len(input_resume.split())} words")

        for attempt in range(self.max_retries + 1):
            # Execute agent
            result = agent_func(*args, **kwargs)

            # Get the modified resume
            if isinstance(result, dict):
                modified_resume = result.get('modified_resume') or result.get('optimized_resume')
            else:
                modified_resume = result

            if not modified_resume:
                print(f"[STANDARDS] {agent_name}: No resume returned!")
                return {
                    "modified_resume": input_resume,
                    "error": "Agent returned no resume"
                }

            # Validate against standards
            validation = validate_resume_against_standards(modified_resume)

            word_count = validation['word_count']
            print(f"[STANDARDS] {agent_name}: Attempt {attempt + 1} - {word_count} words, {len(validation['issues'])} issues")

            # Log issues
            for issue in validation['issues']:
                enforcement_log.append({
                    "attempt": attempt + 1,
                    "severity": issue['severity'],
                    "category": issue['category'],
                    "description": issue['description']
                })
                print(f"[STANDARDS]   [{issue['severity']}] {issue['description']}")

            # Check if we have critical issues
            critical_issues = [i for i in validation['issues'] if i['severity'] == 'CRITICAL']

            if not critical_issues or attempt >= self.max_retries:
                # Success or max retries reached
                if critical_issues:
                    print(f"[STANDARDS] {agent_name}: Max retries reached with {len(critical_issues)} critical issues")
                    # Apply programmatic fixes as fallback
                    modified_resume = self._apply_programmatic_fixes(modified_resume, critical_issues)
                    enforcement_log.append({
                        "attempt": attempt + 1,
                        "action": "Applied programmatic fixes"
                    })
                else:
                    print(f"[STANDARDS] {agent_name}: ✓ Standards validated")

                return {
                    "modified_resume": modified_resume,
                    "validation_result": validation,
                    "retry_count": retry_count,
                    "enforcement_log": enforcement_log,
                    "input_word_count": len(input_resume.split()),
                    "output_word_count": word_count
                }

            # Retry with feedback
            retry_count += 1
            print(f"[STANDARDS] {agent_name}: Retrying with standards feedback...")

            # Inject standards feedback into the agent
            standards_feedback = self._generate_feedback(validation['issues'])
            kwargs['standards_feedback'] = standards_feedback

    def _apply_programmatic_fixes(self, resume: str, issues: list) -> str:
        """
        Apply programmatic fixes for common critical issues.

        Args:
            resume: Resume content
            issues: List of critical issues

        Returns:
            Fixed resume
        """
        from utils.resume_validator import ResumeStructureValidator

        print("[STANDARDS] Applying programmatic fixes...")

        validator = ResumeStructureValidator()
        result = validator.validate_and_fix(resume, original_resume=None)

        if result['fixes_applied']:
            print(f"[STANDARDS] Applied {len(result['fixes_applied'])} fixes:")
            for fix in result['fixes_applied']:
                print(f"[STANDARDS]   - {fix}")

        return result['fixed_resume']

    def _generate_feedback(self, issues: list) -> str:
        """
        Generate feedback message for agent retry.

        Args:
            issues: List of validation issues

        Returns:
            Feedback string to inject into agent prompt
        """
        feedback = "\n\n**CRITICAL: Standards Validation Failed. You MUST fix these issues:**\n\n"

        critical = [i for i in issues if i['severity'] == 'CRITICAL']
        if critical:
            feedback += "**CRITICAL ISSUES:**\n"
            for issue in critical:
                feedback += f"- [{issue['category']}] {issue['description']}\n"

        feedback += f"\n**Please review the Resume Structure Standards and ensure compliance.**\n"
        feedback += f"\nKey reminders:\n"
        feedback += f"- Job metadata lines MUST end with backslash (\\)\n"
        feedback += f"- Each job MUST have an italicized headline immediately after metadata\n"
        feedback += f"- NO blank lines between metadata and headline\n"

        return feedback


def create_enforced_agent_wrapper(agent_class, method_name: str):
    """
    Create a wrapper that adds standards enforcement to an agent method.

    Args:
        agent_class: The agent class
        method_name: Name of the method to wrap

    Returns:
        Wrapped method with enforcement
    """
    def wrapper(self, *args, **kwargs):
        enforcer = StandardsEnforcer(max_retries=1)

        # Get the original method
        original_method = getattr(agent_class, method_name)

        # Get input resume from args
        input_resume = args[0] if args else kwargs.get('resume_content') or kwargs.get('modified_resume')

        # Execute with enforcement
        result = enforcer.enforce_with_retry(
            agent_func=lambda: original_method(self, *args, **kwargs),
            agent_name=f"{agent_class.__name__}.{method_name}",
            input_resume=input_resume,
            *args,
            **kwargs
        )

        return result['modified_resume']

    return wrapper
