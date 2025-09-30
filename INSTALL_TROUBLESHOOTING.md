# Installation Troubleshooting Guide

This guide helps resolve common installation issues with the Personal AI Retrieval System.

## Common Issues and Solutions

### 1. Dependency Conflicts (PyTorch/Sentence-Transformers)

**Error**: `ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts`

**Solution Options**:

### 2. NumPy 2.x Compatibility Issues

**Error**: `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.3.3 as it may crash`

**Solution**: Downgrade NumPy to 1.x
```bash
pip install "numpy<2.0.0"
# Then reinstall other packages
pip install --force-reinstall torch sentence-transformers
```

**Alternative**: Use the fixed requirements
```bash
pip install -r requirements.txt  # Now includes numpy<2.0.0
```

#### Option A: Use Minimal Requirements (Recommended for Quick Start)
```bash
# Install minimal dependencies (no local embeddings)
pip install -r requirements-minimal.txt
pip install -e .
```

This installs only the essential dependencies and relies on OpenAI/Claude for embeddings.

#### Option B: Install PyTorch First
```bash
# Install PyTorch first, then other dependencies
pip install torch torchvision torchaudio
pip install -r requirements.txt
pip install -e .
```

#### Option C: Use Conda (Recommended for ML Dependencies)
```bash
# Create conda environment
conda create -n personal-ai python=3.11
conda activate personal-ai

# Install PyTorch via conda
conda install pytorch torchvision torchaudio -c pytorch

# Install other dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Python Version Issues

**Error**: Package incompatibility with Python 3.13

**Solution**: Use Python 3.11 or 3.12
```bash
# Using pyenv
pyenv install 3.11.9
pyenv local 3.11.9

# Or using conda
conda create -n personal-ai python=3.11
conda activate personal-ai
```

### 3. macOS Specific Issues

#### M1/M2 Mac Issues
```bash
# For Apple Silicon Macs, use conda for better compatibility
conda create -n personal-ai python=3.11
conda activate personal-ai
conda install pytorch torchvision torchaudio -c pytorch
pip install -r requirements.txt
```

#### Xcode Command Line Tools
```bash
# Install Xcode command line tools if needed
xcode-select --install
```

### 4. ChromaDB Issues

**Error**: ChromaDB installation fails

**Solution**:
```bash
# Install build dependencies
pip install --upgrade pip setuptools wheel
pip install chromadb
```

### 5. Google API Dependencies

**Error**: Google API packages conflict

**Solution**:
```bash
# Install Google packages separately
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

## Installation Methods by Use Case

### For OpenAI/Claude Only (No Local Models)
```bash
pip install -r requirements-minimal.txt
pip install -e .
```

**Pros**: Fast installation, no ML dependencies
**Cons**: Requires API keys, no offline embeddings

### For Full Local Capabilities
```bash
# Method 1: Conda (Recommended)
conda create -n personal-ai python=3.11
conda activate personal-ai
conda install pytorch torchvision torchaudio -c pytorch
pip install -r requirements.txt
pip install -e .

# Method 2: pip with PyTorch first
pip install torch torchvision torchaudio
pip install -r requirements.txt
pip install -e .
```

**Pros**: Full offline capabilities, local embeddings
**Cons**: Large download, longer installation

### For Development
```bash
# Install in development mode with all dependencies
conda create -n personal-ai-dev python=3.11
conda activate personal-ai-dev
conda install pytorch torchvision torchaudio -c pytorch
pip install -r requirements.txt
pip install -e .
pip install pytest black flake8  # Development tools
```

## Verification

After installation, verify everything works:

```bash
# Test core functionality
python test_core.py

# Test CLI tools
pai-assistant status
pai-ingest status
```

## Environment-Specific Solutions

### GitHub Codespaces / Gitpod
```bash
# Use minimal requirements in cloud environments
pip install -r requirements-minimal.txt
pip install -e .
```

### Docker
```dockerfile
# Use Python 3.11 base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-minimal.txt .
RUN pip install -r requirements-minimal.txt

# Copy and install application
COPY . /app
WORKDIR /app
RUN pip install -e .
```

### Windows
```bash
# Use conda on Windows for better compatibility
conda create -n personal-ai python=3.11
conda activate personal-ai
conda install pytorch torchvision torchaudio cpuonly -c pytorch
pip install -r requirements.txt
pip install -e .
```

## Getting Help

If you continue to have issues:

1. **Check Python version**: `python --version` (should be 3.11 or 3.12)
2. **Update pip**: `pip install --upgrade pip`
3. **Clear pip cache**: `pip cache purge`
4. **Try minimal install**: Use `requirements-minimal.txt`
5. **Use conda**: Often resolves dependency conflicts better than pip

## Common Error Messages and Solutions

| Error | Solution |
|-------|----------|
| `No module named 'torch'` | Install PyTorch first: `pip install torch` |
| `NumPy 1.x cannot be run in NumPy 2.x` | Downgrade NumPy: `pip install "numpy<2.0.0"` |
| `Microsoft Visual C++ 14.0 is required` (Windows) | Install Visual Studio Build Tools |
| `Failed building wheel for chromadb` | Install build tools: `pip install wheel setuptools` |
| `No module named 'sentence_transformers'` | Use minimal requirements or install PyTorch first |
| `ImportError: cannot import name 'packaging'` | `pip install packaging` |

## Performance Notes

- **Minimal install**: ~500MB, fast startup
- **Full install**: ~3-5GB, includes local ML models
- **First run**: Local models download automatically (~1-2GB)
- **Subsequent runs**: Fast startup with cached models