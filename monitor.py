import shutil

def get_free_space_c_drive():
    try:
        # On Windows, 'C:/' is the typical path for the C drive
        # On Linux/macOS, you might check '/' or a specific mount point
        # This script assumes a Windows-like environment for 'C:'
        # For cross-platform, a more robust check might be needed or accept a path as arg.
        total, used, free = shutil.disk_usage('C:/')
        free_gb = free / (1024**3)
        print(f"Free space on C drive: {free_gb:.2f} GB")
        return free_gb
    except Exception as e:
        print(f"Error checking C drive space: {e}")
        return None

if __name__ == "__main__":
    get_free_space_c_drive()