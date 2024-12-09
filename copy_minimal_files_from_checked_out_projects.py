import os
import shutil

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

def copy_project_files(project_minimal_path, project_base_minimal_path):
    for project in os.listdir(project_minimal_path):
        project_path = os.path.join(project_minimal_path, project)
        
        if not os.path.isdir(project_path):
            continue
            
        for bug_id in os.listdir(project_path):
            bug_path = os.path.join(project_path, bug_id)
            
            if not os.path.isdir(bug_path):
                continue
                
            fixed_path = os.path.join(bug_path, 'fixed')
            buggy_path = os.path.join(bug_path, 'buggy')
            
            # Create corresponding paths in project_base_minimal
            base_project_path = os.path.join(project_base_minimal_path, project, bug_id)
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
                'bugsinpy_requirements.txt'
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

if __name__ == "__main__":
    project_minimal_path = "project_minimal"
    project_base_minimal_path = "project_base_minimal"
    copy_project_files(project_minimal_path, project_base_minimal_path)