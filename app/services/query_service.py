# ======================================================================
# New Code
# ======================================================================

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
        return {key: serialize_mongo(value) for key, value in data.items()}

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

        title = doc["title"]

        data.append({
            "_id": doc["_id"],
            "title": title,
            "description": doc.get("description", ""),
            "quick_link": {
                "label": f"View Details of {title}",
                "value": str(doc["_id"])
            }
        })

    return serialize_mongo(data)


# =====================================================
# LIST CATEGORIES
# =====================================================
async def list_categories():

    data = []

    async for doc in categories.find({"isDeleted": False}):

        category_name = doc["name"]

        data.append({
            "_id": doc["_id"],
            "name": category_name,
            "quick_link": {
                "label": f"View Courses in {category_name}",
                "value": f"category:{doc['_id']}"
            }
        })

    return serialize_mongo(data)


# =====================================================
# COURSES BY CATEGORY ID
# =====================================================
async def list_courses_by_category_id(category_id: str):

    data = []

    async for doc in courses.find({
        "category": ObjectId(category_id),
        "isDeleted": False
    }):

        title = doc["title"]

        data.append({
            "_id": doc["_id"],
            "title": title,
            "description": doc.get("description", ""),
            "quick_link": {
                "label": f"View Details of {title}",
                "value": f"course:{doc['_id']}"
            }
        })

    return serialize_mongo(data)


# =====================================================
# COURSES UNDER CATEGORY (TEXT MATCH SUPPORT)
# =====================================================
# async def list_courses_by_category_name(question: str):

#     question_lower = question.lower()
#     selected_category = None

#     async for cat in categories.find({"isDeleted": False}):

#         if cat["name"].lower() in question_lower:
#             selected_category = cat
#             break

#     if not selected_category:
#         return []

#     data = []

#     async for doc in courses.find({
#         "category": selected_category["_id"],
#         "isDeleted": False
#     }):

#         title = doc["title"]

#         data.append({
#             "_id": doc["_id"],
#             "title": title,
#             "description": doc.get("description", ""),
#             "quick_link": {
#                 "label": f"View Details of {title}",
#                 "value": str(doc["_id"])
#             }
#         })

#     return serialize_mongo(data)


async def list_courses_by_category_name(question: str):

    question_lower = question.lower().strip()
    selected_category = None

    # Extract category name from question
    # Example: "View Courses in Ethical hacking"
    if "in" in question_lower:
        category_query = question_lower.split("in")[-1].strip()
    else:
        category_query = question_lower

    # Find exact matching category
    async for cat in categories.find({"isDeleted": False}):

        if cat["name"].lower() == category_query:
            selected_category = cat
            break

    # ❌ If no exact match → return empty
    if not selected_category:
        return []

    data = []

    async for doc in courses.find({
        "category": selected_category["_id"],
        "isDeleted": False
    }):

        title = doc["title"]

        data.append({
            "_id": doc["_id"],
            "title": title,
            "description": doc.get("description", ""),
            "quick_link": {
                "label": f"View Details of {title}",
                "value": f"course:{doc['_id']}"
            }
        })

    return serialize_mongo(data)


# =====================================================
# COURSE DETAILS BY ID
# =====================================================
async def get_course_details_by_id(course_id: str):

    doc = await courses.find_one({
        "_id": ObjectId(course_id),
        "isDeleted": False
    })

    if not doc:
        return None

    voucher_list = []

    # Get voucher IDs stored inside course document
    voucher_ids = doc.get("vouchers", [])

    if voucher_ids:

        async for v in vouchers.find({
            "_id": {"$in": voucher_ids},
            "isDeleted": False,
            "isActive": True
        }):

            voucher_list.append({
                "_id": v["_id"],
                "name": v["name"],
                "price": v.get("price"),
                "description": v.get("description"),
                "quick_link": {
                    "label": f"View Voucher Details: {v['name']}",
                    "value": f"Show voucher {v['name']}"
                }
            })

    return serialize_mongo({
        "_id": doc["_id"],
        "title": doc["title"],
        "overviewDescription": doc.get("overviewDescription"),
        "keyFeatures": doc.get("keyFeatures", []),
        "skillsCovered": doc.get("skillsCovered", []),
        "benefits": doc.get("benefits", []),
        "modules": doc.get("modules", []),
        "trainingOptions": doc.get("trainingOptions", {}),
        "vouchers": voucher_list  # ✅ vouchers included
    })

