from pydantic import BaseModel
from typing import List, Dict


class Vulnerability(BaseModel):
    id: str
    pkg: str
    severity: str
    installed_version: str
    fixed_version: str | None
    title: str | None


class SecretFinding(BaseModel):
    rule: str
    category: str
    severity: str
    target: str


class SecurityReport(BaseModel):
    vulnerabilities: List[Vulnerability]
    secrets: List[SecretFinding]
    summary: Dict[str, int]
    vulnerability_count: int
    secret_count: int
