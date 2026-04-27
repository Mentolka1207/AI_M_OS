// SPDX-License-Identifier: GPL-2.0
/*
 * aimos_scheduler.c — AI_M_OS scheduler kernel module
 * Creates /proc/aimos_scheduler
 *   read  → returns module status as key:value lines
 *   write → accepts "pid nice\n" to renice a process
 *
 * Tested on kernel 6.x (uses proc_ops, seq_file).
 * Build: see Makefile alongside this file.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/uaccess.h>
#include <linux/sched.h>
#include <linux/pid.h>
#include <linux/sched/signal.h>
#include <linux/string.h>
#include <linux/ktime.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("AI_M_OS / Mentolka1207");
MODULE_DESCRIPTION("AI_M_OS scheduler interface via /proc/aimos_scheduler");
MODULE_VERSION("0.1");

#define PROC_NAME    "aimos_scheduler"
#define CMD_BUF_SIZE 64

/* --- state tracked for status output --- */
static int    last_pid   = -1;
static int    last_nice  = 0;
static int    total_ops  = 0;
static char   last_err[64] = "none";

/* ------------------------------------------------------------------ */
/*  seq_file read handler — defines the format kernel_iface.py parses */
/* ------------------------------------------------------------------ */
static int aimos_sched_show(struct seq_file *m, void *v)
{
    seq_printf(m, "status: active\n");
    seq_printf(m, "version: 0.1\n");
    seq_printf(m, "last_pid: %d\n",  last_pid);
    seq_printf(m, "last_nice: %d\n", last_nice);
    seq_printf(m, "total_ops: %d\n", total_ops);
    seq_printf(m, "last_error: %s\n", last_err);
    return 0;
}

static int aimos_sched_open(struct inode *inode, struct file *file)
{
    return single_open(file, aimos_sched_show, NULL);
}

/* ------------------------------------------------------------------ */
/*  write handler — protocol: "pid nice\n"                            */
/*  example:  echo "1234 5" > /proc/aimos_scheduler                   */
/* ------------------------------------------------------------------ */
static ssize_t aimos_sched_write(struct file *file,
                                  const char __user *ubuf,
                                  size_t count, loff_t *ppos)
{
    char buf[CMD_BUF_SIZE];
    int  pid, nice_val, ret;
    struct pid      *pid_struct;
    struct task_struct *task;

    if (count >= CMD_BUF_SIZE)
        return -EINVAL;

    if (copy_from_user(buf, ubuf, count))
        return -EFAULT;

    buf[count] = '\0';

    /* parse "pid nice" */
    ret = sscanf(buf, "%d %d", &pid, &nice_val);
    if (ret != 2) {
        snprintf(last_err, sizeof(last_err), "bad_format");
        return -EINVAL;
    }

    /* clamp nice to [-20, 19] */
    if (nice_val < -20) nice_val = -20;
    if (nice_val >  19) nice_val =  19;

    rcu_read_lock();
    pid_struct = find_get_pid(pid);
    if (!pid_struct) {
        rcu_read_unlock();
        snprintf(last_err, sizeof(last_err), "pid_%d_not_found", pid);
        return -ESRCH;
    }

    task = pid_task(pid_struct, PIDTYPE_PID);
    if (!task) {
        put_pid(pid_struct);
        rcu_read_unlock();
        snprintf(last_err, sizeof(last_err), "task_%d_not_found", pid);
        return -ESRCH;
    }

    /*
     * set_user_nice() requires the task_rq lock held by the caller.
     * We grab it via the standard helper.
     */
    set_user_nice(task, nice_val);

    last_pid  = pid;
    last_nice = nice_val;
    total_ops++;
    snprintf(last_err, sizeof(last_err), "none");

    put_pid(pid_struct);
    rcu_read_unlock();

    pr_info("aimos_scheduler: renice pid=%d nice=%d\n", pid, nice_val);
    return count;
}

/* ------------------------------------------------------------------ */
/*  proc_ops — kernel ≥ 5.6 API                                       */
/* ------------------------------------------------------------------ */
static const struct proc_ops aimos_sched_fops = {
    .proc_open    = aimos_sched_open,
    .proc_read    = seq_read,
    .proc_write   = aimos_sched_write,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

/* ------------------------------------------------------------------ */
/*  module init / exit                                                 */
/* ------------------------------------------------------------------ */
static int __init aimos_sched_init(void)
{
    struct proc_dir_entry *entry;

    entry = proc_create(PROC_NAME, 0666, NULL, &aimos_sched_fops);
    if (!entry) {
        pr_err("aimos_scheduler: failed to create /proc/%s\n", PROC_NAME);
        return -ENOMEM;
    }

    pr_info("aimos_scheduler: loaded — /proc/%s ready\n", PROC_NAME);
    return 0;
}

static void __exit aimos_sched_exit(void)
{
    remove_proc_entry(PROC_NAME, NULL);
    pr_info("aimos_scheduler: unloaded\n");
}

module_init(aimos_sched_init);
module_exit(aimos_sched_exit);
