import json
import requests
from requests.auth import HTTPBasicAuth
import sys
import uritemplate


def make_session(user: str, token: str):
    s = requests.Session()
    s.config = {'verbose': sys.stderr}
    s.auth = HTTPBasicAuth(user, token)
    return Github(s)

DEPLOYMENTS_URI = "https://api.github.com/repos/{owner}/{repo}/deployments{/id}"
DEPLOYMENT_STATUS_URI = DEPLOYMENTS_URI + "/statuses"

class Github:
    """
    Abstraction for the Github API.
    """
    def __init__(self, session: requests.Session):
        self._session = session
        pass

    def deployment(self, owner='FAForever', repo=None, id=None):
        """

        :param owner:
        :param repo:
        :param id:
        :return:
        """
        return self._session.get(uritemplate.expand(DEPLOYMENTS_URI,
                                 owner=owner,
                                 repo=repo,
                                 id=str(id)))

    def deployments(self, owner='FAForever', repo=None):
        """
        :param owner:
        :param repo:
        :return:
        """
        return self._session.get(
            uritemplate.expand(DEPLOYMENTS_URI,
                               owner=owner,
                               repo=repo))

    def create_deployment(self, owner='FAForever', repo=None, ref='', environment='', description=''):
        """

        :param owner:
        :param repo:
        :param ref:
        :param environment:
        :param description:
        :return:
        """
        repo_url = uritemplate.expand(DEPLOYMENTS_URI,
                                      owner=owner,
                                      repo=repo)
        return self._session.post(repo_url,
                                  data=json.dumps({
                                      "ref": ref,
                                      "environment": environment,
                                      "description": description
                                  }))

    def create_deployment_status(self, owner='FAForever', repo=None, id=None, state=None, target_url=None, description=None):
        """
        :param owner:
        :param repo:
        :param id:
        :param state:
        :param target_url:
        :param description:
        :return:
        """
        repo_url = uritemplate.expand(DEPLOYMENT_STATUS_URI, owner=owner, repo=repo, id=id)
        return self._session.post(repo_url,
                                  data=json.dumps({
                                      "state": state,
                                      "target_url": target_url,
                                      "description": description
                                  }))