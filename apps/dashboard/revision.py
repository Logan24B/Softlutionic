from django.core.cache import cache


DASHBOARD_REVISION_KEY = 'softfactur_dashboard_revision'


def get_dashboard_revision():
    revision = cache.get(DASHBOARD_REVISION_KEY)
    if revision is None:
        revision = 1
        cache.set(DASHBOARD_REVISION_KEY, revision, None)
    return revision


def bump_dashboard_revision():
    try:
        return cache.incr(DASHBOARD_REVISION_KEY)
    except ValueError:
        cache.set(DASHBOARD_REVISION_KEY, 2, None)
        return 2
