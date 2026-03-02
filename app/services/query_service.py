from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import courses, categories, vouchers, bootcamps


# =====================================================
# UNIVERSAL MONGO SERIALIZER
# =====================================================
def serialize_mongo(data):

    if isinstance(data, list):
        return [serialize_mongo(item) for item in data]

    if isinstance(data, dict):
        return {
            key: serialize_mongo(value)
            for key, value in data.items()
        }

    if isinstance(data, ObjectId):
        return str(data)

    if isinstance(data, datetime):
        return data.isoformat()

    return data


# =====================================================
# LIST ALL COURSES
# =====================================================
async def list_courses():
    data = []
    async for doc in courses.find({"isDeleted": False}):
        data.append({
            "_id": doc["_id"],
            "title": doc["title"],
            "description": doc.get("description", "")
        })

    return serialize_mongo(data)


# =====================================================
# LIST CATEGORIES
# =====================================================
async def list_categories():
    data = []
    async for doc in categories.find({"isDeleted": False}):
        data.append({
            "_id": doc["_id"],
            "name": doc["name"]
        })

    return serialize_mongo(data)


# =====================================================
# LIST ALL ACTIVE VOUCHERS
# =====================================================
async def list_active_vouchers():

    data = []

    async for doc in vouchers.find({
        "isDeleted": False,
        "isActive": True
    }):

        data.append({
            "_id": doc["_id"],
            "name": doc["name"],
            "description": doc.get("description"),
            "price": doc.get("price")
        })

    return serialize_mongo(data)



# =====================================================
# COURSES UNDER CATEGORY
# =====================================================
async def list_courses_by_category_name(question: str):

    question_lower = question.lower()
    selected_category = None

    async for cat in categories.find({"isDeleted": False}):
        if cat["name"].lower() in question_lower:
            selected_category = cat
            break

    if not selected_category:
        return []

    data = []
    async for doc in courses.find({
        "category": selected_category["_id"],
        "isDeleted": False
    }):
        data.append({
            "_id": doc["_id"],
            "title": doc["title"],
            "description": doc.get("description", "")
        })

    return serialize_mongo(data)


# =====================================================
# COURSE FULL DETAILS
# =====================================================
async def get_course_details_by_name(question: str):

    question_lower = question.lower()

    async for doc in courses.find({"isDeleted": False}):

        if doc["title"].lower() in question_lower:

            # Populate vouchers properly
            voucher_list = []

            async for v in vouchers.find({
                "isDeleted": False,
                "isActive": True,
                "applicableCourses": doc["_id"]
            }):
                voucher_list.append({
                    "_id": v["_id"],
                    "name": v["name"],
                    "price": v.get("price"),
                    "description": v.get("description")
                })

            doc["vouchers"] = voucher_list

            return serialize_mongo({
                "_id": doc["_id"],
                "title": doc["title"],
                "overviewDescription": doc.get("overviewDescription"),
                "keyFeatures": doc.get("keyFeatures", []),
                "skillsCovered": doc.get("skillsCovered", []),
                "benefits": doc.get("benefits", []),
                "modules": doc.get("modules", []),
                "trainingOptions": doc.get("trainingOptions", {}),
                "vouchers": voucher_list
            })

    return None

# =====================================================
# COURSE SECTION (skills, features, etc.)
# =====================================================
async def get_course_section_by_name(question: str):

    question_lower = question.lower().strip()

    async for doc in courses.find({"isDeleted": False}):

        title_lower = doc["title"].lower()

        if title_lower in question_lower:

            # SKILLS
            if any(word in question_lower for word in ["skill", "skills covered"]):
                return serialize_mongo({
                    "title": doc["title"],
                    "skillsCovered": doc.get("skillsCovered", [])
                })

            # FEATURES
            if any(word in question_lower for word in ["feature", "key feature"]):
                return serialize_mongo({
                    "title": doc["title"],
                    "keyFeatures": doc.get("keyFeatures", [])
                })

            # BENEFITS
            if "benefit" in question_lower:
                return serialize_mongo({
                    "title": doc["title"],
                    "benefits": doc.get("benefits", [])
                })

            # MODULES
            if any(word in question_lower for word in ["module", "modules"]):
                return serialize_mongo({
                    "title": doc["title"],
                    "modules": doc.get("modules", [])
                })

            # TRAINING OPTIONS
            if any(word in question_lower for word in ["training", "mode"]):
                return serialize_mongo({
                    "title": doc["title"],
                    "trainingOptions": doc.get("trainingOptions", {})
                })

    return None

