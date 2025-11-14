from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import logging
import sys

# 配置日志 - 输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="参考文献校验工具API",
    description="医学科研参考文献校验、补全和纠正工具",
    version="1.0.0"
)

logger.info("="*80)
logger.info("参考文献校验工具 API 启动中...")
logger.info("="*80)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["references"])


@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI 应用启动完成")
    logger.info("API 文档地址: http://localhost:8000/docs")
    logger.info("等待请求...")


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"\n{'='*80}")
    logger.info(f"收到请求: {request.method} {request.url.path}")
    logger.info(f"客户端: {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
    logger.info(f"响应状态: {response.status_code}")
    return response


@app.get("/")
async def root():
    return {"message": "参考文献校验工具API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}

