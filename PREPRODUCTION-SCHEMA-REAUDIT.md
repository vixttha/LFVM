# Pre-production schema re-audit — 149 fields

Mission LFVM-FOUNDATION-AUDIT-001. Review scope: the entire draft field inventory, exact schema from prior partition repair. No real workbook built. Red, Blue and Purple perspectives applied sequentially by the same assistant; no independent agent or final release audit claimed.

The original 28 architecture findings and seven filled readiness findings are retained. Schema decisions are draft, not owner-locked. This review identifies both implemented controls and remaining semantic/production risks.

| Table | Field count | Exact reviewed field inventory | Result / residual |
|---|---:|---|---|
| 01_MANIFEST | 10 | partition_id, dataset_id, schema_version, data_version, relative_path, table_name, record_count, partition_state, artifact_sha256, previous_partition_id | Local counts and IDs validated; external index pins physical bytes. Prior partition links and supersession require accepted edition history; not yet exercised in a real workbook. |
| 02_DICTIONARY | 8 | field_id, table_name, column_name, data_type, required, description, foreign_key, unit_rule | Exact header/type/required/FK/description comparisons; unit_rule optional, no finalized units-display or Excel formatting acceptance. |
| 03_TAXONOMY | 7 | taxonomy_id, family, code, display_label, definition, deprecated, replacement_id | Legacy labels preserved exactly, unique family/code entries; semantic labels/definitions need owner acceptance; retirement migration remains future. |
| 04_PROVIDERS | 10 | entity_id, entity_kind, parent_id, name, official_url, country, status, first_discovered, last_reviewed, notes | Identity, hierarchy and status typed; country code membership and actual official-source authenticity not proven. |
| 05_OFFERS | 38 | offer_id, service_id, offer_name, legacy_category, free_class, access, environment, availability, execution, funding, eligibility, expiration, expiry_date, duration_count, duration_unit, renewable, permanent_free, custom_code, commercial_use, llm_use, signup_url, terms_url, currency, card_required, deposit_state, setup_fee_state, recurring_fee_state, storage_fee_state, network_fee_state, overage_fee_state, renewal_fee_state, billing_cap, auto_upgrade, zero_cost_verified, verification, last_reviewed, review_due, notes | Funding/eligibility/expiration separate; fee states, cap, and E6 scenario conservative. Numeric fee amounts and reset timezone/credit unit need a later explicit schema decision; no live billing verification. |
| 06_RESOURCES | 16 | resource_id, offer_id, profile_id, resource_kind, profile_name, metric, value_state, value_min, value_max, value_text, unit, period_count, period_unit, guarantee, region_code, notes | Profile isolation, units/ranges/quotas validated. Architecture, GPU specs and time allowances remain facts requiring evidence; token/request quotas and rolling calendar reset details need a later explicit schema decision. |
| 07_COMPATIBILITY | 12 | compatibility_id, offer_id, profile_id, software_name, software_version, status, test_date, test_commit, benchmark_metric, benchmark_value, benchmark_unit, notes | Profile, status, dated execution, metric triad; real benchmark reproducibility and commit verification pending. |
| 08_ASSESSMENTS | 11 | assessment_id, target_table, target_id, dimension, trust_grade, billing_risk, risk, suitability, assessed_on, review_due, rationale | Independent dimensions and dated review; no composite trust score. No actual provider risk audit. |
| 09_EVIDENCE | 16 | evidence_id, claim_id, target_table, target_id, field_name, claimed_value, source_url, publisher, published_on, retrieved_on, effective_on, review_due, grade, outcome, scenario, notes | Claim identity, typed scalar, coverage, freshness, contradiction gates; actual source authenticity and provider execution evidence pending. |
| 10_RELATIONSHIPS | 10 | relationship_id, from_table, from_id, relation, to_table, to_id, field_name, value_state, literal_value, notes | Global references, category/tag/source links and explicit field-state distinction; relationship semantics and source reconciliation for real edition pending. |
| 11_HISTORY | 11 | event_id, target_table, target_id, action, field_name, before_json, after_json, event_on, data_version, reason, evidence_id | Stable target, typed JSON, evidence FK; external accepted history verification and actual successor migration still needed. |

## Newly identified findings and dispositions

| ID | Perspective | Finding | Disposition |
|---|---|---|---|
| PRE-01 | Red | Per-workbook foreign keys reject legitimate cross-workbook references; absent global edition pin | Repaired by external index and combined validation; synthetic cross-workbook tests |
| PRE-02 | Red | Duplicate cell payloads and oversized/nonportable cell values could be accepted | Repaired with strict payload/portable bounds; final workbook compatibility not established |
| PRE-03 | Blue | Contradictory E3 evidence could evade a higher-grade claim check | Repaired by considering current official-grade contradictions independently |
| PRE-04 | Purple | Real authority cannot rely on candidate-supplied key, workflow, or loose commit directory | External policy pin, Git inventory/ancestry and workbook job adapter implemented; real production policy/keys and independent runtime absent |
| PRE-05 | Purple | Multi-workbook validation has finite memory and size limits | Explicit conservative batch bounds; streaming successor required beyond bounds |
| PRE-06 | Blue | Fee states lack actual monetary amounts, token/request units and reset timezone/calendar semantics insufficient for future usage metering | Open design refinement; do not invent consumption measurements or provider quotas. The schema is for offer discovery, not actual usage ledger. |
| PRE-07 | Blue | Actual semantic taxonomy definitions, ISO currency/country membership, true source authentication and Excel UI expansion not fully qualified | Open until implementation and independent evidence |
| PRE-08 | Purple | Candidate can still change its own tests and verification code without protected branch or trusted external verifier | Contained by pre-build-only gate; actual external trust and independent audit remain necessary |
| PRE-09 | Blue | Real PR path not run; live branch PR validation cannot be certified from push tests | Open live test evidence |
| PRE-10 | Purple | Original acceptance findings dependent on real artifacts or owner licensing cannot be closed in a pre-production mission | Explicitly retained as open/deferred, not relabeled fixed |

No production spreadsheet creation, research import, owner lock, release, or license assignment. The schema audit is source-based and not a guarantee of completeness. The production gate remains closed.
