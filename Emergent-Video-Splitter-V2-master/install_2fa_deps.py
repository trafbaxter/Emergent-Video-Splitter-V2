#!/usr/bin/env python3
"""
Install 2FA dependencies for Lambda deployment
"""

import subprocess
import sys
import os
import tempfile
import shutil

def install_2fa_libraries():
    """Install pyotp and qrcode libraries"""
    
    print("🔐 Installing 2FA Dependencies for Lambda")
    print("=" * 50)
    
    # Create temporary directory for packages
    temp_dir = tempfile.mkdtemp()
    packages_dir = os.path.join(temp_dir, 'python')
    os.makedirs(packages_dir)
    
    print(f"📦 Installing packages to: {packages_dir}")
    
    try:
        # Install pyotp
        print("\n🔑 Installing pyotp...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            'pyotp==2.8.0',  # Specific version for compatibility
            '--target', packages_dir,
            '--no-deps'  # Don't install dependencies to keep it lightweight
        ], check=True)
        
        # Install qrcode with minimal dependencies
        print("\n📱 Installing qrcode...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            'qrcode==7.4.2',  # Specific version
            '--target', packages_dir,
            '--no-deps'
        ], check=True)
        
        # Install Pillow (required for qrcode)
        print("\n🖼️ Installing Pillow...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            'Pillow==10.0.0',  # Compatible version
            '--target', packages_dir,
            '--no-deps'
        ], check=True)
        
        # Copy packages to local directory
        local_deps_dir = '/app/python_2fa_deps'
        if os.path.exists(local_deps_dir):
            shutil.rmtree(local_deps_dir)
        
        shutil.copytree(packages_dir, local_deps_dir)
        print(f"\n✅ Packages copied to: {local_deps_dir}")
        
        # List installed packages
        print(f"\n📋 Installed packages:")
        for item in os.listdir(local_deps_dir):
            if os.path.isdir(os.path.join(local_deps_dir, item)):
                print(f"   📁 {item}")
            else:
                print(f"   📄 {item}")
        
        print(f"\n🎉 2FA dependencies installed successfully!")
        print(f"Directory size: {get_dir_size(local_deps_dir):.1f} MB")
        
        return local_deps_dir
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return None
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir)

def get_dir_size(path):
    """Get directory size in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size / (1024 * 1024)

def test_imports():
    """Test if the installed libraries work"""
    
    print("\n🧪 Testing 2FA library imports...")
    
    try:
        # Add the local deps to Python path
        import sys
        sys.path.insert(0, '/app/python_2fa_deps')
        
        # Test pyotp
        import pyotp
        print("✅ pyotp imported successfully")
        
        # Test generating a secret
        secret = pyotp.random_base32()
        print(f"✅ TOTP secret generated: {secret[:8]}...")
        
        # Test TOTP
        totp = pyotp.TOTP(secret)
        code = totp.now()
        print(f"✅ TOTP code generated: {code}")
        
        # Test qrcode
        import qrcode
        print("✅ qrcode imported successfully")
        
        # Test QR code generation
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data('test')
        qr.make(fit=True)
        print("✅ QR code generation test passed")
        
        # Test PIL (Pillow)
        from PIL import Image
        print("✅ Pillow (PIL) imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    # Install dependencies
    deps_dir = install_2fa_libraries()
    
    if deps_dir:
        # Test the installation
        if test_imports():
            print(f"\n🎯 All tests passed! 2FA libraries are ready for Lambda deployment.")
            print(f"\nNext steps:")
            print(f"1. Update Lambda deployment to include: {deps_dir}")
            print(f"2. Deploy the updated Lambda function")
            print(f"3. Test 2FA endpoints")
        else:
            print(f"\n❌ Tests failed. Please check the installation.")
    else:
        print(f"\n❌ Installation failed.")