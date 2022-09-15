import docker
import os
import shutil
import zipfile

runs_dir = '/usr/app/runs'
assignment_dir = '/usr/app/assignments'
client = docker.from_env()

def run_container(container: str, file, filename, uuid):
    run_dir = os.path.join(runs_dir, uuid)
    setup_directory(container, file, filename, run_dir)

    # Create docker image
    image = client.images.build(path=run_dir, tag=container, rm=True)[0]

    # Execute docker container
    res = "No output"
    try:
        # Run container in detached mode and stream logs
        logs = client.containers.run(image=image, auto_remove=True, detach=True).logs(stream=True)
        res = ""
        for log in logs:
            res+=log.decode("utf-8")
        res = res[0:-1]
    except docker.errors.ContainerError:
        print("There was a container error")

    clean_directory(run_dir)
    return res

def saveFile(file, filename, run_dir):
    save_path = os.path.join(run_dir, filename)
    file.save(save_path)
    # Extract zip file contents
    if filename.endswith(".zip"):
        copyAndDecompressZip(save_path, run_dir)
        # Remove zip file
        os.remove(save_path)


def copyAndDecompressZip(src, dest):
    assert src.endswith(".zip")

    with zipfile.ZipFile(src, 'r') as zip_ref:
        zip_ref.extractall(dest)

def setup_directory(container, file, filename, run_dir):
    if not os.path.exists(runs_dir):
        os.mkdir(runs_dir)
        
    os.mkdir(run_dir)
    saveFile(file, filename, run_dir)

    # Copy over autograder zip
    copyAndDecompressZip(os.path.join(assignment_dir, container, "Dockerfile.zip"), run_dir)


def clean_directory(run_dir):
    shutil.rmtree(run_dir)