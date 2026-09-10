import json, sys, time, faulthandler
_started=time.monotonic()
def mark(phase,**extra):
    print(json.dumps({'phase':phase,'seconds':round(time.monotonic()-_started,6),**extra}),file=sys.stderr,flush=True)
def install():
    import pyshacl.entrypoints as entry
    original=entry.validate
    from functools import wraps
    @wraps(original)
    def measured(*args,**kwargs):
        mark('meta_shacl_start')
        result=original(*args,**kwargs)
        mark('meta_shacl_end',conforms=bool(result[0]))
        return result
    entry.validate=measured
    import cProfile, signal, pstats
    profile=cProfile.Profile(); profile.enable()
    def stop(*_):
        profile.disable()
        pstats.Stats(profile,stream=sys.stderr).sort_stats('cumtime').print_stats(24)
        raise TimeoutError('Diagnostic profiling stopped after five seconds.')
    signal.signal(signal.SIGALRM,stop); signal.setitimer(signal.ITIMER_REAL,5)

