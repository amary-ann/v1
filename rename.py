import os

# Path to the directory containing the files
folder_path = "C:/Users/user/OneDrive/Documents/Sound Recordings"

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    if "PVCSample" in filename:
        new_filename = filename.replace("PVCSample", "0000000")
        old_file = os.path.join(folder_path, filename)
        new_file = os.path.join(folder_path, new_filename)
        os.rename(old_file, new_file)
        print(f"Renamed: {filename} -> {new_filename}")
