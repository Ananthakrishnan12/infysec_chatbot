from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import uuid

from app.services.llm_service import generate_response
from app.services.query_service import (
    list_courses,
    list_categories,
    list_courses_by_category_id,
    get_course_details_by_id,
    get_voucher_by_id,
    list_active_vouchers,
    list_upcoming_bootcamps,
    get_bootcamp_details_by_id,
    get_course_section_by_name
)

router = APIRouter()
session_memory = {}


class ChatRequest(BaseModel):
    question: Optional[str] = None
    session_id: Optional[str] = None
    action: Optional[str] = None


@router.post("/chat")
async def chat(req: ChatRequest):

    question_original = (req.question or "").strip()
    question = question_original.lower()

    # ===============================
    # SESSION START
    # ===============================
    if (
        not req.session_id
        or question in ["hi", "hello", "hey"]
        or "back to home" in question
    ):
        session_id = req.session_id or str(uuid.uuid4())
        session_memory[session_id] = {}

        return {
            "session_id": session_id,
            "answer": "Hello! 👋 Welcome to our course support.",
            "quick_links": [
                {"label": "📚 Course Category", "value": "Show Course Category"},
                {"label": "🎓 Bootcamps", "value": "Show upcoming bootcamps"},
                {"label": "🎟 Vouchers", "value": "Show available vouchers"},
            ]
        }

    session_id = req.session_id
    session_memory.setdefault(session_id, {})
    memory = session_memory[session_id]

    # =====================================================
    # 🔥 1. COURSE BY ID (HIGHEST PRIORITY)
    # =====================================================
    if (
        (req.action and req.action.startswith("course:")) or
        question.startswith("course:")
    ):

        course_id = (
            req.action.split(":")[1]
            if req.action and req.action.startswith("course:")
            else question.split(":")[1]
        )

        course = await get_course_details_by_id(course_id)

        if course:
            memory["last_course_id"] = course_id

            return {
                "session_id": session_id,
                "course": course,
                "quick_links": [
                    {"label": "⭐ Key Features", "value": "Show key features"},
                    {"label": "🧠 Skills Covered", "value": "Show skills"},
                    {"label": "📑 Modules", "value": "Show modules"},
                    {"label": "💰 Pricing", "value": "Show pricing"},
                    {"label": "⬅ Back to Course Category", "value": "Show Course Category"},
                    {"label": "🏠 Back to Home", "value": "hi"}
                ]
            }

    # =====================================================
    # 🔥 2. CATEGORY BY ID
    # =====================================================
    if (
        (req.action and req.action.startswith("category:")) or
        question.startswith("category:")
    ):

        category_id = (
            req.action.split(":")[1]
            if req.action and req.action.startswith("category:")
            else question.split(":")[1]
        )

        courses = await list_courses_by_category_id(category_id)

        if courses:
            return {
                "session_id": session_id,
                "courses": courses,
                "quick_links": [
                    {"label": "⬅ Back to Course Category", "value": "Show Course Category"},
                    {"label": "🏠 Back to Home", "value": "hi"}
                ]
            }

        return {
            "session_id": session_id,
            "answer": "❌ No courses found under this category.",
            "quick_links": [
                {"label": "📚 View Course Category", "value": "Show Course Category"},
                {"label": "🏠 Back to Home", "value": "hi"}
            ]
        }

    # =====================================================
    # 🔥 3. COURSE SECTIONS (USING MEMORY)
    # =====================================================
    if any(word in question for word in ["feature", "skill", "module", "benefit"]):

        course_id = memory.get("last_course_id")

        if course_id:
            section = await get_course_section_by_name(question_original)

            if section:
                return {
                    "session_id": session_id,
                    "courseSection": section,
                    "quick_links": [
                        {"label": "⬅ Back to Course Details", "value": f"course:{course_id}"},
                        {"label": "🏠 Back to Home", "value": "hi"}
                    ]
                }

    # =====================================================
    # 🔥 4. BOOTCAMP BY ID
    # =====================================================
    if req.action and req.action.startswith("bootcamp:"):

        bootcamp_id = req.action.split(":")[1]
        bootcamp = await get_bootcamp_details_by_id(bootcamp_id)

        if bootcamp:
            return {
                "session_id": session_id,
                "bootcamp": bootcamp,
                "quick_links": [
                    {"label": "⬅ Back to Bootcamps", "value": "Show upcoming bootcamps"},
                    {"label": "🏠 Back to Home", "value": "hi"}
                ]
            }

    # =====================================================
    # 🔥 5. VOUCHER BY ID
    # =====================================================
    if req.action and req.action.startswith("voucher:"):

        voucher_id = req.action.split(":")[1]
        voucher = await get_voucher_by_id(voucher_id)

        if voucher:
            return {
                "session_id": session_id,
                "voucher": voucher,
                "quick_links": [
                    {"label": "🎟 View All Vouchers", "value": "Show available vouchers"},
                    {"label": "🏠 Back to Home", "value": "hi"}
                ]
            }

    # =====================================================
    # CATEGORY LIST
    # =====================================================
    if "category" in question and not question.startswith("category:"):
        return {
            "session_id": session_id,
            "categories": await list_categories(),
            "quick_links": [
                {"label": "🏠 Back to Home", "value": "hi"}
            ]
        }

    # =====================================================
    # BOOTCAMPS
    # =====================================================
    if "bootcamp" in question:
        return {
            "session_id": session_id,
            "bootcamps": await list_upcoming_bootcamps(),
            "quick_links": [
                {"label": "🏠 Back to Home", "value": "hi"}
            ]
        }

    # =====================================================
    # VOUCHERS
    # =====================================================
    if "voucher" in question or "discount" in question:
        return {
            "session_id": session_id,
            "vouchers": await list_active_vouchers(),
            "quick_links": [
                {"label": "🏠 Back to Home", "value": "hi"}
            ]
        }

    # =====================================================
    # COURSE LIST (LOWEST PRIORITY)
    # =====================================================
    if "course" in question and not question.startswith("course:"):
        return {
            "session_id": session_id,
            "courses": await list_courses(),
            "quick_links": [
                {"label": "📚 Course Category", "value": "Show Course Category"},
                {"label": "🏠 Back to Home", "value": "hi"}
            ]
        }

    # =====================================================
    # FALLBACK
    # =====================================================
    response = await generate_response(question_original)

    return {
        "session_id": session_id,
        "answer": response,
        "quick_links": [
            {"label": "🏠 Back to Home", "value": "hi"}
        ]
    }