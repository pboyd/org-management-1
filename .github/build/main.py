import yaml
import os
import requests

def main():
    with open("./config/opendatahub-io/org.yaml", "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        new_odh_org = data.get("orgs").get("opendatahub-io")
    os.system("git fetch --all")
    os.system("git checkout main")

    with open("./config/opendatahub-io/org.yaml", "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        old_odh_org = data.get("orgs").get("opendatahub-io")

    pr_number = os.environ.get("PR_NUMBER")
    affected_teams = get_affected_groups(old_odh_org, new_odh_org)
    approver_teams = get_valid_approvers(old_odh_org, affected_teams)
    pr_approvers = get_pr_approvers(pr_number, os.environ.get("TOKEN"))
    for team in approver_teams:
        if team[1].intersection(pr_approvers):
            print(f"Valid reviewer found for {team[0]} in PR approvers: {pr_approvers}")
        else:
            print(f"No valid reviewers found for {team[0]} in PR approvers: {pr_approvers}")
            exit(1)


def get_affected_groups(old_org, new_org):
    affected_groups = {"teams": [], "org_changed": False}
    if old_org==new_org:
        print("No changes detected to org yaml")
        exit(0)
    old_org_teams = old_org.get("teams")
    new_org_teams = new_org.get("teams")
    for team in old_org_teams:
        if old_org_teams.get(team) != new_org_teams.get(team):
            print(f"{team} has been changed")
            affected_groups["teams"].append(team)
    for key, value in old_org.items():
        if key != "teams":
            if value != new_org.get(key):
                affected_groups["org_changed"] = True
                break
    return affected_groups


def get_valid_approvers(org: dict, groups: dict):
    approvers = []
    for team in groups["teams"]:
        approvers.append((team, set(org.get("teams").get(team).get("maintainers"))))
    if groups["org_changed"]:
        approvers.append((org.get("name"), set(org.get("admins"))))
    return approvers


def get_pr_approvers(id: int, token: str):
    response = requests.get(
        "https://api.github.com/repos/" + os.environ.get("REPO") + "/pulls/" + id + "/reviews",
        headers={
        "Authorization": "Bearer " + token
        }
    )

    # Check the response status code
    if response.status_code == 200:
        # Get the list of review comments from the response
        reviews = response.json()

        # Create a list of users who have approved the PR
        approved_users = set()
        for review in reviews:
            if review['state'] == "CHANGES_REQUESTED":
                print(f"{review['user']['login']} has requested changes.")
                exit(1)
            if review['state'] == "APPROVED":
                approved_users.add(review['user']['login'])

        return approved_users
    else:
        print(f"Received an invalid response code: {response.status_code}")
        exit(1)


if __name__ == "__main__":
    main()