# =====================================================
# COURSE PRICING
# =====================================================
async def get_course_price_by_name(question: str):

    question_lower = question.lower()

    async for doc in courses.find({"isDeleted": False}):

        if doc["title"].lower() in question_lower:

            pricing_data = []

            for mode in doc.get("trainingOptions", {}).get("modes", []):
                pricing_data.append({
                    "mode": mode.get("mode"),
                    "originalPrice": mode.get("originalPrice"),
                    "offerPrice": mode.get("offerPrice"),
                    "discountPercentage": mode.get("discountPercentage"),
                    "description": mode.get("description")
                })

            return serialize_mongo({
                "course": doc["title"],
                "pricing": pricing_data
            })

    return None


# =====================================================
# VOUCHERS FOR SPECIFIC COURSE
# =====================================================
# async def get_vouchers_for_course(question: str):

#     question_lower = question.lower()

#     selected_course = None

#     # Step 1: Detect course from question
#     async for course in courses.find({"isDeleted": False}):

#         if course["title"].lower() in question_lower:
#             selected_course = course
#             break

#     if not selected_course:
#         return None

#     course_id = selected_course["_id"]

#     voucher_list = []

#     # Step 2: Fetch vouchers where course_id exists inside applicableCourses array
#     async for doc in vouchers.find({
#         "isDeleted": False,
#         "isActive": True,
#         "applicableCourses": {
#             "$in": [course_id]
#         }
#     }):

#         voucher_list.append({
#             "_id": doc["_id"],
#             "name": doc["name"],
#             "description": doc.get("description"),
#             "price": doc.get("price")
#         })

#     return serialize_mongo({
#         "course": selected_course["title"],
#         "vouchers": voucher_list
#     })


async def get_vouchers_for_course(question: str):

    question_lower = question.lower().strip()

    selected_course = None

    # -------------------------------------------------
    # Step 1: Extract acronym from question (CSA / CEH / CHFI)
    # -------------------------------------------------
    import re

    acronym_match = re.search(r"\((.*?)\)", question_lower)
    question_acronym = acronym_match.group(1).strip() if acronym_match else None

    # -------------------------------------------------
    # Step 2: Match course by EXACT acronym
    # -------------------------------------------------
    async for course in courses.find({"isDeleted": False}):

        title = course["title"]
        title_lower = title.lower().strip()

        course_acronym = None
        if "(" in title and ")" in title:
            course_acronym = title.split("(")[-1].split(")")[0].lower().strip()

        # ✅ Exact acronym match ONLY
        if question_acronym and course_acronym == question_acronym:
            selected_course = course
            break

        # ✅ Exact full title match ONLY
        if question_lower == title_lower:
            selected_course = course
            break

    # -------------------------------------------------
    # Step 3: If no course found → return empty safely
    # -------------------------------------------------
    if not selected_course:
        return serialize_mongo({
            "course": None,
            "vouchers": []
        })

    # -------------------------------------------------
    # Step 4: Fetch vouchers strictly by ObjectId
    # -------------------------------------------------
    voucher_list = []

    async for doc in vouchers.find({
        "isDeleted": False,
        "isActive": True,
        "applicableCourses": {
            "$in": [selected_course["_id"]]
        }
    }):
        voucher_list.append({
            "_id": doc["_id"],
            "name": doc["name"],
            "description": doc.get("description"),
            "price": doc.get("price")
        })

    return serialize_mongo({
        "course": selected_course["title"],
        "vouchers": voucher_list
    })

