import json, pathlib
from .base import StateTaxCalculator

DATA = json.loads((pathlib.Path(__file__).parents[2]/"data/states/md_rates_2025.json").read_text())

class MarylandGeneric(StateTaxCalculator):
    code = "MD"
    def compute(self, *, year:int, ages:tuple[int,int], agi:float,
                taxable_fed:float, county:str|None, filing_status:str) -> dict:
        num65 = sum(1 for a in ages if a and a>=65)
        state_eff = DATA.get("state_effective_rate", 0.0475)
        local_eff = DATA.get("counties", {}).get(county or "", {}).get("local_effective_rate", 0.0281)
        ded = (DATA.get("senior_deduction_per65",6000)+DATA.get("senior_extra_per65",1200))*num65
        md_taxable = max(0.0, agi - ded)
        gross = md_taxable*(state_eff+local_eff)
        credit = 0.0
        cap = DATA.get("senior_credit", {}).get("agi_cap", 150000)
        if agi <= cap:
            credit = DATA["senior_credit"].get("both65",1750) if num65>=2 else (DATA["senior_credit"].get("one65",1000) if num65==1 else 0)
        return {"tax": max(0.0, gross-credit), "details": {"county": county, "ded": ded}}