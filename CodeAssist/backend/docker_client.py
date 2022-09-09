import docker
import os
import shutil

docker_dir = '/Users/rickywoodruff/Desktop/UT Austin/Fall 2022 (Senior)/CS370/codeAssist/CodeAssist/backend/dockerfiles'
runs_dir = '/Users/rickywoodruff/Desktop/UT Austin/Fall 2022 (Senior)/CS370/codeAssist/CodeAssist/backend/runs'
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

def setup_directory(container, file, filename, run_dir):
    if not os.path.exists(runs_dir):
        os.mkdir(runs_dir)
        
    os.mkdir(run_dir)
    file.save(os.path.join(run_dir, filename))
    shutil.copy(os.path.join(docker_dir, container, "Dockerfile"), run_dir)

def clean_directory(run_dir):
    shutil.rmtree(run_dir)