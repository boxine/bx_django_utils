_conversion_powers = {
    'KB': 1,
    'MB': 2,
    'GB': 3,
    'TB': 4,
}


def cgroup_memory_usage(unit='B', cgroup_mem_file='/sys/fs/cgroup/memory/memory.usage_in_bytes'):
    """
    Returns the memory usage of the cgroup the Python interpreter is running in.

    This is handy for getting the memory usage inside a Docker container since they are
    implemented using cgroups.
    With conventional tools (e.g. psutil) this is not possible, because they often rely on
    stats reported by /proc, but that one reports metrics from the host system.
    """
    with open(cgroup_mem_file, 'r') as infile:
        usage_bytes = infile.readline()
    usage_bytes = int(usage_bytes)

    if usage_bytes == 0 or unit == 'B':
        return usage_bytes

    return usage_bytes / 1024 ** _conversion_powers[unit]
