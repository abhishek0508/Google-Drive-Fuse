FUSE Based Google Drive File System
-----------------------------------

FUSE
-----
Filesystem in Userspace (FUSE) is a software interface for Unix and Unix-like computer
operating systems that lets non-privileged users create their own file systems without editing kernel code. This is achieved
by running file system code in user space while the FUSE module provides only a "bridge" to the actual kernel interfaces.

About Project
--------------
Basically its filesystem, which is intended to provide access via familiar posix calls to files which are actually
stored behind a resftul api(like Google Drive API).The filesystem caches files once they've been retrieved for the first time
so that they are more readily available next time.

## 🛠 Installation & Set Up

1. Install FusePy

   ```sh
   pip install fusepy
   ```

2. Install dependencies


3. Go to [Link](https://developers.google.com/drive/api/v3/quickstart/python) and enable drive API and store ```credentials.json``` in current directory

4. Run
    ```sh
   python3 gfs.py path_to_folder_to_mount
   ```



