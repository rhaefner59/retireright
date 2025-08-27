class StateTaxCalculator:
    code = "BASE"
    def compute(self, *, year:int, ages:tuple[int,int], agi:float,
                taxable_fed:float, county:str|None, filing_status:str) -> dict:
        return {"tax": 0.0, "details": {}}