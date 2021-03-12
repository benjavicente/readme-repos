"README repository badges"

import os

import requests
import jinja2


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

REPO_PAYLOAD = R"""
{
  viewer {
    repositories(first: 12, orderBy: {field: STARGAZERS, direction: DESC}, privacy: PUBLIC) {
      edges {
        node {
          name
          forkCount
          description
          isArchived
          url
          updatedAt
          stargazerCount
          languages(first: 1, orderBy: {field: SIZE, direction: DESC}) {
            edges {
              node {
                name
                color
              }
            }
          }
        }
      }
    }
  }
}
"""


def get_repos() -> list[dict]:
    "Gets a list of repos from the `REPO_PAYLOAD` GQL query"

    if "GITHUB_TOKEN" not in os.environ:
        raise ValueError("GITHUB_TOKEN is not set in the environment")

    token = os.environ["GITHUB_TOKEN"]

    if "GITHUB_GRAPHQL_URL" in os.environ:
        url = os.environ["GITHUB_GRAPHQL_URL"]
    else:
        url = GITHUB_GRAPHQL_URL

    response = response = requests.post(
        url, json={"query": REPO_PAYLOAD}, headers={"Authorization": f"bearer {token}"}
    )

    if not response.ok:
        raise requests.RequestException("Request failed")

    repos = response.json()["data"]["viewer"]["repositories"]["edges"]
    repos = list(map(lambda r: r["node"], repos))
    for repo in repos:
        repo["languages"] = list(map(lambda r: r["node"], repo["languages"]["edges"]))

    return repos


def make_cards(
    readme_template=os.path.join("templates", "readme.md.j2"),
    card_template=os.path.join("templates", "card.svg.j2"),
    out_dir="out",
    out_readme="readme.md"
) -> None:
    """
    Makes the cards, using `readme_template` for the README.md template,
    `card_template` for the card svg template, and `out_dir` as the
    output directory.
    """
    repos = get_repos()
    relative_path = os.path.relpath(out_dir, os.path.dirname(out_readme))

    with open(card_template, mode="r", encoding="utf-8") as template_file:
        card = jinja2.Template(template_file.read())

    with open(readme_template, mode="r", encoding="utf-8") as out_format_file:
        readme = jinja2.Template(out_format_file.read())

    for repo in repos:
        file_name = f"{repo['name']}.svg"
        with open(os.path.join(out_dir, file_name), mode="w", encoding="utf-8") as repo_file:
            repo_file.write(card.render(repo))
        repo["card_path"] = os.path.join(relative_path, file_name)


    with open(out_readme, mode="w", encoding="utf-8") as out_file:
        out_file.write(readme.render(repos=repos, relative_path=relative_path))


if __name__ == "__main__":
    make_cards()
