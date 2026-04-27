savedcmd_aimos_scheduler.mod := printf '%s\n'   aimos_scheduler.o | awk '!x[$$0]++ { print("./"$$0) }' > aimos_scheduler.mod
