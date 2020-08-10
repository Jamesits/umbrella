from . import DirProvider
import requests
import logging
import re

logger: logging.Logger = logging.getLogger(__name__)

class GitHubDirProvider(DirProvider):
    def search(self):
        ret = []
        per_page = 100

        api_endpoint = 'https://api.github.com'
        if 'api_endpoint' in self.config:
            api_endpoint = self.config['api_endpoint']
        
        if 'searches' in self.config:
            for s in self.config['searches']:
                url = f"{api_endpoint}/{s}"
                # GitHub api doesn't support `//`` in URL, we need to fix that
                url = re.subn('/+', '/', url)[0].replace(":/", "://")
                headers = {
                    'user-agent': 'umbrella/0 (+https://github.com/Jamesits/umbrella)',
                    'Accept': 'application/vnd.github.v3+json',
                }

                # search for the auth strategy
                auth = None
                auth_strategy = self.auth_rule_matcher.match(f"{api_endpoint}/{s}")
                if auth_strategy['type'] == "username_password":
                    from requests.auth import HTTPBasicAuth
                    auth = HTTPBasicAuth(auth_strategy['username'], auth_strategy['password'])
                elif auth_strategy['type'] == 'null':
                    auth = None
                else:
                    logger.error(f"Unknown auth type {auth_strategy['type']}")

                current_page = 1
                while True:
                    logger.debug(f"{url} loading page {current_page}")
                    r = requests.get(
                        url,
                        params={
                            "sort": "full_name",
                            "direction": "asc",
                            "per_page": per_page,
                            "page": current_page,
                        },
                        headers=headers,
                        auth=auth,
                    )

                    if r.status_code != 200:
                        logger.error(f"{r.url} returned {r.status_code}: {r.text}")
                    
                    for repo in r.json():
                        if "clone_url" in repo:
                            ret.append(repo["clone_url"])
                        if "has_wiki" in repo and repo['has_wiki'] == True:
                            ret.append(repo['html_url'] + '.wiki.git')

                    if len(r.json()) < per_page:
                        break
                    else:
                        current_page += 1

        return ret