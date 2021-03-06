import docker
import os
import pytest
import requests
import time

import cerise_client.service as cs

@pytest.fixture()
def docker_client(request):
    return docker.from_env()

@pytest.fixture(scope="module")
def test_image(request):
    """Get a plain cerise image for testing.

    Ignores errors; we may have a local image available already,
    in which case we want to continue, otherwise the other
    tests will fail.
    """
    docker_client = docker.from_env()
    try:
        docker_client.images.pull('mdstudio/cerise:develop')
    except docker.errors.APIError:
        pass
    return 'mdstudio/cerise:develop'

@pytest.fixture()
def test_service(request, test_image):
    from .clean_up import clean_up_service
    clean_up_service('cerise_client_test_service')
    srv = cs.create_managed_service('cerise_client_test_service', 29593,
            test_image)

    yield srv

    clean_up_service('cerise_client_test_service')

@pytest.fixture()
def this_dir(request):
    return os.path.dirname(__file__)

def create_test_job(test_service, this_dir, name):
    job = test_service.create_job(name)
    r = requests.get('http://localhost:29593/files/input/' + name + '/')
    assert r.status_code == 200

    # run job to create some outputs
    job.set_workflow(os.path.join(this_dir, 'test_workflow2.cwl'))
    job.add_input_file('input_file', os.path.join(this_dir, 'test_workflow2.cwl'))
    job.run()
    while job.is_running():
        time.sleep(0.1)
    assert job.state == 'Success'

    counts = job.outputs['counts']
    assert counts.text != ''
    return job

