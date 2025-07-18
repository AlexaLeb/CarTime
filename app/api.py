from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes import user, balance, Model, home, login
from database.database import init_db
from database.config import get_settings
from api_analytics.fastapi import Analytics
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)

settings = get_settings()

app = FastAPI()
app.include_router(login.router, tags=['login'], prefix='/login')
app.include_router(user.router, tags=['users'], prefix='/api/users')
app.include_router(balance.router, tags=['balance'], prefix='/api/balance')
app.include_router(Model.router, tags=['Model'], prefix='/api/model')
app.include_router(home.router, tags=['home'])

app.add_middleware(Analytics, api_key=settings.API_KEY)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    try:
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("Запуск приложения успешно завершен")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {str(e)}")
        raise


@app.on_event('shutdown')
async def shutdown():
    logger.info("Завершение работы")
    pass


if __name__ == "__main__":
    uvicorn.run('api:app', host='0.0.0.0', port=8080, reload=True, log_level='info')
