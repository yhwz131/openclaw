# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup: camera names and locations, SSH hosts and aliases, preferred TTS voices, speaker/room names, device nicknames, anything environment-specific.

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

---

## SecureClaw Security Skill (v2.2.0)

Security hardening skill by Adversa AI. 15 core rules, 9 scripts, 4 pattern databases.

### Rules

Read and follow all 15 rules in `skills/secureclaw/SKILL.md` at all times.

### Scripts

All scripts are in `skills/secureclaw/scripts/`. Run with bash:

```
bash skills/secureclaw/scripts/quick-audit.sh          # Security audit (OWASP ASI mapped)
bash skills/secureclaw/scripts/quick-harden.sh         # Apply auto-fixes
bash skills/secureclaw/scripts/check-integrity.sh      # Verify cognitive file baselines
bash skills/secureclaw/scripts/check-privacy.sh        # Detect PII before posting
bash skills/secureclaw/scripts/scan-skills.sh          # Supply chain scan
bash skills/secureclaw/scripts/check-advisories.sh     # Vulnerability advisories
bash skills/secureclaw/scripts/emergency-response.sh   # Incident response
```
