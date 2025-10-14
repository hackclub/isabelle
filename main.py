if __name__ == "__main__":

    import uvicorn
    import sentry_sdk
    import isabelle.utils.rsvp_checker as rsvp_checker 
    

    sentry_sdk.init(dsn=env.sentry_dsn, traces_sample_rate=1.0)
    sentry_sdk.profiler.start_profiler()

    rsvp_checker.init()
    uvicorn.run("app:api", reload=True)
