from flask import Blueprint
from auth_utils import role_required  # Import decorator

admin_bp = Blueprint('admin', __name__)

# Rute untuk role `user`
@admin_bp.route('/view-only')
@role_required('user', 'admin', 'super_admin')
def view_only():
    return "This is a view-only page. No interactions allowed."

# Rute untuk role `admin`
@admin_bp.route('/admin-page')
@role_required('admin', 'super_admin')
def admin_page():
    return "Admin can manage content but not users."

# Rute untuk role `super_admin`
@admin_bp.route('/manage-users')
@role_required('super_admin')
def manage_users():
    return "Super Admin can manage users and everything else."
