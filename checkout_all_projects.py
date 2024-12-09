#!/usr/bin/env python3

import os
import subprocess
import shutil
from pathlib import Path
import logging

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def collect_bug(project, bug_id, base_dir):
    """Collect both buggy and fixed versions of a bug"""
    bug_dir = Path(base_dir) / project / str(bug_id)
    buggy_dir = bug_dir / "buggy"
    fixed_dir = bug_dir / "fixed"
    
    # Create directories
    buggy_dir.mkdir(parents=True, exist_ok=True)
    fixed_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = "/tmp/bugsinpy_temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    try:
        # Get buggy version (v=0)
        cmd = f"bugsinpy-checkout -p {project} -i {bug_id} -v 0 -w {temp_dir}"
        logging.info(f"Running: {cmd}")
        subprocess.run(cmd.split(), check=True)
        
        # Copy files from temp to buggy dir
        if os.path.exists(temp_dir):
            for item in os.listdir(os.path.join(temp_dir, project)):
                src = os.path.join(temp_dir, project, item)
                dst = buggy_dir / item
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        
        # Clean temp
        shutil.rmtree(temp_dir)
        
        # Get fixed version (v=1)
        cmd = f"bugsinpy-checkout -p {project} -i {bug_id} -v 1 -w {temp_dir}"
        logging.info(f"Running: {cmd}")
        subprocess.run(cmd.split(), check=True)
        
        # Copy files from temp to fixed dir
        if os.path.exists(temp_dir):
            for item in os.listdir(os.path.join(temp_dir, project)):
                src = os.path.join(temp_dir, project, item)
                dst = fixed_dir / item
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
                    
        # Get bug info
        cmd = f"bugsinpy-info -p {project} -i {bug_id}"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        with open(bug_dir / "bug_description.txt", "w") as f:
            f.write(result.stdout)
            
        # Copy additional files
        src_bug_dir = f"projects/{project}/bugs/{bug_id}"
        for file in ["requirements.txt", "setup.sh", "run_test.sh"]:
            src = os.path.join(src_bug_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, bug_dir / file)
                
    except Exception as e:
        logging.error(f"Error processing {project} bug {bug_id}: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def main():
    base_dir = "complete_projects"
    projects_dir = "projects"
    
    for project in os.listdir(projects_dir):
        project_bugs_dir = os.path.join(projects_dir, project, "bugs")
        if os.path.isdir(project_bugs_dir):
            for bug_id in os.listdir(project_bugs_dir):
                if os.path.isdir(os.path.join(project_bugs_dir, bug_id)):
                    logging.info(f"Processing {project} bug {bug_id}")
                    collect_bug(project, bug_id, base_dir)

if __name__ == "__main__":
    main()
    