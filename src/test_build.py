# src/test_build.py
import subprocess

def test_update():
    subprocess.check_call(["python", "update_data.py"])
    
def test_visualization():
    subprocess.check_call(["python", "visual_tierlist.py"])