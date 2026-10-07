"""
Indian income tax helpers: old vs new regime slabs, PF/ESIC/PT/HRA/gratuity-style computations.

Used by agents and payroll logic; returns structured numbers for display, not legal advice.
"""
import math


def tax_calculator(
    annual_gross_income: float,
    basic_annual: float = 0,
    hra_annual: float = 0,
    rent_paid_annual: float = 0,
    city_tier: str = "metro",
    regime: str = "both",
    section_80c: float = 0,
    section_80d: float = 0,
    hra_received_annual: float = 0,
) -> dict:
    results = {}

    if regime in ("new", "both"):
        results["new_regime"] = _calculate_new_regime(annual_gross_income)

    if regime in ("old", "both"):
        results["old_regime"] = _calculate_old_regime(
            annual_gross_income, basic_annual, hra_annual,
            rent_paid_annual, city_tier, section_80c, section_80d
        )

    if regime == "both" and "new_regime" in results and "old_regime" in results:
        new_tax = results["new_regime"]["total_tax_with_cess"]
        old_tax = results["old_regime"]["total_tax_with_cess"]
        if new_tax <= old_tax:
            results["recommendation"] = "New Regime"
            results["savings"] = round(old_tax - new_tax, 2)
        else:
            results["recommendation"] = "Old Regime"
            results["savings"] = round(new_tax - old_tax, 2)
        results["recommendation_reason"] = (
            f"The {results['recommendation']} saves you ₹{results['savings']:,.0f} annually."
        )

    return {"success": True, "tax_calculation": results}


def _calculate_new_regime(annual_gross: float) -> dict:
    standard_deduction = 75000
    taxable_income = max(0, annual_gross - standard_deduction)

    if taxable_income <= 1200000:
        tax_before_cess = 0
        rebate_applied = True
    else:
        tax_before_cess = _compute_slab_tax_new(taxable_income)
        rebate_applied = False

    cess = round(tax_before_cess * 0.04, 2)
    total_tax = round(tax_before_cess + cess, 2)
    monthly_tds = round(total_tax / 12, 2)

    return {
        "regime": "New Regime (FY 2025-26)",
        "gross_income": annual_gross,
        "standard_deduction": standard_deduction,
        "taxable_income": taxable_income,
        "rebate_87a_applied": rebate_applied,
        "tax_before_cess": tax_before_cess,
        "health_education_cess_4pct": cess,
        "total_tax_with_cess": total_tax,
        "monthly_tds": monthly_tds,
        "slabs": [
            {"range": "0 - 4,00,000", "rate": "0%"},
            {"range": "4,00,001 - 8,00,000", "rate": "5%"},
            {"range": "8,00,001 - 12,00,000", "rate": "10%"},
            {"range": "12,00,001 - 16,00,000", "rate": "15%"},
            {"range": "16,00,001 - 20,00,000", "rate": "20%"},
            {"range": "20,00,001 - 24,00,000", "rate": "25%"},
            {"range": "Above 24,00,000", "rate": "30%"},
        ]
    }


def _compute_slab_tax_new(taxable: float) -> float:
    tax = 0.0
    slabs = [
        (400000, 0.00),
        (400000, 0.05),
        (400000, 0.10),
        (400000, 0.15),
        (400000, 0.20),
        (400000, 0.25),
        (math.inf, 0.30),
    ]
    remaining = taxable
    for slab_amount, rate in slabs:
        if remaining <= 0:
            break
        amount_in_slab = min(remaining, slab_amount)
        tax += amount_in_slab * rate
        remaining -= amount_in_slab
    return round(tax, 2)


def _calculate_old_regime(
    annual_gross: float,
    basic_annual: float,
    hra_annual: float,
    rent_paid_annual: float,
    city_tier: str,
    section_80c: float,
    section_80d: float,
) -> dict:
    standard_deduction = 50000
    hra_exemption = 0

    if basic_annual > 0 and rent_paid_annual > 0:
        metro_pct = 0.50 if city_tier == "metro" else 0.40
        hra_exemption = min(
            hra_annual,
            metro_pct * basic_annual,
            max(0, rent_paid_annual - 0.10 * basic_annual)
        )
        hra_exemption = round(hra_exemption, 2)

    sec_80c = min(section_80c, 150000)
    sec_80d = min(section_80d, 50000)

    total_deductions = standard_deduction + hra_exemption + sec_80c + sec_80d
    taxable_income = max(0, annual_gross - total_deductions)

    if taxable_income <= 500000:
        tax_before_cess = 0
        rebate_applied = True
    else:
        tax_before_cess = _compute_slab_tax_old(taxable_income)
        rebate_applied = False

    cess = round(tax_before_cess * 0.04, 2)
    total_tax = round(tax_before_cess + cess, 2)
    monthly_tds = round(total_tax / 12, 2)

    return {
        "regime": "Old Regime (FY 2025-26)",
        "gross_income": annual_gross,
        "standard_deduction": standard_deduction,
        "hra_exemption": hra_exemption,
        "section_80c_deduction": sec_80c,
        "section_80d_deduction": sec_80d,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "rebate_87a_applied": rebate_applied,
        "tax_before_cess": tax_before_cess,
        "health_education_cess_4pct": cess,
        "total_tax_with_cess": total_tax,
        "monthly_tds": monthly_tds,
        "slabs": [
            {"range": "0 - 2,50,000", "rate": "0%"},
            {"range": "2,50,001 - 5,00,000", "rate": "5%"},
            {"range": "5,00,001 - 10,00,000", "rate": "20%"},
            {"range": "Above 10,00,000", "rate": "30%"},
        ]
    }


