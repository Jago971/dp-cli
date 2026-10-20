# Cron services

Applies to a container whose entrypoint runs `cron`. Parent: [SKILL.md](SKILL.md).

- **The daemon runs as root.** `USER appuser` before `CMD ["cron", "-f"]` fails with `can't open or create /var/run/crond.pid`. Leave the daemon as root.
- **Cron starts jobs with a minimal environment.** The entrypoint writes the container's environment to a file, and the crontab line sources it before the job. A job without it silently falls back to defaults such as a default API URL.
- **Spawn the job as root and drop privileges inside it.** Use plain `crontab`, not `crontab -u <user>`, and wrap the real command in `su appuser -s /bin/sh -c "..."`. The crontab line redirects output (`>> /proc/1/fd/1`, which makes it visible in `docker logs`), and the shell opens that redirect as the job's user. `/proc/1/fd/1` belongs to root with mode 600, so a non-root job fails the redirect and never runs, with no error anywhere. The `su`'d child inherits the root-opened descriptor.
- **Prove a cron change with a real tick.** Done when the scheduled job's output appears in `docker logs` after a tick (or a manual run using the exact redirect the crontab uses), and the job reports the instance's own env values. A successful `docker build` and an `Up` container are silent about all of the above.
