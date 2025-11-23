# Utility Scripts

This directory contains utility scripts for the Agentic Platform.

## Available Scripts

### 📄 generate_docs_pdf.sh

Generate PDF versions of all documentation.

**Requirements**:
- `pandoc` - Document converter
- `xelatex` - PDF engine (usually comes with TeX Live)

**Installation**:

```bash
# macOS
brew install pandoc
brew install --cask mactex-no-gui  # For xelatex

# Ubuntu/Debian
sudo apt-get install pandoc texlive-xetex texlive-fonts-recommended

# Check installation
pandoc --version
xelatex --version
```

**Usage**:

```bash
# From project root
./scripts/generate_docs_pdf.sh

# Or with make
make docs-pdf
```

**Output**:
- `docs/pdf/Quick_Reference_2025-01-09.pdf`
- `docs/pdf/Codebase_Deep_Dive_2025-01-09.pdf`
- `docs/pdf/Architecture_Decisions_2025-01-09.pdf`
- `docs/pdf/Complete_Documentation_2025-01-09.pdf`

Plus `_Latest.pdf` symlinks for easy access.

**Note**: Mermaid diagrams are not rendered in PDFs. View the markdown files in GitHub or VS Code to see diagrams.

**Alternative - Using Docker**:

If you don't want to install dependencies locally:

```bash
# Generate PDFs using Docker
docker run --rm -v $(pwd):/data pandoc/latex:latest \
  generate_docs_pdf.sh
```

---

### 🌱 seed_dev_data.py

Seed development database with test data.

**Usage**:

```bash
# With Docker
docker-compose exec api python scripts/seed_dev_data.py

# Local development
poetry run python scripts/seed_dev_data.py
```

**Creates**:
- Default tenant (Example Corp)
- Admin user (admin@example.com / admin123)
- Sample agents

---

### 🗄️ init-db.sql

Database initialization SQL script.

**Usage**:

Automatically run by PostgreSQL container on first startup via docker-compose.yml.

**Manual execution**:

```bash
psql -U postgres -d agentic_platform -f scripts/init-db.sql
```

---

## Adding New Scripts

When adding new utility scripts:

1. **Make executable**:
   ```bash
   chmod +x scripts/your_script.sh
   ```

2. **Add shebang**:
   ```bash
   #!/bin/bash
   # or
   #!/usr/bin/env python3
   ```

3. **Document in this README**:
   - Purpose
   - Requirements
   - Usage examples
   - Output description

4. **Add to Makefile** (optional):
   ```makefile
   .PHONY: your-command
   your-command:
       ./scripts/your_script.sh
   ```

---

## Script Guidelines

- ✅ Include error handling (`set -e` for bash)
- ✅ Add helpful output messages
- ✅ Check for required dependencies
- ✅ Use colors for better readability
- ✅ Provide usage examples in comments
- ✅ Test in both Docker and local environments
- ✅ Add to CI/CD if applicable

---

**Questions?** Open an issue or ask the team!
