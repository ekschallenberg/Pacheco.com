import pytest

from jobwatcher.role import in_role


@pytest.mark.parametrize("title", [
    "Financial Analyst", "Senior Financial Analyst, Revenue", "FP&A Manager", "Data Analyst",
    "Credit Risk Analyst", "Treasury Analyst", "Business Intelligence Analyst", "Strategy & Operations Analyst",
    "Senior Manager, Financial Planning",
])
def test_titles_in_role(title):
    assert in_role(title)


@pytest.mark.parametrize("title", [
    "Software Engineer", "Data Scientist", "Account Executive", "Marketing Analyst",
    "Data Engineer", "Financial Systems Engineer", "Analyst Relations Lead", "", "Recruiter, Finance",
])
def test_titles_not_in_role(title):
    assert not in_role(title)
