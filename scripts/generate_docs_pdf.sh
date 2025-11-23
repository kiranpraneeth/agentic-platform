#!/bin/bash

# Script to generate PDF versions of documentation
# Requires: pandoc, wkhtmltopdf (for Mermaid diagrams)
#
# Install dependencies:
#   macOS: brew install pandoc wkhtmltopdf
#   Ubuntu: sudo apt-get install pandoc wkhtmltopdf
#   Docker: Use the provided Docker command below

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="docs"
OUTPUT_DIR="docs/pdf"
TIMESTAMP=$(date +"%Y-%m-%d")

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Documentation PDF Generator${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo -e "${RED}Error: pandoc is not installed${NC}"
    echo ""
    echo "Install options:"
    echo "  macOS:   brew install pandoc"
    echo "  Ubuntu:  sudo apt-get install pandoc"
    echo "  Docker:  docker run --rm -v \$(pwd):/data pandoc/latex:latest ..."
    echo ""
    exit 1
fi

echo -e "${YELLOW}Pandoc version:${NC} $(pandoc --version | head -n 1)"
echo ""

# Function to generate PDF
generate_pdf() {
    local input_file=$1
    local output_name=$2
    local title=$3

    echo -e "${YELLOW}Generating:${NC} $output_name.pdf"

    pandoc "$input_file" \
        -o "$OUTPUT_DIR/$output_name.pdf" \
        --pdf-engine=xelatex \
        --variable=geometry:margin=1in \
        --variable=fontsize:11pt \
        --variable=documentclass:article \
        --variable=mainfont:"Arial" \
        --variable=monofont:"Courier New" \
        --toc \
        --toc-depth=3 \
        --highlight-style=tango \
        --metadata title="$title" \
        --metadata date="$TIMESTAMP" \
        --metadata author="Agentic Platform Team" \
        2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Created: $OUTPUT_DIR/$output_name.pdf"
    else
        echo -e "${RED}✗${NC} Failed to create: $output_name.pdf"
    fi
    echo ""
}

# Generate PDFs for main documentation
echo "Generating PDF documentation..."
echo ""

# Check if files exist
if [ ! -f "$DOCS_DIR/QUICK_REFERENCE.md" ]; then
    echo -e "${RED}Error: Documentation files not found in $DOCS_DIR/${NC}"
    exit 1
fi

# Generate each PDF
generate_pdf "$DOCS_DIR/QUICK_REFERENCE.md" \
    "Quick_Reference_$TIMESTAMP" \
    "Agentic Platform - Quick Reference"

generate_pdf "$DOCS_DIR/CODEBASE_DEEP_DIVE.md" \
    "Codebase_Deep_Dive_$TIMESTAMP" \
    "Agentic Platform - Codebase Deep Dive"

generate_pdf "$DOCS_DIR/ARCHITECTURE_DECISIONS.md" \
    "Architecture_Decisions_$TIMESTAMP" \
    "Agentic Platform - Architecture Decisions"

generate_pdf "$DOCS_DIR/README.md" \
    "Documentation_Guide_$TIMESTAMP" \
    "Agentic Platform - Documentation Guide"

# Generate combined PDF
echo -e "${YELLOW}Generating:${NC} Complete_Documentation.pdf"

pandoc \
    "$DOCS_DIR/README.md" \
    "$DOCS_DIR/QUICK_REFERENCE.md" \
    "$DOCS_DIR/CODEBASE_DEEP_DIVE.md" \
    "$DOCS_DIR/ARCHITECTURE_DECISIONS.md" \
    -o "$OUTPUT_DIR/Complete_Documentation_$TIMESTAMP.pdf" \
    --pdf-engine=xelatex \
    --variable=geometry:margin=1in \
    --variable=fontsize:11pt \
    --variable=documentclass:article \
    --variable=mainfont:"Arial" \
    --variable=monofont:"Courier New" \
    --toc \
    --toc-depth=2 \
    --highlight-style=tango \
    --metadata title="Agentic Platform - Complete Documentation" \
    --metadata date="$TIMESTAMP" \
    --metadata author="Agentic Platform Team" \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Created: $OUTPUT_DIR/Complete_Documentation_$TIMESTAMP.pdf"
else
    echo -e "${RED}✗${NC} Failed to create complete documentation PDF"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PDF Generation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Generated files:"
ls -lh "$OUTPUT_DIR"/*.pdf | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo -e "${YELLOW}Note:${NC} Mermaid diagrams are not included in PDFs."
echo "      View markdown files in GitHub or VS Code for full diagrams."
echo ""

# Create symlinks to latest versions (without timestamp)
cd "$OUTPUT_DIR"
ln -sf "Quick_Reference_$TIMESTAMP.pdf" "Quick_Reference_Latest.pdf"
ln -sf "Codebase_Deep_Dive_$TIMESTAMP.pdf" "Codebase_Deep_Dive_Latest.pdf"
ln -sf "Architecture_Decisions_$TIMESTAMP.pdf" "Architecture_Decisions_Latest.pdf"
ln -sf "Complete_Documentation_$TIMESTAMP.pdf" "Complete_Documentation_Latest.pdf"
cd - > /dev/null

echo -e "${GREEN}Latest versions linked:${NC}"
echo "  $OUTPUT_DIR/Quick_Reference_Latest.pdf"
echo "  $OUTPUT_DIR/Codebase_Deep_Dive_Latest.pdf"
echo "  $OUTPUT_DIR/Architecture_Decisions_Latest.pdf"
echo "  $OUTPUT_DIR/Complete_Documentation_Latest.pdf"
echo ""
