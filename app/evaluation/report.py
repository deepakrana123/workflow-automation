"""
app/evaluation/report.py

Console reporter for EvaluationReport.

Formats and prints a human-readable evaluation summary.
This is the only file in the evaluation package that produces output.
"""

from app.evaluation.models import EvaluationReport


def print_report(report: EvaluationReport) -> None:
    """
    Pretty-print an EvaluationReport to stdout.

    Example output:

        ===================================
        MFlows Evaluation Report
        ===================================
        Workflows        : 2
        Actions          : 18
        Triggers         : 6
        -----------------------------------
        Action Accuracy  : 88.9%
        Trigger Accuracy : 100.0%
        Avg Similarity   : 0.84
        -----------------------------------
        Unknown Actions  : 2
        Unknown Triggers : 0
        ===================================

        Per-Workflow Breakdown
        ===================================
        Workflow: Loan Approval
          Actions  : 10  |  Correct: 9  |  Accuracy: 90.0%
          Triggers :  3  |  Correct: 3  |  Accuracy: 100.0%

        Workflow: Fraud Detection
          Actions  :  8  |  Correct: 7  |  Accuracy: 87.5%
          Triggers :  3  |  Correct: 3  |  Accuracy: 100.0%
        ===================================
    """
    sep = "=" * 35
    dash = "-" * 35

    print(sep)
    print("MFlows Evaluation Report")
    print(sep)
    print(f"{'Workflows':<20}: {report.total_workflows}")
    print(f"{'Actions':<20}: {report.total_actions}")
    print(f"{'Triggers':<20}: {report.total_triggers}")
    print(dash)
    print(f"{'Action Accuracy':<20}: {report.action_accuracy * 100:.1f}%")
    print(f"{'Trigger Accuracy':<20}: {report.trigger_accuracy * 100:.1f}%")
    print(f"{'Avg Similarity':<20}: {report.average_similarity:.2f}")
    print(dash)
    print(f"{'Unknown Actions':<20}: {report.unknown_actions}")
    print(f"{'Unknown Triggers':<20}: {report.unknown_triggers}")
    print(sep)

    if report.workflow_results:
        print()
        print("Per-Workflow Breakdown")
        print(sep)

        for wf in report.workflow_results:
            total_actions = len(wf.action_results)
            correct_actions = sum(1 for r in wf.action_results if r.correct)
            action_pct = (
                correct_actions / total_actions * 100 if total_actions else 0.0
            )

            total_triggers = len(wf.trigger_results)
            correct_triggers = sum(1 for r in wf.trigger_results if r.correct)
            trigger_pct = (
                correct_triggers / total_triggers * 100 if total_triggers else 0.0
            )

            print(f"Workflow: {wf.workflow_name}")
            print(
                f"  Actions  : {total_actions:>3}  |  "
                f"Correct: {correct_actions:>3}  |  "
                f"Accuracy: {action_pct:.1f}%"
            )
            print(
                f"  Triggers : {total_triggers:>3}  |  "
                f"Correct: {correct_triggers:>3}  |  "
                f"Accuracy: {trigger_pct:.1f}%"
            )
            print()

        print(sep)
