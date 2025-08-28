#!/usr/bin/env python3
"""
Test that the Streamlit app can start without errors
"""

import subprocess
import sys
import time
import os
import signal

def test_app_startup():
    """Test that the app starts successfully"""
    print("🚀 Testing Streamlit app startup...")
    
    # Set a dummy API key for testing
    env = os.environ.copy()
    env['OPENAI_API_KEY'] = 'test-key-for-startup-test'
    
    try:
        # Start the Streamlit app in the background
        process = subprocess.Popen(
            ['uv', 'run', 'streamlit', 'run', 'chatbot_app.py', '--server.headless', 'true', '--server.port', '8502'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        # Wait for the app to start
        print("⏳ Waiting for app to start...")
        time.sleep(8)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ App started successfully!")
            
            # Try to get some output
            try:
                stdout, stderr = process.communicate(timeout=2)
                if "You can now view your Streamlit app" in stdout or "Local URL" in stdout:
                    print("✅ Streamlit server is running")
                else:
                    print("ℹ️  App started but checking logs...")
                    if stderr:
                        print(f"   Stderr: {stderr[:200]}...")
                    if stdout:
                        print(f"   Stdout: {stdout[:200]}...")
            except subprocess.TimeoutExpired:
                print("✅ App is running (timeout on communicate is normal)")
            
            # Clean up
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ App failed to start")
            print(f"   Return code: {process.returncode}")
            if stderr:
                print(f"   Error: {stderr}")
            if stdout:
                print(f"   Output: {stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        try:
            process.terminate()
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_app_startup()
    print(f"\n{'🎉 Startup test passed!' if success else '❌ Startup test failed!'}")
    if not success:
        sys.exit(1)