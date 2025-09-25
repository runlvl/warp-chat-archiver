# Contributing to Warp Chat Archiver

First off, thank you for considering contributing to Warp Chat Archiver! 🎉

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## What we are looking for

Warp Chat Archiver is an open source project and we love to receive contributions from our community — you! There are many ways to contribute, from writing tutorials or blog posts, improving the documentation, submitting bug reports and feature requests or writing code which can be incorporated into the main project itself.

### Types of Contributions

- 🐛 **Bug Reports**: Report bugs using GitHub issues
- ✨ **Feature Requests**: Suggest new features or improvements
- 📖 **Documentation**: Improve README, add examples, write tutorials
- 🧪 **Testing**: Add test cases, improve test coverage
- 💻 **Code**: Fix bugs, implement new features
- 🎨 **Design**: UI/UX improvements, icons, themes
- 🌍 **Localization**: Translate the application to other languages

## Getting Started

### Development Environment Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/warp-chat-archiver.git
   cd warp-chat-archiver
   ```

3. **Set up the development environment**:
   ```bash
   # Create a virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number
   ```

5. **Test that everything works**:
   ```bash
   python warp_archiver_gui.py
   python -m pytest tests/
   ```

### Development Workflow

1. **Make your changes** in your feature branch
2. **Add or update tests** as needed
3. **Ensure all tests pass**:
   ```bash
   python -m pytest tests/ -v
   ```
4. **Format your code** (we use Black):
   ```bash
   black .
   isort .
   ```
5. **Lint your code**:
   ```bash
   flake8 .
   ```
6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add awesome feature"
   ```
7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a Pull Request** on GitHub

## Pull Request Guidelines

### Before Submitting

- [ ] Run the full test suite and ensure all tests pass
- [ ] Format your code with Black and sort imports with isort  
- [ ] Update documentation if needed
- [ ] Add tests for any new functionality
- [ ] Update CHANGELOG.md if applicable

### PR Description Template

When creating a pull request, please include:

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested this change manually

## Screenshots (if applicable)
Add screenshots to help explain your changes

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
```

## Coding Standards

### Python Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Import sorting**: Use isort
- **String quotes**: Prefer double quotes

### Code Organization

```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import tkinter as tk
from tkinter import ttk

# Local application imports
from database_manager import DatabaseManager
from export_manager import ExportManager
```

### Documentation

- Use **docstrings** for all modules, classes, and functions
- Follow [Google docstring format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Include type hints where beneficial

```python
def export_conversations(self, conversations: List[Dict], 
                        output_path: str, format: str = "json") -> bool:
    """Export conversations to specified format.
    
    Args:
        conversations: List of conversation dictionaries
        output_path: Path where to save the export file
        format: Export format (json, csv, html, markdown)
        
    Returns:
        True if export was successful, False otherwise
        
    Raises:
        ExportError: If the export format is not supported
    """
```

### Testing

- Write tests for new functionality
- Aim for good test coverage
- Use descriptive test names
- Group related tests in classes

```python
class TestExportManager:
    def test_export_to_json_creates_valid_file(self):
        """Test that JSON export creates a valid JSON file."""
        # Test implementation
        pass
        
    def test_export_to_json_handles_empty_conversations(self):
        """Test JSON export with empty conversation list."""
        # Test implementation
        pass
```

## Issue Guidelines

### Bug Reports

When filing a bug report, please include:

- **System information**: OS, Python version, GUI toolkit version
- **Steps to reproduce**: Clear steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Screenshots**: If applicable
- **Logs**: Any relevant error messages or log output

Use this template:

```markdown
**System Information:**
- OS: [e.g. Ubuntu 22.04, Windows 11, macOS 13]
- Python Version: [e.g. 3.11.2]
- Warp Chat Archiver Version: [e.g. 1.0.0]

**Bug Description:**
A clear and concise description of what the bug is.

**To Reproduce:**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior:**
A clear description of what you expected to happen.

**Screenshots:**
If applicable, add screenshots to help explain your problem.

**Additional Context:**
Add any other context about the problem here.
```

### Feature Requests

For feature requests, please include:

- **Use case**: Why this feature would be useful
- **Description**: What the feature should do
- **Alternatives**: Other ways to achieve the same goal
- **Implementation ideas**: If you have thoughts on implementation

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Version number is bumped in `version.py`
- [ ] CHANGELOG.md is updated
- [ ] Git tag is created
- [ ] GitHub release is created

## Community

### Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Wiki**: For documentation and tutorials

### Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor statistics

## Additional Resources

- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

## Questions?

Don't hesitate to ask! Create an issue or start a discussion if you have any questions about contributing.

Thank you for contributing to Warp Chat Archiver! 🚀