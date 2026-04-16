#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>
#include <linux/sched.h>
#include <linux/pid.h>
#include <linux/sched/signal.h>

#define MODULE_NAME   "aimos_scheduler"
#define PROC_ENTRY    "aimos_scheduler"
#define BUFFER_SIZE   64

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Mentolka1207");
MODULE_DESCRIPTION("AI_M_OS AI Scheduler — adjusts process priorities via AI-daemon");
MODULE_VERSION("0.1");

static struct proc_dir_entry *proc_entry;

/* AI-daemon пишет: "<pid> <nice_value>\n" */
static ssize_t scheduler_write(struct file *file, const char __user *buf,
                                size_t count, loff_t *ppos)
{
    char kbuf[BUFFER_SIZE];
    pid_t pid;
    int nice_val;
    struct pid *pid_struct;
    struct task_struct *task;

    if (count >= BUFFER_SIZE)
        return -EINVAL;

    if (copy_from_user(kbuf, buf, count))
        return -EFAULT;

    kbuf[count] = '\0';

    if (sscanf(kbuf, "%d %d", &pid, &nice_val) != 2) {
        pr_err("aimos_scheduler: invalid format. Expected: <pid> <nice>\n");
        return -EINVAL;
    }

    if (nice_val < -20 || nice_val > 19) {
        pr_err("aimos_scheduler: nice %d out of range [-20, 19]\n", nice_val);
return -EINVAL;
    }

    pid_struct = find_get_pid(pid);
    if (!pid_struct) {
        pr_err("aimos_scheduler: PID %d not found\n", pid);
        return -ESRCH;
    }

    task = pid_task(pid_struct, PIDTYPE_PID);
    if (!task) {
        put_pid(pid_struct);
        pr_err("aimos_scheduler: task for PID %d not found\n", pid);
        return -ESRCH;
    }

    set_user_nice(task, nice_val);
    pr_info("aimos_scheduler: PID %d -> nice %d\n", pid, nice_val);

    put_pid(pid_struct);
    return count;
}

static ssize_t scheduler_read(struct file *file, char __user *buf,
                               size_t count, loff_t *ppos)
{
char msg[] = "AI_M_OS Scheduler active. Write: <pid> <nice_value>\n";
    size_t len = strlen(msg);

    if (*ppos >= len)
        return 0;
    if (copy_to_user(buf, msg, len))
        return -EFAULT;

    *ppos += len;
    return len;
}

static const struct proc_ops scheduler_ops = {
    .proc_read  = scheduler_read,
    .proc_write = scheduler_write,
};

static int __init aimos_scheduler_init(void)
{
    proc_entry = proc_create(PROC_ENTRY, 0666, NULL, &scheduler_ops);
    if (!proc_entry) {
        pr_err("aimos_scheduler: failed to create /proc/%s\n", PROC_ENTRY);
        return -ENOMEM;
    }
    pr_info("aimos_scheduler: loaded. Interface: /proc/%s\n", PROC_ENTRY);
    return 0;
}

static void __exit aimos_scheduler_exit(void)
{
    proc_remove(proc_entry);
    pr_info("aimos_scheduler: unloaded\n");
}

module_init(aimos_scheduler_init);
module_exit(aimos_scheduler_exit);
