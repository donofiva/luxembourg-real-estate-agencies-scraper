# Contributing to Luxembourg Real Estate Agencies Scraper

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- A clear description of the feature
- Why it would be useful
- Potential implementation approach (optional)

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**:
   - Follow the existing code style
   - Add docstrings to new functions/classes
   - Update README.md if needed
3. **Test your changes**: Ensure the scraper still works
4. **Commit your changes**: Use clear, descriptive commit messages
5. **Push to your fork** and submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/LuxembourgAgenciesExtractor.git
cd LuxembourgAgenciesExtractor

# Run setup script
./setup.sh

# Activate virtual environment
source .venv/bin/activate
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Write clear, concise docstrings
- Keep functions focused and modular
- Prefer readability over cleverness

## Testing

Before submitting a PR:
1. Run the scraper to ensure it works
2. Test with edge cases if applicable
3. Verify no new dependencies are required (or update requirements.txt)

## Questions?

Feel free to open an issue for any questions or clarifications.

---

By contributing, you agree that your contributions will be licensed under the MIT License.
