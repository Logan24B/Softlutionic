"""Start polling only in initialized serving workers, never during migrations/tests."""

def post_worker_init(worker):
    from apps.mobile_api.contact_watcher import start
    start()


def worker_exit(server, worker):
    from apps.mobile_api.contact_watcher import stop
    stop()