# =====================================================
# COURSE DETAILS BY NAME (TEXT MATCH SUPPORT)
# =====================================================
async def get_course_details_by_name(question: str):

    question_lower = question.lower()

    async for doc in courses.find({"isDeleted": False}):

        if doc["title"].lower() in question_lower:

            voucher_list = []

            voucher_ids = doc.get("vouchers", [])

            if voucher_ids:

                async for v in vouchers.find({
                    "_id": {"$in": voucher_ids},
                    "isDeleted": False,
                    "isActive": True
                }):

                    voucher_list.append({
                        "_id": v["_id"],
                        "name": v["name"],
                        "price": v.get("price"),
                        "description": v.get("description"),
                        "quick_link": {
                            "label": f"View Voucher: {v['name']}",
                            "value": f"Show voucher {v['name']}"
                        }
                    })

            return serialize_mongo({
                "_id": doc["_id"],
                "title": doc["title"],
                "overviewDescription": doc.get("overviewDescription"),
                "keyFeatures": doc.get("keyFeatures", []),
                "skillsCovered": doc.get("skillsCovered", []),
                "benefits": doc.get("benefits", []),
                "modules": doc.get("modules", []),
                "trainingOptions": doc.get("trainingOptions", {}),
                "vouchers": voucher_list   # ✅ vouchers added here
            })

    return None

# =====================================================
# COURSE SECTION
# =====================================================
async def get_course_section_by_name(question: str):

    question_lower = question.lower().strip()

    async for doc in courses.find({"isDeleted": False}):

        title_lower = doc["title"].lower()

        if title_lower in question_lower:

            title = doc["title"]

            if "skill" in question_lower:
                return serialize_mongo({
                    "title": title,
                    "skillsCovered": doc.get("skillsCovered", [])
                })

            if "feature" in question_lower:
                return serialize_mongo({
                    "title": title,
                    "keyFeatures": doc.get("keyFeatures", [])
                })

            if "benefit" in question_lower:
                return serialize_mongo({
                    "title": title,
                    "benefits": doc.get("benefits", [])
                })

            if "module" in question_lower:
                return serialize_mongo({
                    "title": title,
                    "modules": doc.get("modules", [])
                })

            if "training" in question_lower:
                return serialize_mongo({
                    "title": title,
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
# LIST ALL ACTIVE VOUCHERS (WITH APPLICABLE COURSES)
# =====================================================
async def list_active_vouchers():

    data = []

    async for doc in vouchers.find({
        "isDeleted": False,
        "isActive": True
    }):

        course_titles = []

        # fetch course titles from applicableCourses ids
        for course_id in doc.get("applicableCourses", []):
            course = await courses.find_one({"_id": course_id})
            if course:
                course_titles.append(course["title"])

        data.append({
            "_id": doc["_id"],
            "name": doc["name"],
            "price": doc.get("price"),
            "description": doc.get("description"),
            "applicableCourses": course_titles   # ✅ NEW FIELD
        })

    return serialize_mongo(data)


# =====================================================
# GET VOUCHERS FOR SPECIFIC COURSE
# =====================================================
async def get_vouchers_for_course(question: str):

    question_lower = question.lower().strip()
    selected_course = None

    # Find matching course
    async for course in courses.find({"isDeleted": False}):

        if course["title"].lower() in question_lower:
            selected_course = course
            break

    if not selected_course:
        return {
            "course": None,
            "vouchers": []
        }

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
            "price": doc.get("price"),
            "description": doc.get("description"),
            "quick_link": {
                "label": f"View Voucher: {doc.get('name')}",
                "value": f"voucher:{str(doc.get['_id'])}"
    }
        })

    return serialize_mongo({
        "course": selected_course["title"],
        "vouchers": voucher_list
    })
    
    
