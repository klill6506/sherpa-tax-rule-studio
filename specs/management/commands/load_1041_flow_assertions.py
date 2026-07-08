"""Form 1041 (estates & trusts) — flow assertions (S-11 leg 8a, Ken-approved
2026-07-08 via the tax-app REVIEW_QUEUE authoring plan).

The S-11 RS authoring (load_1041_spine / load_1041_schedule_k1, 2026-07-05)
shipped rules/diagnostics/tests but NO FlowAssertions — found when the tts leg-8
gate build hit an empty `/api/flow-assertions/export/?entity_type=1041`. These
16 assertions are transcribed from the APPROVED spec's own rules (R-1041-* /
R-K1041-*) — no new tax law; each `definition.formula` quotes the seeded rule
formula (source citations live on the rules themselves).

Consumed by the tts flow-assertion gate (tests/test_flow_assertions.py): each
assertion gets a registered pure runner exercising the BUILT engine
(apps.returns.compute_1041 / k1_allocator_1041 / compute_ga501 — all pure).

RECONCILIATION with the 2026-07-05 staged drafts (found mid-authoring): the S-11
loaders had ALREADY staged 10 draft FAs (load_1041_spine: DNI/IDD/TIERS/EXEMPT/
TAX/NIIT · load_1041_schedule_k1: CHAR/RECON/FINYR/NIIT) — never activated, which
is why the export served zero. This loader is now the SINGLE FA home for the
1041 family (the FA blocks were removed from the two spec loaders so a reseed
cannot regress statuses):
  - Ids shared with the drafts (DNI/IDD/TIERS/EXEMPT/CHAR) are re-authored here
    and FORCED ACTIVE (the load_sch_1a "force-active what it owns" precedent).
  - FA-K1041-FINYR adopted (engine-backed: allocate_k1_boxes is_final_year
    gating) and activated.
  - FA-1041-TAX superseded by the finer FA-1041-RATES + FA-1041-CGRATE pair;
    FA-K1041-RECON superseded by FA-K1041-SUM → both DISABLED (the
    "disable superseded ids on renames" rule).
  - FA-1041-NIIT and FA-K1041-NIIT stay STAGED (draft) here: the trust-side
    8960 computation and the 1041-K-1 box-14H → beneficiary-8960-L7 import are
    not built — activating them would fail the gate on unbuilt behavior.

Deliberately NOT asserted (structural/conditional spec rules with no compute):
  - R-1041-SEPSHARE (§663(c) separate-share) — engine allocates by dni_pct only;
    the D_1041_* diagnostic carries the boundary. Add an FA when per-share DNI
    is built.
  - R-1041-65DAY (§663(b)) — an input-semantics rule (B10 includes 65-day
    amounts); nothing to pin beyond the IDD chain already covered.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from specs.models import FlowAssertion


FLOW_ASSERTIONS: list[dict] = [
    # ── Page-1 chains ──
    {"assertion_id": "FA-1041-TOTINC", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "Page-1 L9 total income = L1 + L2a + L3..L8 (2b is a subset, never added)",
     "description": "R-1041-TOTINC. Bug it catches: qualified dividends (2b) double-counted into total income, or an income line dropped from the combine.",
     "definition": {"kind": "formula_check", "form": "1041",
                    "formula": "L9 = interest + ordinary_dividends + business + capital_gain + rents_passthrough + farm + 4797_gain + other"},
     "sort_order": 1},
    {"assertion_id": "FA-1041-ATI", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "L16 = add L10-15b ; L17 adjusted total income = L9 - L16",
     "description": "R-1041-TOTDED / R-1041-ATI. Bug it catches: a deduction line dropped from L16, or L17 not netting. L17 is the GA Form 501 base.",
     "definition": {"kind": "formula_check", "form": "1041",
                    "formula": "L16 = L10+L11+L12+L13+L14+L15a+L15b ; L17 = L9 - L16"},
     "sort_order": 2},
    # ── Schedule B — the Subchapter J core ──
    {"assertion_id": "FA-1041-DNI", "assertion_type": "reconciliation", "entity_types": ["1041"],
     "title": "DNI (Sch B L7): §643(a) modifications incl. the corpus-gain back-out",
     "description": "R-1041-DNI. Bug it catches: page-1 L4 corpus capital gains left inside DNI (B6 back-out dropped), adjusted tax-exempt interest (B2) unfloored, or DNI not floored at 0.",
     "definition": {"kind": "reconciliation", "form": "1041",
                    "formula": "B1=L17 ; B2=max(0, TE_INT-TE_EXP) ; B6=-L4 ; B7=max(0, B1+B2+B3+B4-B5+B6)"},
     "sort_order": 3},
    {"assertion_id": "FA-1041-IDD", "assertion_type": "reconciliation", "entity_types": ["1041"],
     "title": "IDD (Sch B L15) = smaller of L13 or L14 -> page-1 L18 (DNI cap)",
     "description": "R-1041-IDD. THE Subchapter J limitation: distributions deduct only up to taxable DNI. Bug it catches: the smaller-of inverted, tax-exempt not backed out of either side, or L15 not landing on page-1 L18.",
     "definition": {"kind": "reconciliation", "form": "1041",
                    "formula": "B11=B9+B10 ; B13=B11-B12 ; B14=max(0, B7-B2) ; B15=min(B13,B14) ; L18=B15"},
     "sort_order": 4},
    {"assertion_id": "FA-1041-TIERS", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "§662 two-tier allocation: DNI to tier 1 first, tier 2 gets the excess",
     "description": "R-1041-TIERS. Bug it catches: second-tier distributions carrying out DNI already absorbed by first-tier income.",
     "definition": {"kind": "formula_check", "form": "1041",
                    "formula": "tier1 = min(B9, taxable_dni) ; tier2 = min(B10, max(0, taxable_dni - B9)) with taxable_dni = B14"},
     "sort_order": 5},
    # ── Exemption / taxable income / tax ──
    {"assertion_id": "FA-1041-EXEMPT", "assertion_type": "table_invariant", "entity_types": ["1041"],
     "title": "§642(b) exemption table: estate 600 / simple 300 / complex 100 / QDisT 5,100 / ESBT 0",
     "description": "R-1041-EXEMPT (QDisT per Rev. Proc. 2024-40 §2.35). Bug it catches: an entity type mapped to the wrong exemption, or the ESBT S-portion granted one.",
     "definition": {"kind": "table_invariant", "form": "1041",
                    "params": {"estate": 600, "simple_trust": 300, "complex_trust": 100, "qdist": 5100, "esbt": 0}},
     "sort_order": 6},
    {"assertion_id": "FA-1041-TAXINC", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "L22 = L18 + L19 + L20 + L21 ; L23 taxable income = max(0, L17 - L22)",
     "description": "R-1041-TAXINC. Bug it catches: the QBI deduction (L20) or exemption dropped from the block, or L23 going negative.",
     "definition": {"kind": "formula_check", "form": "1041",
                    "formula": "L22 = L18 + estate_tax_ded + qbi_ded + L21 ; L23 = max(0, L17 - L22)"},
     "sort_order": 7},
    {"assertion_id": "FA-1041-RATES", "assertion_type": "table_invariant", "entity_types": ["1041"],
     "title": "§1(e) 2025 compressed rate schedule pins (RP 2024-40 Table 5)",
     "description": "R-1041-TAX, ordinary path. Bug it catches: a bracket base/floor drift. Pins: 10% to 3,150 (base 315); 24% to 11,450 (base 2,307); 35% to 15,650 (base 3,777); 37% above. Known-value pin: TI 19,400 -> 5,165 (half-up from 5,164.50).",
     "definition": {"kind": "table_invariant", "form": "1041",
                    "params": {"brackets": [[3150, "0.10"], [11450, "0.24"], [15650, "0.35"], [None, "0.37"]],
                               "bases": [0, 315, 2307, 3777], "pin": {"ti": 19400, "tax": 5165}}},
     "sort_order": 8},
    {"assertion_id": "FA-1041-CGRATE", "assertion_type": "table_invariant", "entity_types": ["1041"],
     "title": "Estate/trust 0/15/20 capital-gain stacking (breaks 3,250 / 15,900) capped at all-ordinary",
     "description": "R-1041-TAX, preferential path. Bug it catches: preferential income stacked UNDER ordinary, wrong 2025 breakpoints, or the worksheet exceeding the all-ordinary tax.",
     "definition": {"kind": "table_invariant", "form": "1041",
                    "params": {"cg0": 3250, "cg15": 15900, "cap": "min(total, rate_schedule(TI))"}},
     "sort_order": 9},
    # ── Schedule G / total tax / settle ──
    {"assertion_id": "FA-1041-TOTTAX", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "Sch G chain: L1e = L1a+L1b+L1c ; L3 = max(0, L1e - credits) ; L9 = L3+L4+L5+L6+L7+L8 -> page-1 L24",
     "description": "R-1041-TOTTAX. Bug it catches: credits under-flooring L3, ESBT/NIIT/other taxes dropped from L9, or L24 not mirroring G9.",
     "definition": {"kind": "formula_check", "form": "1041",
                    "formula": "G1e=G1a+G1b+G1c ; G3=max(0,G1e-(G2a+G2b+G2c+G2d)) ; G9=G3+G4+G5+G6+G7+G8 ; L24=G9"},
     "sort_order": 10},
    {"assertion_id": "FA-1041-ESBT", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "ESBT S-portion: Sch G L4 = 37% x ESBT taxable income; exemption 0",
     "description": "R-1041-ESBT / R-1041-EXEMPT. Bug it catches: the S-portion taxed at graduated rates instead of the top rate, L4 emitted for a non-ESBT, or the ESBT granted a §642(b) exemption.",
     "definition": {"kind": "formula_check", "form": "1041",
                    "formula": "if entity_type==esbt: G4 = round(0.37 x ESBT_TI) and L21 = 0 ; else G4 = 0"},
     "sort_order": 11},
    {"assertion_id": "FA-1041-SETTLE", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "Payments block: L26 = 25a+25e ; L28 due / L29-L30 overpayment split on (L24+L27) vs L26",
     "description": "Page-1 face arithmetic (beyond the spec line_map — the seed_1041 payments precedent). Bug it catches: the penalty (L27) left out of the liability side, or due/overpay both emitted.",
     "definition": {"kind": "formula_check", "form": "1041",
                    "formula": "L26=25a+25e ; liab=L24+L27 ; L28=max(0,liab-L26) ; L29=L30=max(0,L26-liab) ; L28 xor L29"},
     "sort_order": 12},
    # ── Schedule K-1 (1041) issuer side ──
    {"assertion_id": "FA-K1041-CHAR", "assertion_type": "reconciliation", "entity_types": ["1041"],
     "title": "K-1 character retention: box[c] = entity class x DNI% ; no losses in boxes 1-8",
     "description": "R-K1041-CHAR / R-K1041-NOLOSS (Reg. §§1.652(c)-4, 1.662(c)-4). Bug it catches: classes blended before allocation (character lost), or a negative class reaching boxes 1-8.",
     "definition": {"kind": "reconciliation", "form": "SCHEDULE_K1_1041",
                    "formula": "box[c] = round(ent[c] x dni_pct/100), floored at 0 for boxes 1-8"},
     "sort_order": 13},
    {"assertion_id": "FA-K1041-SUM", "assertion_type": "reconciliation", "entity_types": ["1041"],
     "title": "Sum of all beneficiaries' box c == the entity class carried out (within rounding)",
     "description": "R-K1041-RECON. Bug it catches: DNI percentages not exhausting the class, or an allocation double-count. Tolerance: <= 1 dollar per beneficiary (whole-dollar rounding).",
     "definition": {"kind": "reconciliation", "form": "SCHEDULE_K1_1041",
                    "formula": "abs(sum_over_beneficiaries(box[c]) - ent[c]) <= n_beneficiaries"},
     "sort_order": 14},
    # ── Boundary gates + the state base ──
    {"assertion_id": "GATE-1041-DEFERS", "assertion_type": "gating_check", "entity_types": ["1041"],
     "title": "RED-defers hold: Sch I AMT never computed (G1c input-only) ; grantor trust issues no K-1s",
     "description": "D-2 (AMT/bankruptcy RED-defer) + the grantor structure rule. Bug it catches: a silent AMT computation appearing, the D_1041_* defers dropping out of the registry, or a grantor trust suddenly issuing K-1s.",
     "definition": {"kind": "gating_check", "form": "1041",
                    "formula": "G1c is direct-entry ; D_1041 AMT/bankruptcy rules registered ; allocate_all_beneficiary_k1s(grantor) == []"},
     "sort_order": 15},
    {"assertion_id": "FA-1041-GA501", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "GA Form 501 L1 = federal 1041 L17 (ATI) ; L8 = 5.19% of L7c, whole-dollar",
     "description": "R-GA501-BASE / R-GA501-TAX (the fiduciary state base rides the federal ATI, PRE income-distribution deduction; beneficiary share removed at GA L4, never the federal IDD).",
     "definition": {"kind": "flow_assertion", "form": "GA501",
                    "formula": "GA501.L1 = 1041.L17 ; L8 = round(L7c x 0.0519)"},
     "sort_order": 16},
    # ── Adopted from the 2026-07-05 staged drafts (engine-backed → active) ──
    {"assertion_id": "FA-K1041-FINYR", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "title": "Box 11 §642(h) carryovers pass through only in the final year",
     "description": "R-K1041-FINYR (adopted from the 2026-07-05 staged draft). Excess deductions (11A/B) and capital-loss/NOL carryovers (11C/D/E/F) appear on the K-1 only when is_final_year; otherwise box 11 is blank and the attributes stay with the entity.",
     "definition": {"kind": "flow_assertion", "form": "SCHEDULE_K1_1041",
                    "formula": "box11* populated iff is_final_year"},
     "sort_order": 17},
]

# Staged (draft) — spec-true but NOT engine-backed yet; activating them would
# fail the gate on unbuilt behavior. Content preserved from the 2026-07-05
# authoring; they now live HERE (removed from the spec loaders).
STAGED_ASSERTIONS: list[dict] = [
    {"assertion_id": "FA-1041-NIIT", "assertion_type": "reconciliation", "entity_types": ["1041"],
     "status": "draft", "sort_order": 90,
     "title": "§1411 NIIT threshold = top-bracket start ($15,650)",
     "description": "STAGED: Sch G L5 is direct-entry from Form 8960 L21 in the built engine (no trust-side 8960 compute). Activate when the 1041-side 8960 is built. Original: 3.8% x lesser of undistributed NII or (AGI - 15,650).",
     "definition": {"rule": "R-1041-NIIT", "check": "SchG_L5 = 0.038 * min(undistributed_NII, AGI - 15650)"}},
    {"assertion_id": "FA-K1041-NIIT", "assertion_type": "flow_assertion", "entity_types": ["1041"],
     "status": "draft", "sort_order": 91,
     "title": "Distributed NII taxed at the beneficiary (box 14H -> 8960 L7)",
     "description": "STAGED: the 1041-K-1 box-14H -> beneficiary Form 8960 line 7 import flow is not built. Activate with the 1041-K-1 -> 1040 import leg.",
     "definition": {"rule": "R-K1041-BOX14", "check": "box14H -> beneficiary Form 8960 line 7"}},
]

# Superseded by finer-grained replacements — disabled, never deleted (audit).
SUPERSEDED: dict[str, str] = {
    "FA-1041-TAX": "superseded 2026-07-08 by FA-1041-RATES + FA-1041-CGRATE (ordinary schedule and cap-gain stacking split)",
    "FA-K1041-RECON": "superseded 2026-07-08 by FA-K1041-SUM (same reconciliation, runner-shaped definition)",
}


class Command(BaseCommand):
    help = (
        "Seed the sixteen Form 1041 flow assertions (transcribed from the "
        "approved R-1041-*/R-K1041-* rules). FA-only — the 1041 form specs "
        "were seeded by load_1041_spine / load_1041_schedule_k1."
    )

    @transaction.atomic
    def handle(self, *args, **opts):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "Loading Form 1041 flow assertions"))
        for a in FLOW_ASSERTIONS:
            a = dict(a)
            a.setdefault("status", "active")  # force-active what this loader owns
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        for a in STAGED_ASSERTIONS:
            a = dict(a)
            FlowAssertion.objects.update_or_create(
                assertion_id=a.pop("assertion_id"), defaults=a,
            )
        disabled = 0
        for aid, note in SUPERSEDED.items():
            row = FlowAssertion.objects.filter(assertion_id=aid).first()
            if row and row.status != "disabled":
                row.status = "disabled"
                row.description = f"[{note}] " + (row.description or "")
                row.save(update_fields=["status", "description", "updated_at"])
                disabled += 1
        self.stdout.write(
            f"  {len(FLOW_ASSERTIONS)} active + {len(STAGED_ASSERTIONS)} staged; "
            f"{disabled} superseded disabled"
        )
        self.stdout.write(f"FlowAssertions total: {FlowAssertion.objects.count()}")
