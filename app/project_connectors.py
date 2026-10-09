"""Read-only project connector utilities."""

from app.wbs_reconcile import reconcile_wbs


def reconcile_external_work(jira, plane, ganttax=None, github_links=None):
    return reconcile_wbs(jira, plane, ganttax or [], github_links or [])
