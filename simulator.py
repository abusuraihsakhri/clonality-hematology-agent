"""Synthetic stress-test helper for the legacy compatibility interface."""

import random
import sys
import time

from agents.base import AuditLogger, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def run_simulation(iterations: int = 100):
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero")

    print(f"Starting synthetic rule-review simulation ({iterations} tasks)...")
    supervisor = SystemSupervisor(model_provider="mock")
    start_time = time.time()
    nominal_count = 0
    elevated_count = 0
    critical_count = 0
    identifier_blocks = 0
    identifier_trials = 0

    for index in range(iterations):
        payload = SystemTaskPayload(
            task_id=f"SIM-{index + 1:04d}",
            target_identifier=f"SPECIMEN-{random.randint(100, 999)}",
            primary_metric=round(random.uniform(5.0, 40.0), 2),
            secondary_metric=round(random.uniform(1.0, 20.0), 2),
            status_descriptor=random.choice(
                ["NOMINAL", "DISCORDANT_ANOMALY", "MUTANT_VARIANT", "REVIEWED"]
            ),
            is_critical_flag=random.random() < 0.15,
        )

        dossier = supervisor.process_task(payload)
        if dossier.overall_urgency.value == "CRITICAL_STAT_PANIC":
            critical_count += 1
        elif dossier.overall_urgency.value == "ELEVATED_RISK":
            elevated_count += 1
        else:
            nominal_count += 1

        if (index + 1) % 25 == 0:
            identifier_trials += 1
            try:
                PHIGuard.assert_no_phi(
                    f"Patient Example Person MRN-{random.randint(100000, 999999)} test"
                )
            except SecurityException:
                identifier_blocks += 1

    elapsed = time.time() - start_time
    rate = iterations / max(0.001, elapsed)
    block_rate = (
        identifier_blocks / identifier_trials * 100 if identifier_trials else 0.0
    )

    print("\n" + "=" * 70)
    print("SYNTHETIC SIMULATION SUMMARY")
    print("=" * 70)
    print(f"Total tasks:               {iterations}")
    print(f"Elapsed time:              {elapsed:.3f} seconds ({rate:.1f} tasks/sec)")
    print(f"Routine outcomes:          {nominal_count} ({nominal_count / iterations * 100:.1f}%)")
    print(f"Elevated rule outcomes:    {elevated_count} ({elevated_count / iterations * 100:.1f}%)")
    print(f"Critical-flag outcomes:    {critical_count} ({critical_count / iterations * 100:.1f}%)")
    print(f"Identifier-screen trials:  {identifier_trials}")
    print(f"Identifier-screen blocks:  {identifier_blocks} ({block_rate:.1f}% of injected examples)")
    print(f"Audit blocks:              {len(AuditLogger.get_trail())}")
    print(f"HMAC integrity check:      {AuditLogger.verify_integrity()}")
    print("=" * 70)


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_simulation(count)
