from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class Profile:
    filing_status: str
    primary_dob: str
    spouse_dob: Optional[str]
    state: str
    county: Optional[str]


@dataclass
class Inputs:
    start_year: int
    end_year: int
    balances: Dict[str, float]
    returns: Dict[str, float]
    withdrawals_mode: str
    withdrawals_plan: List[Dict]
    fixed_withdrawal: float
    include_roth_in_fixed: bool
    conversions: Dict
    social_security: Dict


@dataclass
class Assumptions:
    rules_version: str
