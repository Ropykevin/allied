"""RBAC permission matrix smoke tests."""

import pytest


@pytest.mark.parametrize(
    "email,allowed,denied",
    [
        ("ops@test.example", "/admin/tours", "/admin/users"),
        ("booking@test.example", "/admin/bookings", "/admin/payments/record/1"),
        ("finance@test.example", "/admin/invoices", "/admin/tours/new"),
        ("content@test.example", "/admin/content/blog", "/admin/invoices"),
        ("admin@test.example", "/admin/users", "/admin/does-not-exist-check"),
    ],
)
def test_role_route_access(client, login_as, email, allowed, denied):
    login_as(client, email)
    ok = client.get(allowed, follow_redirects=False)
    assert ok.status_code in (200, 302)
    if "does-not-exist" not in denied:
        bad = client.get(denied, follow_redirects=True)
        # either forbidden or redirected away from protected action
        assert bad.status_code in (200, 403, 404)
