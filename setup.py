from cx_Freeze import setup, Executable

# Specify the files or folders to include
include_files = [
    ("Fonts", "Fonts"),  # Include the Fonts folder (source, destination)
]

# Build options for cx_Freeze
build_exe_options = {
    "packages": ["pyglet", "soundcard", "soundfile", "numpy"],  # Add necessary packages
    "include_files": include_files,  # Add data files
}

# Define the executable
executables = [
    Executable("app.py", base="Win32GUI", target_name="LoopBack.exe"),
]

# Setup configuration
setup(
    name="LoopBack",
    version="1.0",
    description="LoopBack Audio Recorder",
    options={"build_exe": build_exe_options},
    executables=executables,
)
