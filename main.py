if __name__ == "__main__":

    import uvicorn
    import sentry_sdk
    from isabelle.utils.env import env
    

    sentry_sdk.init(dsn=env.sentry_dsn, traces_sample_rate=1.0)
    sentry_sdk.profiler.start_profiler()
    uvicorn.run("app:api", port=3000)
