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

def read_patchfile_info(file_path):
    """Read the files that need to be copied from patchfile.info"""
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        content = f.read().strip()
        return [path.strip() for path in content.split(';') if path.strip()]

def copy_file_content(src_file, dst_file):
    """Copy content from source file to destination file"""
    if os.path.exists(src_file):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        try:
            # Try reading as text with UTF-8 encoding
            with open(src_file, 'r', encoding='utf-8') as src:
                content = src.read()
                with open(dst_file, 'w', encoding='utf-8') as dst:
                    dst.write(content)
        except UnicodeDecodeError:
            # If UTF-8 fails, copy as binary file
            with open(src_file, 'rb') as src:
                with open(dst_file, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        print(f"Copied content from {os.path.basename(src_file)} to {dst_file}")

def copy_minimal_files(project, bug_id, source_dir, dest_dir):
    try:
        bug_path = os.path.join(source_dir, project, bug_id)
        
        fixed_path = os.path.join(bug_path, 'fixed')
        buggy_path = os.path.join(bug_path, 'buggy')
        
        if not (os.path.isdir(fixed_path) and os.path.isdir(buggy_path)):
            logging.error(f"Required directories not found for {project} bug {bug_id}")
            return
        
        # Create corresponding paths in project_base_minimal
        base_project_path = os.path.join(dest_dir, project, bug_id)
        base_fixed_path = os.path.join(base_project_path, 'fixed')
        base_buggy_path = os.path.join(base_project_path, 'buggy')
        
        # Ensure directories exist
        os.makedirs(base_project_path, exist_ok=True)
        os.makedirs(base_fixed_path, exist_ok=True)
        os.makedirs(base_buggy_path, exist_ok=True)
        
        # 1. Copy files that should go in the bug_id folder
        bug_level_files = [
            'bug_description.txt',
            'requirements.txt',
            'setup.sh',
            'run_test.sh'
        ]
        
        for file_name in bug_level_files:
            # Check if file exists in bug_id folder
            bug_level_file = os.path.join(bug_path, file_name)
            base_file = os.path.join(base_project_path, file_name)
            
            if os.path.exists(bug_level_file):
                copy_file_content(bug_level_file, base_file)
        
        # 2. Copy info files from fixed to fixed and buggy to buggy
        info_files = [
            'bugsinpy_patchfile.info',
            'bugsinpy_bug.info',
            'bugsinpy_requirements.txt',
            'README.srt',
            'README.md',
            'README'
        ]
        
        for file_name in info_files:
            # Copy from fixed to fixed
            fixed_file = os.path.join(fixed_path, file_name)
            base_fixed_file = os.path.join(base_fixed_path, file_name)
            if os.path.exists(fixed_file):
                copy_file_content(fixed_file, base_fixed_file)
            
            # Copy from buggy to buggy
            buggy_file = os.path.join(buggy_path, file_name)
            base_buggy_file = os.path.join(base_buggy_path, file_name)
            if os.path.exists(buggy_file):
                copy_file_content(buggy_file, base_buggy_file)
        
        # 3. Read and copy files mentioned in patchfile.info
        patchfile_info_path = os.path.join(fixed_path, 'bugsinpy_patchfile.info')
        source_files = read_patchfile_info(patchfile_info_path)
        
        for source_file in source_files:
            # Copy from fixed to fixed
            fixed_source = os.path.join(fixed_path, source_file)
            base_fixed_source = os.path.join(base_fixed_path, source_file)
            if os.path.exists(fixed_source):
                copy_file_content(fixed_source, base_fixed_source)
            
            # Copy from buggy to buggy
            buggy_source = os.path.join(buggy_path, source_file)
            base_buggy_source = os.path.join(base_buggy_path, source_file)
            if os.path.exists(buggy_source):
                copy_file_content(buggy_source, base_buggy_source)
        
        # 4. Read and copy test files mentioned in bugsinpy_bug.info
        bug_info_path = os.path.join(fixed_path, 'bugsinpy_bug.info')
        if os.path.exists(bug_info_path):
            with open(bug_info_path, 'r') as f:
                for line in f:
                    if 'test_file=' in line:
                        test_file = line.split('=')[1].strip().strip('"')
                        
                        # Copy from fixed to fixed
                        fixed_test = os.path.join(fixed_path, test_file)
                        base_fixed_test = os.path.join(base_fixed_path, test_file)
                        if os.path.exists(fixed_test):
                            copy_file_content(fixed_test, base_fixed_test)
                        
                        # Copy from buggy to buggy
                        buggy_test = os.path.join(buggy_path, test_file)
                        base_buggy_test = os.path.join(base_buggy_path, test_file)
                        if os.path.exists(buggy_test):
                            copy_file_content(buggy_test, base_buggy_test)
    except Exception as e:
        logging.error(f"Error copying minimal files for {project} bug {bug_id}: {str(e)}")


def remove_bug(project, bug_id, base_dir):
    """Remove a bug directory from the specified base directory"""
    bug_dir = Path(base_dir) / project / str(bug_id)
    try:
        if bug_dir.exists():
            shutil.rmtree(bug_dir)
            logging.info(f"Successfully removed {project} bug {bug_id}")
        else:
            logging.warning(f"Directory not found for {project} bug {bug_id}")
    except Exception as e:
        logging.error(f"Error removing {project} bug {bug_id}: {str(e)}")


def main():
    base_dir = "project_minimal"
    dest_dir = "project_minimal_copy"
    projects_dir = "projects"
    
    
    for project in os.listdir(projects_dir):
        project_bugs_dir = os.path.join(projects_dir, project, "bugs")
        if os.path.isdir(project_bugs_dir):
            for bug_id in os.listdir(project_bugs_dir):
                if os.path.isdir(os.path.join(project_bugs_dir, bug_id)):
                    logging.info(f"Processing {project} bug {bug_id}")
                    collect_bug(project, bug_id, base_dir)
                    copy_minimal_files(project, bug_id, base_dir, dest_dir)
                    remove_bug(project, bug_id, base_dir)

if __name__ == "__main__":
    main()
    