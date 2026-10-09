from app.mcp_governance import CATALOG,authorize_tool

def test_unknown_tool_denied():
    assert authorize_tool("unknown.tool",["ADMIN"],True)["allowed"] is False

def test_write_requires_approval():
    assert authorize_tool("github.pr.merge",["PL"])["allowed"] is False
    assert authorize_tool("github.pr.merge",["PL"],True)["allowed"] is True

def test_sme_approval_is_separate():
    assert authorize_tool("pmo.baseline.approve",["PM"],True)["allowed"] is False
    assert authorize_tool("pmo.baseline.approve",["SME"],True)["allowed"] is True

def test_read_only_permissions():
    assert authorize_tool("github.issues.read",["AUDITOR"])["allowed"] is True
    assert authorize_tool("github.issues.read",["GUEST"])["allowed"] is False

def test_catalog_operations_explicit():
    assert all(p.operation in {"read","write","approve","deploy"} for p in CATALOG.values())
