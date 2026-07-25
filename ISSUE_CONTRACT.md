# Issue Contract — `spacex-propulsion-monitor`

## Pain
Chamber/MR/vibe anomalies must raise RED/YELLOW for launch holds.

## Claim
Health index maps extreme chamber/vibe to RED and healthy samples to GREEN.

## Proof
```bash
python3 job-app/helix/proofs/proof_prop.py
```

## Done when
Proof exits 0. Architecture (strand/integrity/helix) is **not** a substitute for this proof.

## Anti-claim
Not official engine redlines.
