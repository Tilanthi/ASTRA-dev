"""reference_sheet.py — pinned physical constants for LLM-facing prompts.

IOAA (arXiv 2510.05016) gave every model the same reference sheet humans get,
eliminating constant drift as a failure mode. ASTRA's proposer authors code
that sometimes needs a constant (unit conversions, luminosity scaling); these
literals are pinned here so no authored code ever relies on model memory.

Values: CODATA 2018 / IAU 2015 nominal solar values / IAU 2012 au.
"""
REFERENCE_SHEET = """Pinned constants (use these literals; do not re-derive):
c = 2.99792458e8 m/s
G = 6.67430e-11 m3 kg-1 s-2
h = 6.62607015e-34 J s
k_B = 1.380649e-23 J/K
sigma_SB = 5.670374419e-8 W m-2 K-4
m_e = 9.1093837015e-31 kg
m_p = 1.67262192369e-27 kg
e = 1.602176634e-19 C
AU = 1.495978707e11 m
pc = 3.0856775814913673e16 m
M_sun = 1.98892e30 kg
R_sun = 6.957e8 m
L_sun = 3.828e26 W
T_sun = 5772 K
"""
