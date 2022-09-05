import docker
import os
import shutil

client = docker.from_env()
docker_dir = '/Users/rickywoodruff/Desktop/UT Austin/Fall 2022 (Senior)/CS370/codeAssist/CodeAssist/backend/dockerfiles'
runs_dir = '/Users/rickywoodruff/Desktop/UT Austin/Fall 2022 (Senior)/CS370/codeAssist/CodeAssist/backend/runs'

def run_container(container: str, file, filename, uuid):
    run_dir = os.path.join(runs_dir, uuid)
    setup_directory(container, file, filename, run_dir)
    image = client.images.build(path=run_dir, tag=container)
    res = client.containers.run(image=image[0])
    clean_directory(run_dir)
    return res

def setup_directory(container, file, filename, run_dir):
    os.mkdir(run_dir)
    file.save(os.path.join(run_dir, filename))
    shutil.copy(os.path.join(docker_dir, container, "Dockerfile"), run_dir)

def clean_directory(run_dir):
    shutil.rmtree(run_dir)