def _compute_slab_tax_old(taxable: float) -> float:
    tax = 0.0
    slabs = [
        (250000, 0.00),
        (250000, 0.05),
        (500000, 0.20),
        (math.inf, 0.30),
    ]
    remaining = taxable
    for slab_amount, rate in slabs:
        if remaining <= 0:
            break
        amount_in_slab = min(remaining, slab_amount)
        tax += amount_in_slab * rate
        remaining -= amount_in_slab
    return round(tax, 2)


def compute_pf(basic_monthly: float) -> dict:
    pf_wage = min(basic_monthly, 15000)
    employee_pf = round(pf_wage * 0.12, 2)
    employer_pf = round(pf_wage * 0.12, 2)
    employer_eps = round(min(pf_wage, 15000) * 0.0833, 2)
    employer_epf = round(employer_pf - employer_eps, 2)
    return {
        "pf_wage": pf_wage,
        "employee_contribution": employee_pf,
        "employer_contribution": employer_pf,
        "employer_eps": employer_eps,
        "employer_epf": employer_epf,
    }


def compute_esic(gross_monthly: float) -> dict:
    if gross_monthly > 21000:
        return {"applicable": False, "employee_contribution": 0, "employer_contribution": 0}
    employee_esic = round(gross_monthly * 0.0075, 2)
    employer_esic = round(gross_monthly * 0.0325, 2)
    return {
        "applicable": True,
        "employee_contribution": employee_esic,
        "employer_contribution": employer_esic,
    }


def compute_professional_tax(state: str = "maharashtra", gross_monthly: float = 0) -> float:
    pt_map = {
        "maharashtra": 200 if gross_monthly > 10000 else 0,
        "karnataka": 200 if gross_monthly > 15000 else 0,
        "west bengal": 200 if gross_monthly > 10000 else 0,
        "tamil nadu": 0,
        "telangana": 200 if gross_monthly > 15000 else 0,
        "delhi": 0,
        "gujarat": 200 if gross_monthly > 12000 else 0,
    }
    return pt_map.get(state.lower(), 200)


def compute_hra_exemption(
    basic_monthly: float,
    hra_received_monthly: float,
    rent_paid_monthly: float,
    city_tier: str = "metro"
) -> dict:
    if rent_paid_monthly <= 0:
        return {"exemption": 0, "taxable_hra": hra_received_monthly, "reason": "No rent paid"}

    metro_pct = 0.50 if city_tier == "metro" else 0.40
    option_a = hra_received_monthly
    option_b = metro_pct * basic_monthly
    option_c = max(0, rent_paid_monthly - 0.10 * basic_monthly)

    exemption = round(min(option_a, option_b, option_c), 2)
    taxable_hra = round(hra_received_monthly - exemption, 2)

    return {
        "actual_hra_received": hra_received_monthly,
        "50pct_or_40pct_of_basic": round(option_b, 2),
        "rent_minus_10pct_basic": round(option_c, 2),
        "exemption": exemption,
        "taxable_hra": taxable_hra,
        "rule_applied": f"Minimum of the three: ₹{exemption:,.0f}"
    }


def compute_gratuity(basic_monthly: float, years_of_service: float) -> dict:
    if years_of_service < 5:
        return {
            "eligible": False,
            "amount": 0,
            "reason": "Minimum 5 years of continuous service required."
        }
    gratuity = round((basic_monthly * 15 * years_of_service) / 26, 2)
    max_gratuity = 2000000
    final = min(gratuity, max_gratuity)
    return {
        "eligible": True,
        "calculated_amount": gratuity,
        "statutory_cap": max_gratuity,
        "payable_amount": final,
        "formula": "(Basic × 15 × Years of Service) / 26",
    }