# =====================================================
# UPCOMING + RUNNING BOOTCAMPS
# =====================================================
async def list_upcoming_bootcamps():

    now = datetime.now(timezone.utc)
    data = []

    async for doc in bootcamps.find({
        "isDeleted": False,
        "status": "active"
    }):

        start_date = doc["startDate"]
        end_date = doc["endDate"]

        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)

        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        if start_date > now:

            days_left = (start_date - now).days

            message = (
                "Starting today! Don't miss it!" if days_left == 0
                else "1 day to go! Hurry up!" if days_left == 1
                else f"{days_left} days to go! Hurry up!"
            )

            data.append({
                "_id": doc["_id"],
                "title": doc["title"],
                "type": "upcoming",
                "startDate": start_date,
                "endDate": end_date,
                "message": message
            })

        elif start_date <= now <= end_date:

            days_remaining = (end_date - now).days

            data.append({
                "_id": doc["_id"],
                "title": doc["title"],
                "type": "running",
                "startDate": start_date,
                "endDate": end_date,
                "message": f"Ongoing! {days_remaining} days remaining."
            })

    data.sort(key=lambda x: x["startDate"])

    return serialize_mongo(data)


# =====================================================
# BOOTCAMP FULL DETAILS
# =====================================================
async def get_bootcamp_details_by_name(question: str):

    question_lower = question.lower()

    async for doc in bootcamps.find({
        "isDeleted": False,
        "status": "active"
    }):

        if doc["title"].lower() in question_lower:

            return serialize_mongo({
                "_id": doc["_id"],
                "title": doc["title"],
                "startDate": doc.get("startDate"),
                "endDate": doc.get("endDate"),
                "timeSlot": doc.get("timeSlot", {}),
                "pricing": doc.get("pricing", {}),
                "features": doc.get("features", {}),
                "agenda": doc.get("agenda", []),
                "keyTakeaways": doc.get("keyTakeaways", [])
            })

    return None




# =====================================================
# FIXED BOOTCAMP SECTION FETCH
# =====================================================
async def get_bootcamp_section_by_name(question: str):

    question_lower = question.lower().strip()

    # Find matching bootcamp EXACTLY and get latest one
    async for doc in bootcamps.find(
        {
            "isDeleted": False,
            "status": "active"
        }
    ).sort("createdAt", -1):   # 🔥 Always get latest bootcamp first

        title_lower = doc["title"].lower().strip()

        if title_lower in question_lower:

            # PRICING
            if any(word in question_lower for word in ["price", "pricing", "fee", "cost"]):
                return serialize_mongo({
                    "title": doc["title"],
                    "pricing": doc.get("pricing", {})
                })

            # AGENDA
            if "agenda" in question_lower:
                return serialize_mongo({
                    "title": doc["title"],
                    "agenda": doc.get("agenda", [])
                })

            # TIME SLOT
            if any(word in question_lower for word in ["time", "slot", "timing"]):
                return serialize_mongo({
                    "title": doc["title"],
                    "timeSlot": doc.get("timeSlot", {})
                })

            # FEATURES
            if "feature" in question_lower:
                return serialize_mongo({
                    "title": doc["title"],
                    "features": doc.get("features", {})
                })

            # DATES
            if any(word in question_lower for word in ["start", "end", "date"]):
                return serialize_mongo({
                    "title": doc["title"],
                    "startDate": doc.get("startDate"),
                    "endDate": doc.get("endDate")
                })

            # KEY TAKEAWAYS
            if "takeaway" in question_lower:
                return serialize_mongo({
                    "title": doc["title"],
                    "keyTakeaways": doc.get("keyTakeaways", [])
                })

    return None




# =====================================================
# GET VOUCHER BY NAME (ENTITY MATCH)
# =====================================================
async def get_voucher_by_name(question: str):

    question_lower = question.lower()

    async for doc in vouchers.find({
        "isDeleted": False,
        "isActive": True
    }):

        if doc["name"].lower() in question_lower:

            return serialize_mongo({
                "_id": doc["_id"],
                "name": doc["name"],
                "price": doc.get("price"),
                "description": doc.get("description")
            })

    return None