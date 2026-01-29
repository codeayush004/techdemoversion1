import os
import shutil
import tempfile
import subprocess


def create_workspace(container_id: str):
    workspace = tempfile.mkdtemp(prefix="optimizer_")
    rootfs = os.path.join(workspace, "rootfs")

    os.makedirs(rootfs, exist_ok=True)

    subprocess.run(
        ["docker", "export", container_id, "-o", os.path.join(workspace, "fs.tar")],
        check=True
    )

    subprocess.run(
        ["tar", "-xf", os.path.join(workspace, "fs.tar"), "-C", rootfs],
        check=True
    )

    return workspace, rootfs


def cleanup_workspace(workspace: str):
    shutil.rmtree(workspace, ignore_errors=True)
