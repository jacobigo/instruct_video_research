import os
import shutil
from datetime import datetime


def cleanup_pipeline_folders(folders_to_remove):
    """
    Remove specified folders and their contents.
    
    Args:
        folders_to_remove (list): List of folder paths to remove
    """
    print(f"Cleanup started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    removed_folders = []
    skipped_folders = []
    
    for folder in folders_to_remove:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                removed_folders.append(folder)
                print(f"✓ Removed folder: {folder}")
            except Exception as e:
                print(f"✗ Failed to remove {folder}: {str(e)}")
        else:
            skipped_folders.append(folder)
            print(f"- Folder doesn't exist: {folder}")
    
    print(f"\nCleanup summary:")
    print(f"Removed: {len(removed_folders)} folders")
    print(f"Skipped: {len(skipped_folders)} folders")
    
    return removed_folders, skipped_folders


def interactive_cleanup():
    """
    Interactive cleanup with user confirmation for each folder.
    """
    # Default folders from pipeline
    DEFAULT_FOLDERS = [
        'slide_images',
        'audio_files', 
        'audio_image_clips'
        #'final_video'
    ]
    
    print("Pipeline Cleanup Tool")
    print("=" * 30)
    print("\nFolders that will be removed:")
    
    for i, folder in enumerate(DEFAULT_FOLDERS, 1):
        exists = "✓" if os.path.exists(folder) else "✗"
        print(f"{i}. {folder} {exists}")
    
    print(f"\n✓ = exists, ✗ = doesn't exist")
    
    choice = input("\nDo you want to remove all existing folders? (y/N): ").lower().strip()
    
    if choice in ['y', 'yes']:
        cleanup_pipeline_folders(DEFAULT_FOLDERS)
    else:
        print("Cleanup cancelled.")


def cleanup_all_logs():
    """
    Remove all pipeline timing log files.
    """
    log_files = [f for f in os.listdir('.') if f.startswith('pipeline_timing_') and f.endswith('.json')]
    
    if not log_files:
        print("No pipeline log files found.")
        return
    
    print(f"Found {len(log_files)} log files:")
    for log_file in log_files:
        print(f"  - {log_file}")
    
    choice = input(f"\nRemove all {len(log_files)} log files? (y/N): ").lower().strip()
    
    if choice in ['y', 'yes']:
        removed = 0
        for log_file in log_files:
            try:
                os.remove(log_file)
                print(f"✓ Removed: {log_file}")
                removed += 1
            except Exception as e:
                print(f"✗ Failed to remove {log_file}: {str(e)}")
        print(f"\nRemoved {removed} log files.")
    else:
        print("Log cleanup cancelled.")


if __name__ == '__main__':
    print("Choose cleanup option:")
    print("1. Clean pipeline folders (except final video)")
    print("2. Clean log files") 
    print("3. Clean everything (1 and 2)")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        interactive_cleanup()
    elif choice == '2':
        cleanup_all_logs()
    elif choice == '3':
        interactive_cleanup()
        print("\n" + "="*30)
        cleanup_all_logs()
    elif choice == '4':
        print("Exiting.")
    else:
        print("Invalid choice. Exiting.")