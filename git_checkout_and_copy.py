import os
import shutil
import subprocess
import re

def extract_file_paths_from_patch(patch_file):
    file_paths = []
    with open(patch_file, 'r') as f:
        for line in f:
            if line.startswith('diff --git'):
                # Extract the b/ path (fixed version path)
                match = re.search(r'b/(.*?)\s*$', line)
                if match:
                    file_paths.append(match.group(1))
    return file_paths

def copy_required_files(src_dir, dest_dir, files_to_copy):
    for file in files_to_copy:
        src_file = os.path.join(src_dir, file)
        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_dir)

def clean_and_checkout(repo_dir, commit_id):
    # Reset any changes but keep untracked files for now
    subprocess.run(['git', 'reset', '--hard'], cwd=repo_dir)
    # Checkout the specific commit
    subprocess.run(['git', 'checkout', commit_id], cwd=repo_dir)
    # Now clean untracked files
    subprocess.run(['git', 'clean', '-fd'], cwd=repo_dir)
    # Checkout again to ensure we have the correct files
    subprocess.run(['git', 'checkout', commit_id], cwd=repo_dir)

def process_project(project_dir):
    # Get project name and bug id from directory structure
    project_name = os.path.basename(project_dir)
    bugs_dir = os.path.join(project_dir, 'bugs')
    
    for bug_id in os.listdir(bugs_dir):
        bug_dir = os.path.join(bugs_dir, bug_id)
        if not os.path.isdir(bug_dir):
            continue

        # Read bug info
        bug_info_file = os.path.join(bug_dir, 'bug.info')
        bug_info = {}
        with open(bug_info_file, 'r') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                bug_info[key.strip()] = value.strip().strip('"')

        # Create project_base_minimal structure
        base_dir = 'project_base_minimal'
        project_bug_dir = os.path.join(base_dir, project_name, bug_id)
        buggy_dir = os.path.join(project_bug_dir, 'buggy')
        fixed_dir = os.path.join(project_bug_dir, 'fixed')
        os.makedirs(buggy_dir, exist_ok=True)
        os.makedirs(fixed_dir, exist_ok=True)

        # Checkout only once using bugsinpy-checkout
        subprocess.run(['bugsinpy-checkout', '-p', project_name, '-i', bug_id, '-v', 'buggy'])
        
        # Get modified file paths from patch
        patch_file = os.path.join(bug_dir, 'bug_patch.txt')
        modified_files = extract_file_paths_from_patch(patch_file)

        # Get the repository directory
        repo_dir = os.path.join('/home/ubuntu/hexo/new/BugsInPy/framework/bin/temp', project_name)

        # First handle buggy version
        clean_and_checkout(repo_dir, bug_info['buggy_commit_id'])
        
        # Copy modified files and test files for buggy version
        test_files = bug_info['test_file'].split(';')
        all_files_to_copy = modified_files + test_files

        for file_path in all_files_to_copy:
            file_path = file_path.strip()
            src_file = os.path.join(repo_dir, file_path)
            if os.path.exists(src_file):
                dest_path = os.path.join(buggy_dir, file_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_file, dest_path)

        # Copy required files for buggy version from bug directory
        required_files = [
            'bugsinpy_patchfile.info',
            'bugsinpy_bug.info',
            'bugsinpy_requirements.txt',
            'README.rst',
            'README.md',
            'README'
        ]
        
        # First try to copy from the original bug directory
        for file in required_files:
            # Try to copy from the bug directory first
            src_file = os.path.join(bug_dir, file)  # bug_dir is the original bug directory
            if os.path.exists(src_file):
                print(f"Copying {file} from bug directory to buggy")
                shutil.copy2(src_file, buggy_dir)
            else:
                # If not in bug directory, try from repo directory
                src_file = os.path.join(repo_dir, file)
                if os.path.exists(src_file):
                    print(f"Copying {file} from repo directory to buggy")
                    shutil.copy2(src_file, buggy_dir)

        # Then handle fixed version
        clean_and_checkout(repo_dir, bug_info['fixed_commit_id'])
        
        # Copy modified files and test files for fixed version
        for file_path in all_files_to_copy:
            file_path = file_path.strip()
            src_file = os.path.join(repo_dir, file_path)
            if os.path.exists(src_file):
                dest_path = os.path.join(fixed_dir, file_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_file, dest_path)

        # Copy required files for fixed version
        for file in required_files:
            # Try to copy from the bug directory first
            src_file = os.path.join(bug_dir, file)
            if os.path.exists(src_file):
                print(f"Copying {file} from bug directory to fixed")
                shutil.copy2(src_file, fixed_dir)
            else:
                # If not in bug directory, try from repo directory
                src_file = os.path.join(repo_dir, file)
                if os.path.exists(src_file):
                    print(f"Copying {file} from repo directory to fixed")
                    shutil.copy2(src_file, fixed_dir)

        # Generate bug description using bugsinpy-info
        bug_desc_file = os.path.join(project_bug_dir, 'bug_description')
        subprocess.run(['bugsinpy-info', '-p', project_name, '-i', bug_id], 
                      stdout=open(bug_desc_file, 'w'))

        # Create requirements.txt in project bug directory
        project_requirements = os.path.join(project_bug_dir, 'requirements.txt')
        with open(project_requirements, 'w') as f:
            f.write('pytest\n')  # Add basic requirement

        # Create run_test.sh
        with open(os.path.join(project_bug_dir, 'run_test.sh'), 'w') as f:
            f.write('#!/bin/bash\n')
            # Write all test files to run
            for test_file in test_files:
                f.write(f'python -m pytest {test_file.strip()}\n')
        os.chmod(os.path.join(project_bug_dir, 'run_test.sh'), 0o755)

def main():
    projects_dir = 'projects'
    # for project in os.listdir(projects_dir):
    #     if project == 'pandas':
    #         continue
    #     project_dir = os.path.join(projects_dir, project)
    #     if os.path.isdir(project_dir):
    process_project(os.path.join(projects_dir, 'fastapi'))

if __name__ == '__main__':
    main()