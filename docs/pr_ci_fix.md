Fix the cross-platform eval-set hash mismatch that prevents the Linux CI gate from comparing against the Windows-generated baseline. Pin eval-set JSONL files to LF, make v1/v2 builders write LF explicitly, and regenerate the baseline and reports from the same committed bytes. Item content and labels remain unchanged.

Validation: 46 Core student tests and 3 eval-set builder tests pass. The new builder regression assertion rejects CRLF output. The working and committed dataset hashes both equal 4d100783aa8e. Local gate accepts swarm/fixed and blocks seeded_regression on pass_rate. Lab8 and the separate Day08 source are unchanged.

The previous main run failed at Evaluate and gate the PR swarm: https://github.com/miao1114/K5-L3B-DAY09-NguyenDucMinh-2A202603765-EvaluationandFailureAnalysis/actions/runs/44232891255

Reports and generated evaluation documents now reference the LF dataset. Confirm the hosted eval-gate job succeeds before merging this repair PR.
