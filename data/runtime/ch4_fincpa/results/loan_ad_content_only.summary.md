# Review Summary: loan_ad_content_only

- final decision: `non_compliant`
- should escalate: `true`
- review scope: `content_only`
- product scope hint: `loan`
- channel scope hint: `advertising`
- applicable rules: `3`
- failed rules: `1`
- uncertain rules: `0`
- missing SIR fields: `2`

## Triggered Citations

- `금융소비자 보호에 관한 법률 제22조④` | 금융상품등에 관한 광고 관련 준수사항 | 대출성 상품 광고 시 대출이자율 범위·산정방법 등을 불명확하게 표시하거나 일 단위 표시로 저렴한 것으로 오인하게 하는 행위를 금지한다.

## Missing SIR Fields

- `loan_interest_timing`
- `loan_rate_basis`

## Failed Rules

- `law_fincpa_main_2026-01-02:제22조:④:ob04:rule01` | `prohibited_presence` | prohibited_condition_detected_or_required_disclosure_missing | fields: loan_rate_basis, loan_interest_timing
  legal basis: `금융소비자 보호에 관한 법률 제22조④`
  source text: 4. 대출성 상품 가. 대출이자율의 범위ㆍ산정방법, 대출이자의 지급ㆍ부과 시기 및 부수적 혜택ㆍ비용을 명확히 표시하지 아니하여 금융소비자가 오인하게 하는 행위 나. 대출이자를 일 단위로 표시하여 대출이자가 저렴한 것으로 오인하게 하는 행위 등 금융소비자 보호를 위하여 대통령령으로 정하는 행위

## Uncertain Rules

- none