# =====================================================
# GET VOUCHER BY NAME (ENTITY MATCH)
# =====================================================
async def get_voucher_by_name(question: str):

    question_lower = question.lower().strip()

    async for doc in vouchers.find({
        "isDeleted": False,
        "isActive": True
    }):

        voucher_name = doc["name"].lower()

        if voucher_name in question_lower:

            return serialize_mongo({
                "_id": doc["_id"],
                "name": doc["name"],
                "price": doc.get("price"),
                "description": doc.get("description")
            })

    return None


# =====================================================
# GET VOUCHER BY ID
# =====================================================
async def get_voucher_by_id(voucher_id: str):

    doc = await vouchers.find_one({
        "_id": ObjectId(voucher_id),
        "isDeleted": False,
        "isActive": True
    })

    if not doc:
        return None

    return serialize_mongo({
        "_id": doc["_id"],
        "name": doc["name"],
        "price": doc.get("price"),
        "description": doc.get("description")
    })


# =====================================================
# LIST UPCOMING BOOTCAMPS
# =====================================================
async def list_upcoming_bootcamps():

    now = datetime.now(timezone.utc)
    data = []

    async for doc in bootcamps.find({
        "isDeleted": False,
        "status": "active"
    }):

        start = doc["startDate"]
        end = doc["endDate"]

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        if start > now:

            title = doc["title"]

            data.append({
                "_id": doc["_id"],
                "title": title,
                "startDate": start,
                "endDate": end,
                "quick_link": {
                    "label": f"View Bootcamp Details: {title}",
                    "value": f"bootcamp:{doc['_id']}"
                }
            })

    # ✅ HANDLE EMPTY CASE
    if not data:
        return {
            "message": "No Bootcamps available"
        }

    return serialize_mongo(data)



# async def list_upcoming_bootcamps():

#     now = datetime.now(timezone.utc)
#     data = []

#     async for doc in bootcamps.find({
#         "isDeleted": False,
#         "status": "active"
#     }):

#         start = doc["startDate"]
#         end = doc["endDate"]

#         # Ensure timezone aware
#         if start.tzinfo is None:
#             start = start.replace(tzinfo=timezone.utc)

#         if end.tzinfo is None:
#             end = end.replace(tzinfo=timezone.utc)

#         # ✅ FIX: allow ongoing + upcoming
#         if end >= now:

#             title = doc["title"]

#             data.append({
#                 "_id": doc["_id"],
#                 "title": title,
#                 "startDate": start,
#                 "endDate": end,
#                 "quick_link": {
#                     "label": f"View Bootcamp Details: {title}",
#                     "value": f"bootcamp:{doc['_id']}"
#                 }
#             })

#     return serialize_mongo(data)

# =====================================================
# BOOTCAMP DETAILS
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
                "timeSlot": doc.get("timeSlot"),
                "pricing": doc.get("pricing"),
                "features": doc.get("features"),
                "agenda": doc.get("agenda"),
                "keyTakeaways": doc.get("keyTakeaways")
            })

    return None


# =====================================================
# BOOTCAMP DETAILS BY ID
# =====================================================
async def get_bootcamp_details_by_id(bootcamp_id: str):

    doc = await bootcamps.find_one({
        "_id": ObjectId(bootcamp_id),
        "isDeleted": False
    })

    if not doc:
        return None

    return serialize_mongo({
        "_id": doc["_id"],
        "title": doc["title"],
        "startDate": doc.get("startDate"),
        "endDate": doc.get("endDate"),
        "timeSlot": doc.get("timeSlot"),
        "pricing": doc.get("pricing"),
        "features": doc.get("features"),
        "agenda": doc.get("agenda"),
        "keyTakeaways": doc.get("keyTakeaways")
    })

# =====================================================
# BOOTCAMP SECTION FETCH
# =====================================================
async def get_bootcamp_section_by_name(question: str):

    question_lower = question.lower().strip()

    async for doc in bootcamps.find({
        "isDeleted": False,
        "status": "active"
    }):

        title_lower = doc["title"].lower()

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