import tarfile
import docker
import os
import shutil
import zipfile

runs_dir = '/usr/app/runs'
assignment_dir = '/usr/app/assignments'
client = docker.from_env()

def get_run_dir_for_uuid(uuid: str) -> str:
    return os.path.join(runs_dir, uuid)

def run_container(container_name: str, file, filename, uuid: str):
    run_dir = get_run_dir_for_uuid(uuid)
    setup_directory(container_name, file, filename, run_dir)

    # Create docker image
    image = client.images.build(path=run_dir, tag=container_name, rm=True)[0]

    # Execute docker container
    logs = "No output"
    res = ""
    try:
        # Run container in detached mode
        container = client.containers.run(image=image, detach=True)

        # Stream logs to catch output and errors
        streamed_logs = container.logs(stream=True)
        logs = ""
        for log in streamed_logs:
            logs+=log.decode("utf-8")
        logs = logs[0:-1]

        # Download final results to local tar file
        bits, _ = container.get_archive("/usr/app/results.json")
        tar_file = open(os.path.join(run_dir,"results.tar"), "wb")
        for chunk in bits:
            tar_file.write(chunk)
        tar_file.close()  # timeout, kubernetes, docker on separate server

        # Unpack tar file and capture results
        tar_file = open(os.path.join(run_dir,"results.tar"), "rb")
        tar = tarfile.open(fileobj=tar_file)
        files = tar.getmembers()
        res = tar.extractfile(files[0]).read().decode("utf-8")

        container.remove()
    except docker.errors.ContainerError:
        print("There was a container error")

    clean_directory(run_dir)
    return (logs, res)

def saveFile(file, filename, run_dir, unzip=True):
    save_path = os.path.join(run_dir, filename)
    file.save(save_path)
    # Extract zip file contents
    if filename.endswith(".zip") and unzip:
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
# todo: get rid of hard coded Dockerfile.zip

def clean_directory(run_dir):
    shutil.rmtree(run_dir)