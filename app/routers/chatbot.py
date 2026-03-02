from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import uuid

from app.services.llm_service import generate_response
from app.services.query_service import (
    list_courses,
    list_categories,
    list_courses_by_category_name,
    get_course_details_by_name,
    get_course_price_by_name,
    get_vouchers_for_course,
    get_voucher_by_name,
    list_upcoming_bootcamps,
    get_bootcamp_details_by_name,
    list_active_vouchers,
    get_bootcamp_section_by_name,
    get_course_section_by_name,   # ✅ MAKE SURE THIS EXISTS
)

router = APIRouter()

# =====================================================
# SESSION MEMORY
# =====================================================
session_memory = {}


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@router.post("/chat")
async def chat(req: ChatRequest):

    question_original = req.question
    question = question_original.lower().strip()

    # =====================================================
    # SESSION START
    # =====================================================
    if not req.session_id or question in ["hi", "hello", "hey"]:
        session_id = str(uuid.uuid4())
        session_memory[session_id] = {}

        return {
            "session_id": session_id,
            "answer": "Hello! 👋 Welcome to our course support.",
            "options": ["Course Category", "Bootcamps", "Vouchers"]
        }

    session_id = req.session_id
    session_memory.setdefault(session_id, {})
    memory = session_memory[session_id]

    is_bootcamp = "bootcamp" in question
    is_course = "course" in question

    # =====================================================
    # CATEGORY LIST
    # =====================================================
    if "category" in question and "under" not in question:
        return {
            "session_id": session_id,
            "categories": await list_categories()
        }

    # =====================================================
    # COURSES UNDER CATEGORY
    # =====================================================
    if "under" in question:
        data = await list_courses_by_category_name(question_original)
        if data:
            return {"session_id": session_id, "courses": data}

        return {
            "session_id": session_id,
            "answer": "No courses found under this category."
        }

    # =====================================================
    # PRICE HANDLING
    # =====================================================
    if any(word in question for word in ["price", "pricing", "fee", "cost"]):

        voucher = await get_voucher_by_name(question_original)
        if voucher:
            return {
                "session_id": session_id,
                "voucherPricing": voucher
            }

        pricing = await get_course_price_by_name(question_original)

        if not pricing:
            last_course = memory.get("last_course")
            if last_course:
                pricing = await get_course_price_by_name(last_course)

        if pricing:
            return {
                "session_id": session_id,
                "coursePricing": pricing
            }

    # =====================================================
    # VOUCHER ENTITY MATCH
    # =====================================================
    voucher_entity = await get_voucher_by_name(question_original)

    if voucher_entity:
        memory.pop("last_course", None)
        memory.pop("last_bootcamp", None)

        return {
            "session_id": session_id,
            "voucher": voucher_entity
        }

    # =====================================================
    # VOUCHER LIST
    # =====================================================
    if "voucher" in question or "discount" in question:

        voucher_info = await get_vouchers_for_course(question_original)

        if not voucher_info:
            last_course = memory.get("last_course")
            if last_course:
                voucher_info = await get_vouchers_for_course(last_course)

        if voucher_info and voucher_info.get("vouchers"):
            return {
                "session_id": session_id,
                "vouchers": voucher_info["vouchers"]
            }

        all_vouchers = await list_active_vouchers()
        if all_vouchers:
            return {
                "session_id": session_id,
                "vouchers": all_vouchers
            }

        return {
            "session_id": session_id,
            "answer": "No vouchers available."
        }

    # =====================================================
    # BOOTCAMPS (SECTION FIRST FIX)
    # =====================================================
    if is_bootcamp or any(word in question for word in [
        "agenda", "time", "slot", "timing",
        "price", "pricing", "fee", "cost",
        "feature", "date", "start", "end", "takeaway"
    ]):

        # ✅ FIRST check specific section
        section = await get_bootcamp_section_by_name(question_original)

        if section:
            memory["last_bootcamp"] = section["title"]
            memory.pop("last_course", None)

            return {
                "session_id": session_id,
                "bootcampSection": section
            }

        # ✅ ELSE full details
        details = await get_bootcamp_details_by_name(question_original)

        if details:
            memory["last_bootcamp"] = details["title"]
            memory.pop("last_course", None)

            return {
                "session_id": session_id,
                "bootcamp": details
            }

        bootcamps = await list_upcoming_bootcamps()
        if bootcamps:
            return {
                "session_id": session_id,
                "bootcamps": bootcamps
            }

        return {
            "session_id": session_id,
            "answer": "No bootcamps available."
        }

    # =====================================================
    # 🔥 COURSE SECTION FIRST (FIXED)
    # =====================================================
    if is_course or any(word in question for word in [
        "detail", "about", "explain", "description",
        "skill", "feature", "benefit", "module", "training"
    ]):

        # ✅ FIRST check if specific section requested
        section = await get_course_section_by_name(question_original)

        if section:
            memory["last_course"] = section["title"]
            memory.pop("last_bootcamp", None)

            return {
                "session_id": session_id,
                "courseSection": section
            }

        # ✅ ELSE full course
        course = await get_course_details_by_name(question_original)

        if course:
            memory["last_course"] = course["title"]
            memory.pop("last_bootcamp", None)

            return {
                "session_id": session_id,
                "course": course
            }

    # =====================================================
    # GENERAL COURSE LIST
    # =====================================================
    if "course" in question:
        return {
            "session_id": session_id,
            "courses": await list_courses()
        }

    # =====================================================
    # AI FALLBACK
    # =====================================================
    response = await generate_response(question_original)
    return {
        "session_id": session_id,
        "answer": response
    }