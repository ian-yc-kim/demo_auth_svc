from fastapi import FastAPI

from demo_auth_svc.routers import google_auth, forum

app = FastAPI(debug=True)

app.include_router(google_auth.router)
app.include_router(forum.router)
