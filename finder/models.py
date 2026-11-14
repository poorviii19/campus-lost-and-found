"""
Data Access Layer (Service Layer) for MongoDB 'item_reports' collection.

Note on Architecture:
Django's built-in ORM (django.db.models.Model) generates SQL queries designed for relational databases (e.g. SQLite, PostgreSQL).
Because MongoDB Atlas is a NoSQL document database, we use PyMongo directly to perform CRUD (Create, Read, Update, Delete) operations.
"""

from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from .db import get_reports_collection

# Predefined categories for Campus Lost & Found
CATEGORIES = [
    'Electronics',
    'Books',
    'Accessories',
    'ID Cards',
    'Clothing',
    'Other',
]

# Report Types
REPORT_TYPES = ['lost', 'found']

# Valid Statuses
STATUS_PENDING = 'Pending'
STATUS_APPROVED = 'Approved'
STATUS_REJECTED = 'Rejected'
STATUS_RESOLVED = 'Resolved'

STATUSES = [STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_RESOLVED]


def format_doc(doc):
    """
    Helper to convert MongoDB document for seamless use in Django templates:
    - Adds string representation of `_id` as `doc['id']`
    - Returns None if doc is None
    """
    if not doc:
        return None
    doc['id'] = str(doc['_id'])
    return doc


class ReportService:
    """
    Encapsulates all database operations for item reports.
    """

    @staticmethod
    def create_report(
        reporter_id,
        reporter_username,
        report_type,
        title,
        category,
        description,
        location,
        date_lost_found,
        image_path='',
        status=STATUS_PENDING,
    ):
        """
        Inserts a new report document into the 'item_reports' collection.
        Returns the inserted document with string 'id'.
        """
        collection = get_reports_collection()
        report_doc = {
            'reporter_id': int(reporter_id),
            'reporter_username': str(reporter_username),
            'report_type': report_type.lower(),  # 'lost' or 'found'
            'title': title.strip(),
            'category': category,
            'description': description.strip(),
            'location': location.strip(),
            'date_lost_found': date_lost_found,  # string 'YYYY-MM-DD' or date
            'image_path': image_path,            # relative path inside MEDIA_ROOT
            'status': status,                    # Default: 'Pending'
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        result = collection.insert_one(report_doc)
        report_doc['_id'] = result.inserted_id
        return format_doc(report_doc)

    @staticmethod
    def get_report_by_id(report_id):
        """
        Retrieves a single report by its MongoDB ObjectId string.
        Returns formatted document or None if not found or invalid ID.
        """
        try:
            obj_id = ObjectId(report_id)
        except (InvalidId, TypeError):
            return None

        collection = get_reports_collection()
        doc = collection.find_one({'_id': obj_id})
        return format_doc(doc)

    @staticmethod
    def get_approved_reports(search_query='', report_type='', category='', location=''):
        """
        Finds all 'Approved' reports matching optional search & filter criteria.
        Sorted by newest reports first (created_at DESC).
        """
        collection = get_reports_collection()
        query = {'status': STATUS_APPROVED}

        if report_type:
            query['report_type'] = report_type.lower()
        if category:
            query['category'] = category
        if location:
            query['location'] = {'$regex': location.strip(), '$options': 'i'}
        if search_query:
            # Case-insensitive substring search across title and description
            query['$or'] = [
                {'title': {'$regex': search_query.strip(), '$options': 'i'}},
                {'description': {'$regex': search_query.strip(), '$options': 'i'}},
            ]

        cursor = collection.find(query).sort('created_at', -1)
        return [format_doc(doc) for doc in cursor]

    @staticmethod
    def get_recent_approved_reports(limit=6):
        """
        Retrieves the most recent approved reports for the home page.
        """
        collection = get_reports_collection()
        cursor = collection.find({'status': STATUS_APPROVED}).sort('created_at', -1).limit(limit)
        return [format_doc(doc) for doc in cursor]

    @staticmethod
    def get_user_reports(user_id):
        """
        Retrieves all reports submitted by a specific user (regardless of status).
        """
        collection = get_reports_collection()
        cursor = collection.find({'reporter_id': int(user_id)}).sort('created_at', -1)
        return [format_doc(doc) for doc in cursor]

    @staticmethod
    def get_all_reports(status_filter='', search_query=''):
        """
        Used by Admin to view all reports across the campus.
        """
        collection = get_reports_collection()
        query = {}
        if status_filter:
            query['status'] = status_filter
        if search_query:
            query['$or'] = [
                {'title': {'$regex': search_query.strip(), '$options': 'i'}},
                {'reporter_username': {'$regex': search_query.strip(), '$options': 'i'}},
                {'location': {'$regex': search_query.strip(), '$options': 'i'}},
            ]
        cursor = collection.find(query).sort('created_at', -1)
        return [format_doc(doc) for doc in cursor]

    @staticmethod
    def update_report(report_id, update_fields, user_id=None):
        """
        Updates fields of an existing report.
        If user_id is provided, ensures only the author can update their report.
        """
        try:
            obj_id = ObjectId(report_id)
        except (InvalidId, TypeError):
            return False

        collection = get_reports_collection()
        filter_query = {'_id': obj_id}
        if user_id is not None:
            filter_query['reporter_id'] = int(user_id)

        update_fields['updated_at'] = datetime.utcnow()
        result = collection.update_one(filter_query, {'$set': update_fields})
        return result.modified_count > 0 or result.matched_count > 0

    @staticmethod
    def update_status(report_id, new_status):
        """
        Updates the approval/resolution status of a report (Used by Admin).
        """
        if new_status not in STATUSES:
            return False
        return ReportService.update_report(report_id, {'status': new_status})

    @staticmethod
    def delete_report(report_id, user_id=None):
        """
        Deletes a report document.
        If user_id is provided, ensures only the author can delete it.
        """
        try:
            obj_id = ObjectId(report_id)
        except (InvalidId, TypeError):
            return False

        collection = get_reports_collection()
        filter_query = {'_id': obj_id}
        if user_id is not None:
            filter_query['reporter_id'] = int(user_id)

        result = collection.delete_one(filter_query)
        return result.deleted_count > 0

    @staticmethod
    def get_statistics():
        """
        Calculates aggregate statistics for the portal (only approved/verified items):
        - Total verified lost reports (status='Approved')
        - Total verified found reports (status='Approved')
        - Total verified resolved reports (status='Resolved')
        """
        collection = get_reports_collection()
        total_lost = collection.count_documents({
            'report_type': 'lost',
            'status': STATUS_APPROVED
        })
        total_found = collection.count_documents({
            'report_type': 'found',
            'status': STATUS_APPROVED
        })
        total_resolved = collection.count_documents({
            'status': STATUS_RESOLVED
        })
        return {
            'total_lost': total_lost,
            'total_found': total_found,
            'total_resolved': total_resolved,
        }
