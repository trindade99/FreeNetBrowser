from .main import main
import sys
import os

def redirect_output():
    """Redirect stdout and stderr to files for packaged app"""
    if getattr(sys, 'frozen', False):  # Only in packaged app
        log_dir = os.path.join(get_app_data_dir(), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # Redirect stdout and stderr
        sys.stdout = open(os.path.join(log_dir, 'stdout.log'), 'w', encoding='utf-8')
        sys.stderr = open(os.path.join(log_dir, 'stderr.log'), 'w', encoding='utf-8')

# Call this before any other imports or code

if __name__ == "__main__":
    redirect_output()
    main()
