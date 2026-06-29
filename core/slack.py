import os, requests
from dotenv import load_dotenv
load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

def send_slack_notification(repo: str, pr_number: int, verdict: dict):
    if not SLACK_WEBHOOK_URL:
        print("  No Slack webhook configured, skipping")
        return False

    final = verdict.get("final", {})
    impact = verdict.get("debate_impact", {})
    conflicts = verdict.get("conflicts", [])

    verdict_emoji = {
        "BLOCK": ":no_entry:",
        "REQUEST_CHANGES": ":warning:",
        "APPROVE": ":white_check_mark:"
    }.get(final.get("final_verdict", ""), ":question:")

    verdict_color = {
        "BLOCK": "#E24B4A",
        "REQUEST_CHANGES": "#EF9F27",
        "APPROVE": "#3fb950"
    }.get(final.get("final_verdict", ""), "#888780")

    conflict_text = f"{len(conflicts)} conflicts detected" if conflicts else "No conflicts"
    impact_score = impact.get("score", 0)

    message = {
        "attachments": [
            {
                "color": verdict_color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{verdict_emoji} CodeCouncil Review — {final.get('final_verdict', 'UNKNOWN')}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Repo:* `{repo}` | *PR:* #{pr_number}\n{final.get('summary', '')}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Confidence:*\n{final.get('confidence', 0)}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Debate Impact:*\n{impact_score}/100"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Conflicts:*\n{conflict_text}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Winner:*\nSecurityAuditor"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*TechLead:* {final.get('who_won_debate', '')[:200]}..."
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View PR on GitHub"
                                },
                                "url": f"https://github.com/{repo}/pull/{pr_number}",
                                "style": "primary"
                            }
                        ]
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=10
        )
        if response.status_code == 200:
            print("  Slack notification sent")
            return True
        else:
            print(f"  Slack error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  Slack error: {e}")
        return False