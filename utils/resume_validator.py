"""Resume structure validator and fixer."""
import re
from typing import Dict, List, Tuple


class ResumeStructureValidator:
    """Validates and fixes resume structure issues, particularly in Experience section."""

    def __init__(self):
        """Initialize the validator."""
        # Pattern to match job metadata line (should end with backslash)
        self.job_metadata_pattern = re.compile(
            r'\*\*[^*]+\*\*\s*\|.*\|.*\|.*\*[^*]+\*'
        )
        # Pattern to match job headline (italicized line)
        self.job_headline_pattern = re.compile(r'^\*[^*]+\*$')

    def validate_and_fix(self, resume: str, original_resume: str = None) -> Dict:
        """
        Validate resume structure and fix issues.

        Args:
            resume: The resume to validate
            original_resume: Optional original resume to extract missing headlines

        Returns:
            Dictionary with:
                - fixed_resume: str (corrected resume)
                - issues_found: List[str] (list of issues detected)
                - fixes_applied: List[str] (list of fixes applied)
                - is_valid: bool (True if no critical issues)
        """
        issues_found = []
        fixes_applied = []

        lines = resume.split('\n')
        fixed_lines = []
        i = 0

        # Extract job headlines from original if provided
        original_headlines = {}
        if original_resume:
            original_headlines = self._extract_job_headlines(original_resume)

        # Identify Experience section boundaries
        in_experience_section = False

        while i < len(lines):
            line = lines[i]

            # Check if we're entering or leaving the Experience section
            if self._is_section_header(line, "Experience"):
                in_experience_section = True
                fixed_lines.append(line)
                i += 1
                continue
            elif self._is_section_header(line) and in_experience_section:
                # Entering a different section, stop validating
                in_experience_section = False

            # Only validate job metadata lines within Experience section
            if in_experience_section and self._is_job_metadata_line(line):
                job_title = self._extract_job_title(line)

                # Issue 1: Check if backslash is present at end
                if not line.rstrip().endswith('\\'):
                    issues_found.append(f"Job metadata missing backslash: {job_title}")
                    line = line.rstrip() + '\\'
                    fixes_applied.append(f"Added backslash to job metadata: {job_title}")

                fixed_lines.append(line)
                i += 1

                # Issue 2: Check if next line is the job headline
                if i < len(lines):
                    next_line = lines[i].strip()

                    # Check for blank lines between metadata and headline
                    blank_count = 0
                    while i < len(lines) and not lines[i].strip():
                        blank_count += 1
                        i += 1

                    if blank_count > 0:
                        issues_found.append(
                            f"Found {blank_count} blank line(s) between metadata and headline for: {job_title}"
                        )
                        fixes_applied.append(
                            f"Removed {blank_count} blank line(s) after metadata for: {job_title}"
                        )

                    # Now check if we have a headline
                    if i < len(lines):
                        potential_headline = lines[i].strip()

                        if self._is_job_headline(potential_headline):
                            # Good - headline exists
                            fixed_lines.append(lines[i])
                            i += 1
                        else:
                            # Issue 3: Missing headline - try to recover from original
                            issues_found.append(f"CRITICAL: Missing job headline for: {job_title}")

                            if job_title in original_headlines:
                                recovered_headline = original_headlines[job_title]
                                fixed_lines.append(recovered_headline)
                                fixes_applied.append(
                                    f"Recovered missing headline from original for: {job_title}"
                                )
                            else:
                                # Create a placeholder headline
                                placeholder = f"*Role description for {job_title}*"
                                fixed_lines.append(placeholder)
                                fixes_applied.append(
                                    f"Created placeholder headline for: {job_title}"
                                )

                            # Don't increment i - process the current line normally
                else:
                    # Metadata is last line - missing headline
                    issues_found.append(f"CRITICAL: Job metadata at end of file missing headline: {job_title}")

                    if job_title in original_headlines:
                        recovered_headline = original_headlines[job_title]
                        fixed_lines.append(recovered_headline)
                        fixes_applied.append(f"Recovered missing headline for: {job_title}")
            else:
                # Not a job metadata line, keep as-is
                fixed_lines.append(line)
                i += 1

        fixed_resume = '\n'.join(fixed_lines)

        # Determine if valid (no critical issues)
        critical_issues = [issue for issue in issues_found if "CRITICAL" in issue]
        is_valid = len(critical_issues) == 0

        return {
            "fixed_resume": fixed_resume,
            "issues_found": issues_found,
            "fixes_applied": fixes_applied,
            "is_valid": is_valid,
            "had_critical_issues": len(critical_issues) > 0
        }

    def _is_job_metadata_line(self, line: str) -> bool:
        """
        Check if line is a job metadata line.

        Args:
            line: Line to check

        Returns:
            True if this is job metadata
        """
        # Must have bold title, pipes, and date
        return bool(self.job_metadata_pattern.search(line))

    def _is_job_headline(self, line: str) -> bool:
        """
        Check if line is a job headline (italicized description).

        Args:
            line: Line to check

        Returns:
            True if this is a job headline
        """
        return bool(self.job_headline_pattern.match(line))

    def _extract_job_title(self, line: str) -> str:
        """
        Extract job title from metadata line.

        Args:
            line: Job metadata line

        Returns:
            Job title (cleaned)
        """
        # Extract text between first ** and **
        match = re.search(r'\*\*([^*]+)\*\*', line)
        if match:
            return match.group(1).strip()
        return "Unknown Job"

    def _is_section_header(self, line: str, section_name: str = None) -> bool:
        """
        Check if line is a section header.

        Args:
            line: Line to check
            section_name: Optional specific section name to match

        Returns:
            True if this is a section header
        """
        stripped = line.strip()

        # Common section headers
        section_headers = [
            "## Experience", "## Professional Experience", "## Work Experience",
            "## Education", "## Skills", "## Technical Skills",
            "## Certifications", "## Key Achievements", "## Summary",
            "## Projects", "## Publications"
        ]

        if section_name:
            # Check for specific section
            return any(section_name.lower() in header.lower() for header in section_headers if header in stripped)
        else:
            # Check if it's any section header
            return stripped in section_headers or stripped.startswith("## ")

    def _extract_job_headlines(self, resume: str) -> Dict[str, str]:
        """
        Extract all job headlines from a resume's Experience section.

        Args:
            resume: Resume content

        Returns:
            Dictionary mapping job titles to their headlines
        """
        headlines = {}
        lines = resume.split('\n')
        in_experience_section = False

        for i in range(len(lines) - 1):
            line = lines[i]

            # Track Experience section
            if self._is_section_header(line, "Experience"):
                in_experience_section = True
                continue
            elif self._is_section_header(line) and in_experience_section:
                in_experience_section = False
                break

            # Only extract from Experience section
            if in_experience_section and self._is_job_metadata_line(line):
                job_title = self._extract_job_title(line)

                # Check next non-blank line
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1

                if j < len(lines) and self._is_job_headline(lines[j].strip()):
                    headlines[job_title] = lines[j]

        return headlines

    def validate_only(self, resume: str) -> Dict:
        """
        Validate without fixing - just report issues.

        Args:
            resume: Resume to validate

        Returns:
            Dictionary with validation results
        """
        issues = []
        lines = resume.split('\n')
        in_experience_section = False

        for i in range(len(lines)):
            line = lines[i]

            # Track Experience section
            if self._is_section_header(line, "Experience"):
                in_experience_section = True
                continue
            elif self._is_section_header(line) and in_experience_section:
                in_experience_section = False

            # Only validate within Experience section
            if in_experience_section and self._is_job_metadata_line(line):
                job_title = self._extract_job_title(line)

                # Check backslash
                if not line.rstrip().endswith('\\'):
                    issues.append(f"Missing backslash: {job_title}")

                # Check for headline on next line
                if i + 1 < len(lines):
                    # Skip blank lines
                    j = i + 1
                    blank_count = 0
                    while j < len(lines) and not lines[j].strip():
                        blank_count += 1
                        j += 1

                    if blank_count > 0:
                        issues.append(f"Blank lines between metadata and headline: {job_title}")

                    if j < len(lines):
                        if not self._is_job_headline(lines[j].strip()):
                            issues.append(f"CRITICAL: Missing headline for: {job_title}")
                else:
                    issues.append(f"CRITICAL: Missing headline (EOF) for: {job_title}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "critical_count": len([i for i in issues if "CRITICAL" in i])
        }
