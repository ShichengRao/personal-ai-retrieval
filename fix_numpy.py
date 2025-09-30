#!/usr/bin/env python3
"""
Quick fix script for NumPy 2.x compatibility issues.
Run this if you encounter NumPy compatibility errors.
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and print the output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def main():
    print("🔧 Fixing NumPy 2.x compatibility issues...")
    print("=" * 50)
    
    # Step 1: Downgrade NumPy
    print("\n1. Downgrading NumPy to 1.x...")
    if not run_command('pip install "numpy<2.0.0"'):
        print("❌ Failed to downgrade NumPy")
        return 1
    
    # Step 2: Reinstall PyTorch
    print("\n2. Reinstalling PyTorch...")
    if not run_command('pip install --force-reinstall torch torchvision torchaudio'):
        print("❌ Failed to reinstall PyTorch")
        return 1
    
    # Step 3: Reinstall sentence-transformers
    print("\n3. Reinstalling sentence-transformers...")
    if not run_command('pip install --force-reinstall sentence-transformers'):
        print("❌ Failed to reinstall sentence-transformers")
        return 1
    
    # Step 4: Test the fix
    print("\n4. Testing the fix...")
    try:
        import numpy
        import torch
        import sentence_transformers
        print(f"✅ NumPy version: {numpy.__version__}")
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ Sentence-transformers version: {sentence_transformers.__version__}")
        
        # Test basic functionality
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer import successful")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    print("\n🎉 NumPy compatibility fix completed successfully!")
    print("\nYou can now run:")
    print("  python test_core.py")
    print("  pai-assistant status")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())