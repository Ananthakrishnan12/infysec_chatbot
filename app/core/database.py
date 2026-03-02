from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import MONGO_URL, DB_NAME

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

courses = db.courses
categories = db.coursecategories
bootcamps = db.bootcamps
vouchers = db.vouchers
