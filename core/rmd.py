# Simple SECURE 2.0 mapping (starter):
# Born 1951–1959 → 73; Born >= 1960 → 75; <=1950 → 72 (legacy)

def rmd_start_age_from_dob(dob: str) -> int:
    y = int(dob.split("-")[0])
    if y >= 1960:
        return 75
    if 1951 <= y <= 1959:
        return 73
    return 72

UNIFORM_DIVISORS = {
    73:26.5,74:25.5,75:24.7,76:23.8,77:22.9,78:22.0,79:21.2,80:20.3,
    81:19.5,82:18.7,83:17.9,84:17.1,85:16.3,86:15.6,87:14.8,88:14.1,
    89:13.4,90:12.7,91:12.0,92:11.4,93:10.8,94:10.1,95:9.5,96:8.9,
    97:8.4,98:7.8,99:7.3,100:6.8
}

def rmd_uniform(age:int, balance:float) -> float:
    if balance <= 0:
        return 0.0
    d = UNIFORM_DIVISORS.get(int(age))
    if d is None:
        return 0.0
    return balance/d